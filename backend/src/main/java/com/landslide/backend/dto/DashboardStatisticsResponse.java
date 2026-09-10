package com.landslide.backend.dto;

import com.landslide.backend.entity.InfrastructureType;
import com.landslide.backend.entity.RiskLevel;

import java.util.Map;

public class DashboardStatisticsResponse {

    private long totalLandslides;
    private Map<String, Long> landslidesBySeverity;
    private Map<String, Long> landslidesByStatus;
    private Map<RiskLevel, Long> landslidesByRiskLevel;
    private long unassignedLandslides;
    private long totalRiskZones;
    private Map<RiskLevel, Long> riskZonesByRiskLevel;
    private long totalInfrastructure;
    private Map<InfrastructureType, Long> infrastructureByType;

    public DashboardStatisticsResponse() {
    }

    public DashboardStatisticsResponse(
            long totalLandslides,
            Map<String, Long> landslidesBySeverity,
            Map<String, Long> landslidesByStatus,
            Map<RiskLevel, Long> landslidesByRiskLevel,
            long unassignedLandslides,
            long totalRiskZones,
            Map<RiskLevel, Long> riskZonesByRiskLevel,
            long totalInfrastructure,
            Map<InfrastructureType, Long> infrastructureByType
    ) {
        this.totalLandslides = totalLandslides;
        this.landslidesBySeverity = landslidesBySeverity;
        this.landslidesByStatus = landslidesByStatus;
        this.landslidesByRiskLevel = landslidesByRiskLevel;
        this.unassignedLandslides = unassignedLandslides;
        this.totalRiskZones = totalRiskZones;
        this.riskZonesByRiskLevel = riskZonesByRiskLevel;
        this.totalInfrastructure = totalInfrastructure;
        this.infrastructureByType = infrastructureByType;
    }

    public long getTotalLandslides() {
        return totalLandslides;
    }

    public void setTotalLandslides(long totalLandslides) {
        this.totalLandslides = totalLandslides;
    }

    public Map<String, Long> getLandslidesBySeverity() {
        return landslidesBySeverity;
    }

    public void setLandslidesBySeverity(Map<String, Long> landslidesBySeverity) {
        this.landslidesBySeverity = landslidesBySeverity;
    }

    public Map<String, Long> getLandslidesByStatus() {
        return landslidesByStatus;
    }

    public void setLandslidesByStatus(Map<String, Long> landslidesByStatus) {
        this.landslidesByStatus = landslidesByStatus;
    }

    public Map<RiskLevel, Long> getLandslidesByRiskLevel() {
        return landslidesByRiskLevel;
    }

    public void setLandslidesByRiskLevel(Map<RiskLevel, Long> landslidesByRiskLevel) {
        this.landslidesByRiskLevel = landslidesByRiskLevel;
    }

    public long getUnassignedLandslides() {
        return unassignedLandslides;
    }

    public void setUnassignedLandslides(long unassignedLandslides) {
        this.unassignedLandslides = unassignedLandslides;
    }

    public long getTotalRiskZones() {
        return totalRiskZones;
    }

    public void setTotalRiskZones(long totalRiskZones) {
        this.totalRiskZones = totalRiskZones;
    }

    public Map<RiskLevel, Long> getRiskZonesByRiskLevel() {
        return riskZonesByRiskLevel;
    }

    public void setRiskZonesByRiskLevel(Map<RiskLevel, Long> riskZonesByRiskLevel) {
        this.riskZonesByRiskLevel = riskZonesByRiskLevel;
    }

    public long getTotalInfrastructure() {
        return totalInfrastructure;
    }

    public void setTotalInfrastructure(long totalInfrastructure) {
        this.totalInfrastructure = totalInfrastructure;
    }

    public Map<InfrastructureType, Long> getInfrastructureByType() {
        return infrastructureByType;
    }

    public void setInfrastructureByType(Map<InfrastructureType, Long> infrastructureByType) {
        this.infrastructureByType = infrastructureByType;
    }
}
