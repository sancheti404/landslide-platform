package com.landslide.backend.controller;

import com.landslide.backend.dto.DashboardStatisticsResponse;
import com.landslide.backend.service.DashboardService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/dashboard")
@Tag(name = "Dashboard", description = "Endpoints for dashboard statistics and analytics")
public class DashboardController {

    private final DashboardService dashboardService;

    public DashboardController(DashboardService dashboardService) {
        this.dashboardService = dashboardService;
    }

    @GetMapping("/statistics")
    @Operation(summary = "Get Dashboard Statistics", description = "Returns aggregated statistical counts for landslides (by severity, status, risk level, and unassigned), risk zones (by risk level), and infrastructure (by type).")
    public DashboardStatisticsResponse getDashboardStatistics() {
        return dashboardService.getDashboardStatistics();
    }
}
