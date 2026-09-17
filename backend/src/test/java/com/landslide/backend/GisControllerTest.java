package com.landslide.backend;

import com.landslide.backend.controller.GisController;
import com.landslide.backend.dto.LandslideEventResponse;
import com.landslide.backend.service.LandslideEventService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyDouble;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class GisControllerTest {

    private MockMvc mockMvc;
    private LandslideEventService landslideEventService;

    @BeforeEach
    void setUp() {
        landslideEventService = Mockito.mock(LandslideEventService.class);
        GisController controller = new GisController(landslideEventService);
        controller.initBoundaryCache();
        mockMvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    void testGetStateBoundary_Success() throws Exception {
        mockMvc.perform(get("/api/gis/state-boundary"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.type").value("FeatureCollection"))
                .andExpect(jsonPath("$.provenance.state").value("Uttarakhand"))
                .andExpect(jsonPath("$.provenance.source").value("William & Mary geoBoundaries (gbOpen)"));
    }

    @Test
    void testGetDistrictSummary() throws Exception {
        Map<String, Long> summary = Map.of(
                "Chamoli", 1284L,
                "Rudraprayag", 950L,
                "Uttarkashi", 820L
        );
        Mockito.when(landslideEventService.getDistrictSummary()).thenReturn(summary);

        mockMvc.perform(get("/api/gis/district-summary"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.Chamoli").value(1284))
                .andExpect(jsonPath("$.Rudraprayag").value(950))
                .andExpect(jsonPath("$.Uttarkashi").value(820));
    }

    @Test
    void testGetHistoricalLandslides() throws Exception {
        LandslideEventResponse sample = new LandslideEventResponse(
                100L, 30.55, 79.10, "HIGH", "HISTORICAL", "GSI_NLSM",
                LocalDateTime.now(), LocalDateTime.now(), null, null, null,
                "UK-001", "Chamoli", "Badrinath Slide", "Debris", "Debris Slide", "Active during monsoon"
        );
        Mockito.when(landslideEventService.findHistoricalLandslides(any(), any(), any(), any(), any(), any(), anyInt()))
                .thenReturn(List.of(sample));

        mockMvc.perform(get("/api/gis/historical-landslides")
                        .param("district", "Chamoli")
                        .param("limit", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].slideNo").value("UK-001"))
                .andExpect(jsonPath("$[0].district").value("Chamoli"))
                .andExpect(jsonPath("$[0].source").value("GSI_NLSM"))
                .andExpect(jsonPath("$[0].movementType").value("Debris Slide"));
    }

    @Test
    void testGetGisMetadata() throws Exception {
        mockMvc.perform(get("/api/gis/metadata"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.operational_envelope.min_latitude").value(28.5))
                .andExpect(jsonPath("$.operational_envelope.max_longitude").value(81.3))
                .andExpect(jsonPath("$.layers").isArray());
    }
}
