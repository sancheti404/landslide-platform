package com.landslide.backend;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.landslide.backend.controller.RiskAssessmentController;
import com.landslide.backend.dto.RiskAssessmentRequest;
import com.landslide.backend.dto.RiskAssessmentResponse;
import com.landslide.backend.entity.RiskLevel;
import com.landslide.backend.service.RiskAssessmentService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class RiskAssessmentControllerTest {

    private MockMvc mockMvc;
    private RiskAssessmentService riskAssessmentService;
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        riskAssessmentService = Mockito.mock(RiskAssessmentService.class);
        RiskAssessmentController controller = new RiskAssessmentController(riskAssessmentService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller).build();
        objectMapper = new ObjectMapper();
    }

    @Test
    void testAssessLandslideRisk_Success() throws Exception {
        RiskAssessmentRequest request = new RiskAssessmentRequest(30.5295, 79.0859, "2023-07-15");

        RiskAssessmentResponse mockResponse = new RiskAssessmentResponse();
        mockResponse.setLatitude(30.5295);
        mockResponse.setLongitude(79.0859);
        mockResponse.setTimestamp("2023-07-15");
        mockResponse.setXgboostProbability(0.85);
        mockResponse.setSwinProbability(0.90);
        mockResponse.setStaticVisualFusionScore(0.881);
        mockResponse.setRainfall3dMm(77.37);
        mockResponse.setRainfall7dMm(242.44);
        mockResponse.setRainfall14dMm(284.41);
        mockResponse.setRainfall30dMm(415.58);
        mockResponse.setMaximumDailyRainfallMm(55.20);
        mockResponse.setRainfallAnomaly(1.026);
        mockResponse.setDynamicRainfallTriggerScore(0.7339);
        mockResponse.setTriggerIndicator("SEVERE_TRIGGER");
        mockResponse.setOperationalLandslideRiskScore(1.00);
        mockResponse.setRiskLevel(RiskLevel.CRITICAL);
        mockResponse.setModelVersion("1.0.0");
        mockResponse.setStatus("success");

        Mockito.when(riskAssessmentService.assessLandslideRisk(any(RiskAssessmentRequest.class)))
                .thenReturn(mockResponse);

        mockMvc.perform(post("/api/risk/assess")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.operational_landslide_risk_score").value(1.0))
                .andExpect(jsonPath("$.risk_level").value("CRITICAL"))
                .andExpect(jsonPath("$.static_visual_fusion_score").value(0.881))
                .andExpect(jsonPath("$.xgboost_probability").value(0.85))
                .andExpect(jsonPath("$.swin_probability").value(0.90));
    }

    @Test
    void testAssessLandslideRisk_InvalidCoordinates() throws Exception {
        // Out-of-bounds latitude (< 28.0)
        RiskAssessmentRequest request = new RiskAssessmentRequest(25.0, 79.0859, "2023-07-15");

        mockMvc.perform(post("/api/risk/assess")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void testCheckMlHealth() throws Exception {
        Mockito.when(riskAssessmentService.checkMlHealth())
                .thenReturn(Map.of("status", "healthy", "device", "cpu"));

        mockMvc.perform(get("/api/risk/ml-health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("healthy"));
    }
}
