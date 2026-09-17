package com.landslide.backend.entity;

import jakarta.persistence.*;
import org.locationtech.jts.geom.Point;

import java.time.LocalDateTime;

@Entity
@Table(name = "landslide_events")
public class LandslideEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Double latitude;

    @Column(nullable = false)
    private Double longitude;

    @Column(columnDefinition = "geometry(Point,4326)")
    private Point location;

    @Column(nullable = false)
    private String severity;

    @Column(nullable = false)
    private String status;

    private String source;

    @Column(name = "slide_no", length = 100)
    private String slideNo;

    @Column(name = "district", length = 100)
    private String district;

    @Column(name = "slide_name", length = 255)
    private String slideName;

    @Column(name = "material_involved", length = 100)
    private String materialInvolved;

    @Column(name = "movement_type", length = 100)
    private String movementType;

    @Column(name = "history", length = 100)
    private String history;

    @ManyToOne
    @JoinColumn(name = "risk_zone_id")
    private RiskZone riskZone;

    private LocalDateTime occurredAt;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }


    // Getters and Setters

    public Long getId() {
        return id;
    }

    public Double getLatitude() {
        return latitude;
    }

    public void setLatitude(Double latitude) {
        this.latitude = latitude;
    }

    public Double getLongitude() {
        return longitude;
    }

    public void setLongitude(Double longitude) {
        this.longitude = longitude;
    }

    public Point getLocation() {
        return location;
    }

    public void setLocation(Point location) {
        this.location = location;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public String getSlideNo() {
        return slideNo;
    }

    public void setSlideNo(String slideNo) {
        this.slideNo = slideNo;
    }

    public String getDistrict() {
        return district;
    }

    public void setDistrict(String district) {
        this.district = district;
    }

    public String getSlideName() {
        return slideName;
    }

    public void setSlideName(String slideName) {
        this.slideName = slideName;
    }

    public String getMaterialInvolved() {
        return materialInvolved;
    }

    public void setMaterialInvolved(String materialInvolved) {
        this.materialInvolved = materialInvolved;
    }

    public String getMovementType() {
        return movementType;
    }

    public void setMovementType(String movementType) {
        this.movementType = movementType;
    }

    public String getHistory() {
        return history;
    }

    public void setHistory(String history) {
        this.history = history;
    }

    public RiskZone getRiskZone() {
        return riskZone;
    }


    public void setRiskZone(RiskZone riskZone) {
        this.riskZone = riskZone;
    }

    public LocalDateTime getOccurredAt() {
        return occurredAt;
    }

    public void setOccurredAt(LocalDateTime occurredAt) {
        this.occurredAt = occurredAt;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
}
