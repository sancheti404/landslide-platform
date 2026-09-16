package com.landslide.backend.dto;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class RiskAssessmentRequest {

    @NotNull(message = "Latitude is required")
    @DecimalMin(value = "28.0", message = "Latitude must be within Uttarakhand region (>= 28.0)")
    @DecimalMax(value = "32.0", message = "Latitude must be within Uttarakhand region (<= 32.0)")
    private Double latitude;

    @NotNull(message = "Longitude is required")
    @DecimalMin(value = "77.0", message = "Longitude must be within Uttarakhand region (>= 77.0)")
    @DecimalMax(value = "82.0", message = "Longitude must be within Uttarakhand region (<= 82.0)")
    private Double longitude;

    @NotBlank(message = "Timestamp is required (YYYY-MM-DD or ISO-8601)")
    private String timestamp;

    private Double rainfallWeight = 0.50;

    private String combinationMode = "multiplicative";

    public RiskAssessmentRequest() {
    }

    public RiskAssessmentRequest(Double latitude, Double longitude, String timestamp) {
        this.latitude = latitude;
        this.longitude = longitude;
        this.timestamp = timestamp;
    }

    public RiskAssessmentRequest(Double latitude, Double longitude, String timestamp, Double rainfallWeight, String combinationMode) {
        this.latitude = latitude;
        this.longitude = longitude;
        this.timestamp = timestamp;
        this.rainfallWeight = rainfallWeight != null ? rainfallWeight : 0.50;
        this.combinationMode = combinationMode != null ? combinationMode : "multiplicative";
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

    public Double getRainfallWeight() {
        return rainfallWeight;
    }

    public void setRainfallWeight(Double rainfallWeight) {
        this.rainfallWeight = rainfallWeight;
    }

    public String getCombinationMode() {
        return combinationMode;
    }

    public void setCombinationMode(String combinationMode) {
        this.combinationMode = combinationMode;
    }
}
