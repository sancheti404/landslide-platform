package com.landslide.backend.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@Tag(name = "System", description = "Endpoints for application and database health verification")
public class HealthController {

    @PersistenceContext
    private EntityManager entityManager;

    @GetMapping("/")
    @Operation(summary = "Root Endpoint", description = "Returns welcome message confirming API service is running.")
    public Map<String, String> home() {
        return Map.of(
                "message", "Landslide Risk Management API is running"
        );
    }

    @GetMapping("/api/health")
    @Operation(summary = "Health Check", description = "Verifies overall application status, PostgreSQL database connectivity, and PostGIS spatial engine status.")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> healthStatus = new HashMap<>();

        boolean dbUp = checkDatabaseConnection();
        boolean postgisUp = checkPostGisAvailability();

        healthStatus.put("database", dbUp ? "UP" : "DOWN");
        healthStatus.put("postgis", postgisUp ? "UP" : "DOWN");

        if (dbUp && postgisUp) {
            healthStatus.put("status", "UP");
            return ResponseEntity.ok(healthStatus);
        } else {
            healthStatus.put("status", "DOWN");
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(healthStatus);
        }
    }

    private boolean checkDatabaseConnection() {
        try {
            Object result = entityManager.createNativeQuery("SELECT 1").getSingleResult();
            return result != null;
        } catch (Exception e) {
            return false;
        }
    }

    private boolean checkPostGisAvailability() {
        try {
            Object result = entityManager.createNativeQuery("SELECT PostGIS_Version()").getSingleResult();
            return result != null;
        } catch (Exception e) {
            return false;
        }
    }
}
