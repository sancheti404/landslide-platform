package com.landslide.backend.dto;

import com.landslide.backend.entity.RiskLevel;

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

    private Long riskZoneId;
    private String riskZoneName;
    private RiskLevel riskLevel;

    private String slideNo;
    private String district;
    private String slideName;
    private String materialInvolved;
    private String movementType;
    private String history;

    public LandslideEventResponse() {}

    public LandslideEventResponse(
            Long id,
            Double latitude,
            Double longitude,
            String severity,
            String status,
            String source,
            LocalDateTime occurredAt,
            LocalDateTime createdAt,
            Long riskZoneId,
            String riskZoneName,
            RiskLevel riskLevel
    ) {
        this(id, latitude, longitude, severity, status, source, occurredAt, createdAt,
                riskZoneId, riskZoneName, riskLevel, null, null, null, null, null, null);
    }

    public LandslideEventResponse(
            Long id,
            Double latitude,
            Double longitude,
            String severity,
            String status,
            String source,
            LocalDateTime occurredAt,
            LocalDateTime createdAt,
            Long riskZoneId,
            String riskZoneName,
            RiskLevel riskLevel,
            String slideNo,
            String district,
            String slideName,
            String materialInvolved,
            String movementType,
            String history
    ) {
        this.id = id;
        this.latitude = latitude;
        this.longitude = longitude;
        this.severity = severity;
        this.status = status;
        this.source = source;
        this.occurredAt = occurredAt;
        this.createdAt = createdAt;
        this.riskZoneId = riskZoneId;
        this.riskZoneName = riskZoneName;
        this.riskLevel = riskLevel;
        this.slideNo = slideNo;
        this.district = district;
        this.slideName = slideName;
        this.materialInvolved = materialInvolved;
        this.movementType = movementType;
        this.history = history;
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

    public Long getRiskZoneId() {
        return riskZoneId;
    }

    public String getRiskZoneName() {
        return riskZoneName;
    }

    public RiskLevel getRiskLevel() {
        return riskLevel;
    }

    public String getSlideNo() {
        return slideNo;
    }

    public String getDistrict() {
        return district;
    }

    public String getSlideName() {
        return slideName;
    }

    public String getMaterialInvolved() {
        return materialInvolved;
    }

    public String getMovementType() {
        return movementType;
    }

    public String getHistory() {
        return history;
    }
}

