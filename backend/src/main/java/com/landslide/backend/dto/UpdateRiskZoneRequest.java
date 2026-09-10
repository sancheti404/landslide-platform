package com.landslide.backend.dto;

import com.landslide.backend.entity.RiskLevel;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class UpdateRiskZoneRequest {

    @NotBlank(message = "Risk zone name is required")
    private String name;

    @NotNull(message = "Risk level is required")
    private RiskLevel riskLevel;

    @NotBlank(message = "Boundary WKT is required")
    private String boundary;

    private String description;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public RiskLevel getRiskLevel() {
        return riskLevel;
    }

    public void setRiskLevel(RiskLevel riskLevel) {
        this.riskLevel = riskLevel;
    }

    public String getBoundary() {
        return boundary;
    }

    public void setBoundary(String boundary) {
        this.boundary = boundary;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }
}
