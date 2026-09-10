package com.landslide.backend.controller;

import com.landslide.backend.dto.CreateRiskZoneRequest;
import com.landslide.backend.dto.RiskZoneResponse;
import com.landslide.backend.service.RiskZoneService;

import jakarta.validation.Valid;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/risk-zones")
public class RiskZoneController {

    private final RiskZoneService riskZoneService;

    public RiskZoneController(
            RiskZoneService riskZoneService
    ) {
        this.riskZoneService = riskZoneService;
    }

    // CREATE RISK ZONE
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public RiskZoneResponse createRiskZone(
            @Valid @RequestBody CreateRiskZoneRequest request
    ) {
        return riskZoneService.createRiskZone(request);
    }

    // GET ALL RISK ZONES
    @GetMapping
    public List<RiskZoneResponse> getAllRiskZones() {
        return riskZoneService.getAllRiskZones();
    }

    @GetMapping("/contains")
    public List<RiskZoneResponse> findRiskZonesContainingPoint(
            @RequestParam Double latitude,
            @RequestParam Double longitude
    ) {
        return riskZoneService
                .findRiskZonesContainingPoint(latitude, longitude);
    }

    // GET RISK ZONE BY ID
    @GetMapping("/{id}")
    public RiskZoneResponse getRiskZoneById(
            @PathVariable Long id
    ) {
        return riskZoneService.getRiskZoneById(id);
    }
}
