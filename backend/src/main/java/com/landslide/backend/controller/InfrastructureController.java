package com.landslide.backend.controller;

import com.landslide.backend.dto.CreateInfrastructureRequest;
import com.landslide.backend.dto.InfrastructureResponse;
import com.landslide.backend.service.InfrastructureService;

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
    public InfrastructureResponse createInfrastructure(
            @Valid @RequestBody CreateInfrastructureRequest request
    ) {
        return infrastructureService
                .createInfrastructure(request);
    }

    // GET ALL
    @GetMapping
    public List<InfrastructureResponse> getAllInfrastructure() {
        return infrastructureService
                .getAllInfrastructure();
    }

    // GET NEARBY
    @GetMapping("/nearby")
    public List<InfrastructureResponse> findNearbyInfrastructure(
            @RequestParam
            @DecimalMin(value = "-90.0", message = "Latitude must be at least -90")
            @DecimalMax(value = "90.0", message = "Latitude must be at most 90")
            Double latitude,

            @RequestParam
            @DecimalMin(value = "-180.0", message = "Longitude must be at least -180")
            @DecimalMax(value = "180.0", message = "Longitude must be at most 180")
            Double longitude,

            @RequestParam
            @Positive(message = "Distance must be greater than 0")
            Double distance
    ) {
        return infrastructureService
                .findNearbyInfrastructure(latitude, longitude, distance);
    }

    // GET BY ID
    @GetMapping("/{id}")
    public InfrastructureResponse getInfrastructureById(
            @PathVariable Long id
    ) {
        return infrastructureService
                .getInfrastructureById(id);
    }

    // DELETE
    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteInfrastructure(
            @PathVariable Long id
    ) {
        infrastructureService.deleteInfrastructure(id);
    }
}
