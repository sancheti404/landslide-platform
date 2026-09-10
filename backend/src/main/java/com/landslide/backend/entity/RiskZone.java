package com.landslide.backend.entity;

import jakarta.persistence.*;
import org.locationtech.jts.geom.MultiPolygon;

import java.time.LocalDateTime;

@Entity
@Table(name = "risk_zones")
public class RiskZone {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private RiskLevel riskLevel;

    @Column(columnDefinition = "geometry(MultiPolygon,4326)", nullable = false)
    private MultiPolygon boundary;

    @Column(length = 2000)
    private String description;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    public Long getId() {
        return id;
    }

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

    public MultiPolygon getBoundary() {
        return boundary;
    }

    public void setBoundary(MultiPolygon boundary) {
        this.boundary = boundary;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
}
