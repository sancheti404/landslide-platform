package com.landslide.backend.controller;

import com.landslide.backend.dto.RiskAssessmentRequest;
import com.landslide.backend.dto.RiskAssessmentResponse;
import com.landslide.backend.service.RiskAssessmentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/risk")
@Tag(name = "Risk Assessment", description = "Endpoints for multimodal landslide risk evaluation, ML static-visual fusion, dynamic rainfall integration, and PostGIS enrichment")
public class RiskAssessmentController {


    private final RiskAssessmentService riskAssessmentService;

    public RiskAssessmentController(RiskAssessmentService riskAssessmentService) {
        this.riskAssessmentService = riskAssessmentService;
    }

    @PostMapping("/assess")
    @Operation(
            summary = "Assess Landslide Risk",
            description = "Evaluates multimodal landslide risk at a coordinate and timestamp. Combines XGBoost terrain susceptibility, Swin Sentinel-2 optical risk, static-visual fusion (0.38/0.62), dynamic CHIRPS rainfall triggering, and PostGIS spatial risk zones."
    )
    public ResponseEntity<RiskAssessmentResponse> assessLandslideRisk(
            @Valid @RequestBody RiskAssessmentRequest request,
            @RequestHeader(value = "X-Request-ID", required = false) String requestId
    ) {
        String effectiveRequestId = (requestId != null && !requestId.isBlank())
                ? requestId
                : java.util.UUID.randomUUID().toString();

        RiskAssessmentResponse response = (requestId != null && !requestId.isBlank())
                ? riskAssessmentService.assessLandslideRisk(request, effectiveRequestId)
                : riskAssessmentService.assessLandslideRisk(request);

        return ResponseEntity.ok()
                .header("X-Request-ID", effectiveRequestId)
                .body(response);
    }


    @GetMapping("/ml-health")
    @Operation(
            summary = "Check ML Inference Service Health",
            description = "Checks connectivity to the Python FastAPI ML inference service and returns model readiness status."
    )
    public ResponseEntity<Map<String, Object>> checkMlHealth() {
        Map<String, Object> health = riskAssessmentService.checkMlHealth();
        return ResponseEntity.ok(health);
    }

}
