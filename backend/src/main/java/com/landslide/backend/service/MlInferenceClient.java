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

@Service
public class MlInferenceClient {

    private static final Logger log = LoggerFactory.getLogger(MlInferenceClient.class);

    private final RestClient restClient;
    private final String serviceUrl;

    public MlInferenceClient(
            @Value("${ml.inference.service-url:http://localhost:8000}") String serviceUrl,
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
        try {
            log.info("Forwarding risk assessment to ML service at {} for ({}, {}) @ {}",
                    serviceUrl, request.getLatitude(), request.getLongitude(), request.getTimestamp());

            return restClient.post()
                    .uri("/risk/assess")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(RiskAssessmentResponse.class);

        } catch (RestClientResponseException e) {
            log.error("ML service HTTP error: {} - {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new MlServiceException(
                    "ML inference service error: " + e.getResponseBodyAsString(),
                    e.getStatusCode().value()
            );
        } catch (Exception e) {
            log.error("Failed to connect to ML inference service at {}: {}", serviceUrl, e.getMessage());
            throw new MlServiceException(
                    "ML inference service is currently unreachable. Please ensure the Python FastAPI service is running on " + serviceUrl,
                    e
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
}
