package com.landslide.backend.dto;

import com.landslide.backend.entity.RiskLevel;

import java.time.LocalDateTime;

public class RiskZoneResponse {

    private Long id;
    private String name;
    private RiskLevel riskLevel;
    private String boundary;
    private String description;
    private LocalDateTime createdAt;

    public RiskZoneResponse(
            Long id,
            String name,
            RiskLevel riskLevel,
            String boundary,
            String description,
            LocalDateTime createdAt
    ) {
        this.id = id;
        this.name = name;
        this.riskLevel = riskLevel;
        this.boundary = boundary;
        this.description = description;
        this.createdAt = createdAt;
    }

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public RiskLevel getRiskLevel() {
        return riskLevel;
    }

    public String getBoundary() {
        return boundary;
    }

    public String getDescription() {
        return description;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
}
