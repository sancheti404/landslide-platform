package com.landslide.backend.controller;

import com.landslide.backend.dto.CreateRiskZoneRequest;
import com.landslide.backend.dto.RiskZoneLocationResponse;
import com.landslide.backend.dto.RiskZoneResponse;
import com.landslide.backend.dto.UpdateRiskZoneRequest;
import com.landslide.backend.service.RiskZoneService;

import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;

import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/risk-zones")
@Validated
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

    // CONTAINS POINT
    @GetMapping("/contains")
    public List<RiskZoneResponse> findRiskZonesContainingPoint(
            @RequestParam Double latitude,
            @RequestParam Double longitude
    ) {
        return riskZoneService
                .findRiskZonesContainingPoint(latitude, longitude);
    }

    // LOCATE POINT IN RISK ZONE (Must be before /{id})
    @GetMapping("/locate")
    public RiskZoneLocationResponse locatePoint(
            @RequestParam
            @DecimalMin(value = "-90.0", message = "Latitude must be at least -90")
            @DecimalMax(value = "90.0", message = "Latitude must be at most 90")
            Double latitude,

            @RequestParam
            @DecimalMin(value = "-180.0", message = "Longitude must be at least -180")
            @DecimalMax(value = "180.0", message = "Longitude must be at most 180")
            Double longitude
    ) {
        return riskZoneService.locatePoint(latitude, longitude);
    }

    // UPDATE RISK ZONE
    @PutMapping("/{id}")
    public RiskZoneResponse updateRiskZone(
            @PathVariable Long id,
            @Valid @RequestBody UpdateRiskZoneRequest request
    ) {
        return riskZoneService.updateRiskZone(id, request);
    }

    // GET RISK ZONE BY ID
    @GetMapping("/{id}")
    public RiskZoneResponse getRiskZoneById(
            @PathVariable Long id
    ) {
        return riskZoneService.getRiskZoneById(id);
    }

    // DELETE RISK ZONE
    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteRiskZone(
            @PathVariable Long id
    ) {
        riskZoneService.deleteRiskZone(id);
    }
}
