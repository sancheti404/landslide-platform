package com.landslide.backend.service;

import com.landslide.backend.dto.RiskAssessmentRequest;
import com.landslide.backend.dto.RiskAssessmentResponse;
import com.landslide.backend.exception.MlServiceException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import java.time.Duration;
import java.util.Map;
import java.util.UUID;

@Service
public class MlInferenceClient {

    private static final Logger log = LoggerFactory.getLogger(MlInferenceClient.class);

    private final RestClient restClient;
    private final String serviceUrl;

    public MlInferenceClient(
            @Value("${ml.inference.service-url:http://127.0.0.1:8000}") String serviceUrl,
            @Value("${ml.inference.connect-timeout-ms:5000}") int connectTimeoutMs,
            @Value("${ml.inference.read-timeout-ms:20000}") int readTimeoutMs
    ) {
        this.serviceUrl = serviceUrl;
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofMillis(connectTimeoutMs));
        requestFactory.setReadTimeout(Duration.ofMillis(readTimeoutMs));

        this.restClient = RestClient.builder()
                .baseUrl(serviceUrl)
                .requestFactory(requestFactory)
                .build();
    }

    public RiskAssessmentResponse assessRisk(RiskAssessmentRequest request) {
        return assessRisk(request, UUID.randomUUID().toString());
    }

    public RiskAssessmentResponse assessRisk(RiskAssessmentRequest request, String requestId) {
        long startTime = System.currentTimeMillis();
        try {
            log.info("Forwarding risk assessment [req_id={}] to ML service at {} for ({}, {}) @ {}",
                    requestId, serviceUrl, request.getLatitude(), request.getLongitude(), request.getTimestamp());

            RiskAssessmentResponse response = restClient.post()
                    .uri("/risk/assess")
                    .header("X-Request-ID", requestId)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(RiskAssessmentResponse.class);

            long elapsed = System.currentTimeMillis() - startTime;
            log.info("ML inference successful in {} ms [req_id={}]", elapsed, requestId);
            return response;

        } catch (RestClientResponseException e) {
            long elapsed = System.currentTimeMillis() - startTime;
            log.error("ML service HTTP error after {} ms [req_id={}]: {} - {}",
                    elapsed, requestId, e.getStatusCode(), e.getResponseBodyAsString());
            int code = e.getStatusCode().value();
            String errCode = code == 400 ? "UNSUPPORTED_LOCATION" : "ML_SERVICE_ERROR";
            throw new MlServiceException("ML inference service error: " + e.getResponseBodyAsString(), code, errCode);
        } catch (Exception e) {
            long elapsed = System.currentTimeMillis() - startTime;
            log.error("Failed to connect to ML inference service at {} after {} ms [req_id={}]: {}",
                    serviceUrl, elapsed, requestId, e.getMessage());
            throw new MlServiceException(
                    "ML inference service is currently unreachable. Please ensure the Python FastAPI service is running on " + serviceUrl,
                    e,
                    503,
                    "ML_SERVICE_UNAVAILABLE"
            );
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> checkHealth() {
        try {
            return restClient.get()
                    .uri("/health")
                    .retrieve()
                    .body(Map.class);
        } catch (Exception e) {
            log.warn("ML health check failed: {}", e.getMessage());
            return Map.of(
                    "status", "unreachable",
                    "serviceUrl", serviceUrl,
                    "error", e.getMessage()
            );
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> checkReadiness() {
        try {
            return restClient.get()
                    .uri("/health/ready")
                    .retrieve()
                    .body(Map.class);
        } catch (Exception e) {
            log.warn("ML readiness check failed: {}", e.getMessage());
            return Map.of(
                    "status", "not_ready",
                    "serviceUrl", serviceUrl,
                    "error", e.getMessage()
            );
        }
    }
}

