package com.landslide.backend.validation;

import com.landslide.backend.exception.UnsupportedLocationException;
import org.springframework.stereotype.Component;

@Component
public class UttarakhandGeoValidator {

    public static final double MIN_LAT = 28.50;
    public static final double MAX_LAT = 31.60;
    public static final double MIN_LON = 77.40;
    public static final double MAX_LON = 81.30;

    public boolean isWithinOperationalEnvelope(Double latitude, Double longitude) {
        if (latitude == null || longitude == null) {
            return false;
        }
        if (Double.isNaN(latitude) || Double.isNaN(longitude) || Double.isInfinite(latitude) || Double.isInfinite(longitude)) {
            return false;
        }
        return latitude >= MIN_LAT && latitude <= MAX_LAT && longitude >= MIN_LON && longitude <= MAX_LON;
    }

    public void validateOperationalEnvelope(Double latitude, Double longitude) {
        if (latitude == null || longitude == null) {
            throw new UnsupportedLocationException(
                    "Coordinates cannot be null",
                    latitude, longitude
            );
        }
        if (!isWithinOperationalEnvelope(latitude, longitude)) {
            throw new UnsupportedLocationException(
                    String.format(
                            "Selected coordinate (%.6f, %.6f) is outside the supported Uttarakhand operational envelope [%.2f–%.2f°N, %.2f–%.2f°E].",
                            latitude, longitude, MIN_LAT, MAX_LAT, MIN_LON, MAX_LON
                    ),
                    latitude, longitude
            );
        }
    }
}
