package com.landslide.backend.exception;

public class MlServiceException extends RuntimeException {

    private final int statusCode;
    private final String errorCode;

    public MlServiceException(String message) {
        super(message);
        this.statusCode = 502;
        this.errorCode = "ML_SERVICE_ERROR";
    }

    public MlServiceException(String message, int statusCode) {
        super(message);
        this.statusCode = statusCode;
        this.errorCode = statusCode == 400 ? "UNSUPPORTED_LOCATION" : "ML_SERVICE_ERROR";
    }

    public MlServiceException(String message, int statusCode, String errorCode) {
        super(message);
        this.statusCode = statusCode;
        this.errorCode = errorCode;
    }

    public MlServiceException(String message, Throwable cause) {
        super(message, cause);
        this.statusCode = 503;
        this.errorCode = "ML_SERVICE_UNAVAILABLE";
    }

    public MlServiceException(String message, Throwable cause, int statusCode, String errorCode) {
        super(message, cause);
        this.statusCode = statusCode;
        this.errorCode = errorCode;
    }

    public int getStatusCode() {
        return statusCode;
    }

    public String getErrorCode() {
        return errorCode;
    }
}

