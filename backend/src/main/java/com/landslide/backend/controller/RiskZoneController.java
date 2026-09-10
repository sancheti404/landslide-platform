package com.landslide.backend.controller;

import com.landslide.backend.dto.CreateRiskZoneRequest;
import com.landslide.backend.dto.RiskZoneLocationResponse;
import com.landslide.backend.dto.RiskZoneResponse;
import com.landslide.backend.dto.UpdateRiskZoneRequest;
import com.landslide.backend.service.RiskZoneService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
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
@Tag(name = "Risk Zones", description = "Endpoints for managing risk zones, polygon boundary validation, overlap detection, and point-in-polygon queries")
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
    @Operation(summary = "Create Risk Zone", description = "Creates a new risk zone with boundary polygon, validating SRID 4326 and checking for spatial overlap with existing risk zones.")
    public RiskZoneResponse createRiskZone(
            @Valid @RequestBody CreateRiskZoneRequest request
    ) {
        return riskZoneService.createRiskZone(request);
    }

    // GET ALL RISK ZONES
    @GetMapping
    @Operation(summary = "Get All Risk Zones", description = "Retrieves all risk zones registered in the system.")
    public List<RiskZoneResponse> getAllRiskZones() {
        return riskZoneService.getAllRiskZones();
    }

    // CONTAINS POINT
    @GetMapping("/contains")
    @Operation(summary = "Find Risk Zones Containing Point", description = "Finds all risk zones that spatially contain the specified coordinate.")
    public List<RiskZoneResponse> findRiskZonesContainingPoint(
            @Parameter(description = "Latitude (-90 to 90)") @RequestParam Double latitude,
            @Parameter(description = "Longitude (-180 to 180)") @RequestParam Double longitude
    ) {
        return riskZoneService
                .findRiskZonesContainingPoint(latitude, longitude);
    }

    // LOCATE POINT IN RISK ZONE (Must be before /{id})
    @GetMapping("/locate")
    @Operation(summary = "Locate Point in Risk Zone", description = "Checks whether a point lies inside a risk zone and returns details of the assigned zone or insideRiskZone=false if unassigned.")
    public RiskZoneLocationResponse locatePoint(
            @Parameter(description = "Latitude (-90 to 90)")
            @RequestParam
            @DecimalMin(value = "-90.0", message = "Latitude must be at least -90")
            @DecimalMax(value = "90.0", message = "Latitude must be at most 90")
            Double latitude,

            @Parameter(description = "Longitude (-180 to 180)")
            @RequestParam
            @DecimalMin(value = "-180.0", message = "Longitude must be at least -180")
            @DecimalMax(value = "180.0", message = "Longitude must be at most 180")
            Double longitude
    ) {
        return riskZoneService.locatePoint(latitude, longitude);
    }

    // UPDATE RISK ZONE
    @PutMapping("/{id}")
    @Operation(summary = "Update Risk Zone", description = "Updates an existing risk zone's properties or boundary, re-verifying spatial overlap exclusions.")
    public RiskZoneResponse updateRiskZone(
            @PathVariable Long id,
            @Valid @RequestBody UpdateRiskZoneRequest request
    ) {
        return riskZoneService.updateRiskZone(id, request);
    }

    // GET RISK ZONE BY ID
    @GetMapping("/{id}")
    @Operation(summary = "Get Risk Zone by ID", description = "Retrieves details of a single risk zone by its ID.")
    public RiskZoneResponse getRiskZoneById(
            @PathVariable Long id
    ) {
        return riskZoneService.getRiskZoneById(id);
    }

    // DELETE RISK ZONE
    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete Risk Zone", description = "Deletes a risk zone by ID and detaches associated landslide events.")
    public void deleteRiskZone(
            @PathVariable Long id
    ) {
        riskZoneService.deleteRiskZone(id);
    }
}
