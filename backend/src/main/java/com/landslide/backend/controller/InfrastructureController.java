package com.landslide.backend.controller;

import com.landslide.backend.dto.CreateInfrastructureRequest;
import com.landslide.backend.dto.InfrastructureResponse;
import com.landslide.backend.entity.InfrastructureType;
import com.landslide.backend.service.InfrastructureService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Positive;

import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/infrastructure")
@Validated
@Tag(name = "Infrastructure", description = "Endpoints for managing critical infrastructure assets, proximity queries, and type filtering")
public class InfrastructureController {

    private final InfrastructureService infrastructureService;

    public InfrastructureController(
            InfrastructureService infrastructureService
    ) {
        this.infrastructureService = infrastructureService;
    }

    // CREATE
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Create Infrastructure Asset", description = "Registers a new infrastructure asset (e.g. ROAD, HOSPITAL, SCHOOL, BRIDGE, POLICE_STATION, SHELTER) with spatial coordinates.")
    public InfrastructureResponse createInfrastructure(
            @Valid @RequestBody CreateInfrastructureRequest request
    ) {
        return infrastructureService
                .createInfrastructure(request);
    }

    // GET ALL
    @GetMapping
    @Operation(summary = "Get All Infrastructure Assets", description = "Retrieves all infrastructure assets in the system.")
    public List<InfrastructureResponse> getAllInfrastructure() {
        return infrastructureService
                .getAllInfrastructure();
    }

    // GET NEARBY
    @GetMapping("/nearby")
    @Operation(summary = "Find Nearby Infrastructure", description = "Finds infrastructure assets within a specified radius (in METERS) using PostGIS ST_DWithin with optional type filtering.")
    public List<InfrastructureResponse> findNearbyInfrastructure(
            @Parameter(description = "Latitude (-90 to 90)")
            @RequestParam
            @DecimalMin(value = "-90.0", message = "Latitude must be at least -90")
            @DecimalMax(value = "90.0", message = "Latitude must be at most 90")
            Double latitude,

            @Parameter(description = "Longitude (-180 to 180)")
            @RequestParam
            @DecimalMin(value = "-180.0", message = "Longitude must be at least -180")
            @DecimalMax(value = "180.0", message = "Longitude must be at most 180")
            Double longitude,

            @Parameter(description = "Search radius distance in METERS")
            @RequestParam
            @Positive(message = "Distance must be greater than 0")
            Double distance,

            @Parameter(description = "Optional filter by infrastructure type (ROAD, HOSPITAL, SCHOOL, BRIDGE, POLICE_STATION, SHELTER)")
            @RequestParam(required = false)
            InfrastructureType type
    ) {
        return infrastructureService
                .findNearbyInfrastructure(latitude, longitude, distance, type);
    }

    // GET BY ID
    @GetMapping("/{id}")
    @Operation(summary = "Get Infrastructure by ID", description = "Retrieves details of a single infrastructure asset by ID.")
    public InfrastructureResponse getInfrastructureById(
            @PathVariable Long id
    ) {
        return infrastructureService
                .getInfrastructureById(id);
    }

    // DELETE
    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete Infrastructure Asset", description = "Deletes an infrastructure asset record by ID.")
    public void deleteInfrastructure(
            @PathVariable Long id
    ) {
        infrastructureService.deleteInfrastructure(id);
    }
}
