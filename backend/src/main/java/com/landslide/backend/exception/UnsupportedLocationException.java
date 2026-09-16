package com.landslide.backend.exception;

public class UnsupportedLocationException extends RuntimeException {

    private final Double latitude;
    private final Double longitude;
    private final String errorCode;

    public UnsupportedLocationException(String message, Double latitude, Double longitude) {
        super(message);
        this.latitude = latitude;
        this.longitude = longitude;
        this.errorCode = "UNSUPPORTED_LOCATION";
    }

    public Double getLatitude() {
        return latitude;
    }

    public Double getLongitude() {
        return longitude;
    }

    public String getErrorCode() {
        return errorCode;
    }
}
