package com.landslide.backend.controller;

import com.landslide.backend.dto.CreateInfrastructureRequest;
import com.landslide.backend.dto.InfrastructureResponse;
import com.landslide.backend.service.InfrastructureService;

import jakarta.validation.Valid;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/infrastructure")
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
