package com.landslide.backend.controller;

import com.landslide.backend.dto.CreateLandslideEventRequest;
import com.landslide.backend.dto.LandslideEventResponse;
import com.landslide.backend.dto.LandslideIntelligenceResponse;
import com.landslide.backend.entity.RiskLevel;
import com.landslide.backend.service.LandslideEventService;
import com.landslide.backend.service.LandslideIntelligenceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/landslides")
@Tag(name = "Landslides", description = "Endpoints for managing landslide events, filtering, spatial proximity, and intelligence")
public class LandslideEventController {

    private final LandslideEventService landslideEventService;
    private final LandslideIntelligenceService landslideIntelligenceService;

    public LandslideEventController(
            LandslideEventService landslideEventService,
            LandslideIntelligenceService landslideIntelligenceService
    ) {
        this.landslideEventService = landslideEventService;
        this.landslideIntelligenceService = landslideIntelligenceService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Create Landslide Event", description = "Creates a new landslide event and automatically assigns it to an overlapping risk zone if present.")
    public LandslideEventResponse createEvent(
            @Valid @RequestBody CreateLandslideEventRequest request
    ) {
        return landslideEventService.createEvent(request);
    }

    @GetMapping
    @Operation(summary = "Get / Filter Landslide Events", description = "Retrieves all landslide events with optional filters for severity, status, risk level, risk zone ID, and date range.")
    public List<LandslideEventResponse> getAllEvents(
            @Parameter(description = "Filter by severity (e.g. LOW, MEDIUM, HIGH)")
            @RequestParam(required = false) String severity,

            @Parameter(description = "Filter by status (e.g. ACTIVE, RESOLVED)")
            @RequestParam(required = false) String status,

            @Parameter(description = "Filter by risk level of assigned risk zone (LOW, MEDIUM, HIGH, CRITICAL)")
            @RequestParam(required = false) RiskLevel riskLevel,

            @Parameter(description = "Filter by specific risk zone ID")
            @RequestParam(required = false) Long riskZoneId,

            @Parameter(description = "Filter events occurring from timestamp (ISO format e.g. 2026-01-01T00:00:00)")
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime occurredFrom,

            @Parameter(description = "Filter events occurring to timestamp (ISO format e.g. 2026-12-31T23:59:59)")
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime occurredTo
    ) {
        return landslideEventService.filterEvents(severity, status, riskLevel, riskZoneId, occurredFrom, occurredTo);
    }

    @GetMapping("/nearby")
    @Operation(summary = "Find Nearby Landslides", description = "Finds landslide events within a specified radius (in METERS) of a given coordinate using PostGIS ST_DWithin.")
    public List<LandslideEventResponse> getNearbyLandslides(
            @Parameter(description = "Latitude (-90 to 90)") @RequestParam Double latitude,
            @Parameter(description = "Longitude (-180 to 180)") @RequestParam Double longitude,
            @Parameter(description = "Search radius distance in METERS") @RequestParam Double distance
    ) {
        return landslideEventService.findNearbyLandslides(latitude, longitude, distance);
    }

    @GetMapping("/{id}/intelligence")
    @Operation(summary = "Get Landslide Intelligence", description = "Calculates proximity analysis for nearby risk zones and infrastructure for a specific landslide event.")
    public LandslideIntelligenceResponse getLandslideIntelligence(
            @PathVariable Long id
    ) {
        return landslideIntelligenceService.getLandslideIntelligence(id);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get Landslide Event by ID", description = "Retrieves details of a single landslide event by its ID.")
    public LandslideEventResponse getEventById(
            @PathVariable Long id
    ) {
        return landslideEventService.getEventById(id);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete Landslide Event", description = "Deletes a landslide event record by its ID.")
    public void deleteEvent(
            @PathVariable Long id
    ) {
        landslideEventService.deleteEvent(id);
    }
}
