package com.landslide.backend.dto;

import java.time.LocalDateTime;

public class LandslideEventResponse {

    private Long id;
    private Double latitude;
    private Double longitude;
    private String severity;
    private String status;
    private String source;
    private LocalDateTime occurredAt;
    private LocalDateTime createdAt;

    public LandslideEventResponse(
            Long id,
            Double latitude,
            Double longitude,
            String severity,
            String status,
            String source,
            LocalDateTime occurredAt,
            LocalDateTime createdAt
    ) {
        this.id = id;
        this.latitude = latitude;
        this.longitude = longitude;
        this.severity = severity;
        this.status = status;
        this.source = source;
        this.occurredAt = occurredAt;
        this.createdAt = createdAt;
    }

    public Long getId() {
        return id;
    }

    public Double getLatitude() {
        return latitude;
    }

    public Double getLongitude() {
        return longitude;
    }

    public String getSeverity() {
        return severity;
    }

    public String getStatus() {
        return status;
    }

    public String getSource() {
        return source;
    }

    public LocalDateTime getOccurredAt() {
        return occurredAt;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
}
