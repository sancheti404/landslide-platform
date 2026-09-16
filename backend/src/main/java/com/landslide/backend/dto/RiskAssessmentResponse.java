package com.landslide.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.landslide.backend.entity.RiskLevel;

public class RiskAssessmentResponse {

    private Double latitude;
    private Double longitude;
    private String timestamp;

    @JsonProperty("xgboost_probability")
    private Double xgboostProbability;

    @JsonProperty("swin_probability")
    private Double swinProbability;

    @JsonProperty("static_visual_fusion_score")
    private Double staticVisualFusionScore;

    @JsonProperty("rainfall_3d_mm")
    private Double rainfall3dMm;

    @JsonProperty("rainfall_7d_mm")
    private Double rainfall7dMm;

    @JsonProperty("rainfall_14d_mm")
    private Double rainfall14dMm;

    @JsonProperty("rainfall_30d_mm")
    private Double rainfall30dMm;

    @JsonProperty("maximum_daily_rainfall_mm")
    private Double maximumDailyRainfallMm;

    @JsonProperty("rainfall_anomaly")
    private Double rainfallAnomaly;

    @JsonProperty("dynamic_rainfall_trigger_score")
    private Double dynamicRainfallTriggerScore;

    @JsonProperty("trigger_indicator")
    private String triggerIndicator;

    @JsonProperty("operational_landslide_risk_score")
    private Double operationalLandslideRiskScore;

    @JsonProperty("risk_level")
    private RiskLevel riskLevel;

    @JsonProperty("model_version")
    private String modelVersion;

    private String status;

    // PostGIS Spatial Enrichment
    @JsonProperty("intersecting_risk_zone_id")
    private Long intersectingRiskZoneId;

    @JsonProperty("intersecting_risk_zone_name")
    private String intersectingRiskZoneName;

    @JsonProperty("intersecting_risk_zone_level")
    private RiskLevel intersectingRiskZoneLevel;

    @JsonProperty("nearby_hospitals_count")
    private Integer nearbyHospitalsCount;

    @JsonProperty("nearby_shelters_count")
    private Integer nearbySheltersCount;

    @JsonProperty("nearby_police_stations_count")
    private Integer nearbyPoliceStationsCount;

    @JsonProperty("nearby_roads_count")
    private Integer nearbyRoadsCount;

    public RiskAssessmentResponse() {
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

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public Double getXgboostProbability() {
        return xgboostProbability;
    }

    public void setXgboostProbability(Double xgboostProbability) {
        this.xgboostProbability = xgboostProbability;
    }

    public Double getSwinProbability() {
        return swinProbability;
    }

    public void setSwinProbability(Double swinProbability) {
        this.swinProbability = swinProbability;
    }

    public Double getStaticVisualFusionScore() {
        return staticVisualFusionScore;
    }

    public void setStaticVisualFusionScore(Double staticVisualFusionScore) {
        this.staticVisualFusionScore = staticVisualFusionScore;
    }

    public Double getRainfall3dMm() {
        return rainfall3dMm;
    }

    public void setRainfall3dMm(Double rainfall3dMm) {
        this.rainfall3dMm = rainfall3dMm;
    }

    public Double getRainfall7dMm() {
        return rainfall7dMm;
    }

    public void setRainfall7dMm(Double rainfall7dMm) {
        this.rainfall7dMm = rainfall7dMm;
    }

    public Double getRainfall14dMm() {
        return rainfall14dMm;
    }

    public void setRainfall14dMm(Double rainfall14dMm) {
        this.rainfall14dMm = rainfall14dMm;
    }

    public Double getRainfall30dMm() {
        return rainfall30dMm;
    }

    public void setRainfall30dMm(Double rainfall30dMm) {
        this.rainfall30dMm = rainfall30dMm;
    }

    public Double getMaximumDailyRainfallMm() {
        return maximumDailyRainfallMm;
    }

    public void setMaximumDailyRainfallMm(Double maximumDailyRainfallMm) {
        this.maximumDailyRainfallMm = maximumDailyRainfallMm;
    }

    public Double getRainfallAnomaly() {
        return rainfallAnomaly;
    }

    public void setRainfallAnomaly(Double rainfallAnomaly) {
        this.rainfallAnomaly = rainfallAnomaly;
    }

    public Double getDynamicRainfallTriggerScore() {
        return dynamicRainfallTriggerScore;
    }

    public void setDynamicRainfallTriggerScore(Double dynamicRainfallTriggerScore) {
        this.dynamicRainfallTriggerScore = dynamicRainfallTriggerScore;
    }

    public String getTriggerIndicator() {
        return triggerIndicator;
    }

    public void setTriggerIndicator(String triggerIndicator) {
        this.triggerIndicator = triggerIndicator;
    }

    public Double getOperationalLandslideRiskScore() {
        return operationalLandslideRiskScore;
    }

    public void setOperationalLandslideRiskScore(Double operationalLandslideRiskScore) {
        this.operationalLandslideRiskScore = operationalLandslideRiskScore;
    }

    public RiskLevel getRiskLevel() {
        return riskLevel;
    }

    public void setRiskLevel(RiskLevel riskLevel) {
        this.riskLevel = riskLevel;
    }

    public String getModelVersion() {
        return modelVersion;
    }

    public void setModelVersion(String modelVersion) {
        this.modelVersion = modelVersion;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public Long getIntersectingRiskZoneId() {
        return intersectingRiskZoneId;
    }

    public void setIntersectingRiskZoneId(Long intersectingRiskZoneId) {
        this.intersectingRiskZoneId = intersectingRiskZoneId;
    }

    public String getIntersectingRiskZoneName() {
        return intersectingRiskZoneName;
    }

    public void setIntersectingRiskZoneName(String intersectingRiskZoneName) {
        this.intersectingRiskZoneName = intersectingRiskZoneName;
    }

    public RiskLevel getIntersectingRiskZoneLevel() {
        return intersectingRiskZoneLevel;
    }

    public void setIntersectingRiskZoneLevel(RiskLevel intersectingRiskZoneLevel) {
        this.intersectingRiskZoneLevel = intersectingRiskZoneLevel;
    }

    public Integer getNearbyHospitalsCount() {
        return nearbyHospitalsCount;
    }

    public void setNearbyHospitalsCount(Integer nearbyHospitalsCount) {
        this.nearbyHospitalsCount = nearbyHospitalsCount;
    }

    public Integer getNearbySheltersCount() {
        return nearbySheltersCount;
    }

    public void setNearbySheltersCount(Integer nearbySheltersCount) {
        this.nearbySheltersCount = nearbySheltersCount;
    }

    public Integer getNearbyPoliceStationsCount() {
        return nearbyPoliceStationsCount;
    }

    public void setNearbyPoliceStationsCount(Integer nearbyPoliceStationsCount) {
        this.nearbyPoliceStationsCount = nearbyPoliceStationsCount;
    }

    public Integer getNearbyRoadsCount() {
        return nearbyRoadsCount;
    }

    public void setNearbyRoadsCount(Integer nearbyRoadsCount) {
        this.nearbyRoadsCount = nearbyRoadsCount;
    }
}
