package com.landslide.backend.controller;

import com.landslide.backend.dto.CreateInfrastructureRequest;
import com.landslide.backend.dto.InfrastructureResponse;
import com.landslide.backend.entity.InfrastructureType;
import com.landslide.backend.service.InfrastructureService;

import jakarta.validation.Valid;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/infrastructure")
public class InfrastructureController {

    private final InfrastructureService infrastructureService;

    public InfrastructureController(InfrastructureService infrastructureService) {
        this.infrastructureService = infrastructureService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public InfrastructureResponse createInfrastructure(
            @Valid @RequestBody CreateInfrastructureRequest request
    ) {
        return infrastructureService.createInfrastructure(request);
    }

    @GetMapping
    public List<InfrastructureResponse> getAllInfrastructure() {
        return infrastructureService.getAllInfrastructure();
    }

    @GetMapping("/{id}")
    public InfrastructureResponse getInfrastructureById(
            @PathVariable Long id
    ) {
        return infrastructureService.getInfrastructureById(id);
    }

    @GetMapping("/type/{type}")
    public List<InfrastructureResponse> getInfrastructureByType(
            @PathVariable InfrastructureType type
    ) {
        return infrastructureService.getInfrastructureByType(type);
    }

    @GetMapping("/nearby")
    public List<InfrastructureResponse> findNearbyInfrastructure(
            @RequestParam Double latitude,
            @RequestParam Double longitude,
            @RequestParam(defaultValue = "10.0") Double distanceKm
    ) {
        return infrastructureService.findNearbyInfrastructure(latitude, longitude, distanceKm);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteInfrastructure(
            @PathVariable Long id
    ) {
        infrastructureService.deleteInfrastructure(id);
    }
}
