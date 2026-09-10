package com.landslide.backend.dto;

import com.landslide.backend.entity.InfrastructureType;

import java.time.LocalDateTime;

public class InfrastructureResponse {

    private Long id;
    private String name;
    private InfrastructureType type;
    private Double latitude;
    private Double longitude;
    private String description;
    private LocalDateTime createdAt;

    public InfrastructureResponse(
            Long id,
            String name,
            InfrastructureType type,
            Double latitude,
            Double longitude,
            String description,
            LocalDateTime createdAt
    ) {
        this.id = id;
        this.name = name;
        this.type = type;
        this.latitude = latitude;
        this.longitude = longitude;
        this.description = description;
        this.createdAt = createdAt;
    }

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public InfrastructureType getType() {
        return type;
    }

    public Double getLatitude() {
        return latitude;
    }

    public Double getLongitude() {
        return longitude;
    }

    public String getDescription() {
        return description;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
}
