package com.landslide.backend;

import com.landslide.backend.exception.UnsupportedLocationException;
import com.landslide.backend.validation.UttarakhandGeoValidator;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class UttarakhandGeoValidatorTest {

    private UttarakhandGeoValidator validator;

    @BeforeEach
    void setUp() {
        validator = new UttarakhandGeoValidator();
    }

    @Test
    void testA_ValidInteriorCoordinate() {
        assertTrue(validator.isWithinOperationalEnvelope(30.529505, 79.085957));
        assertDoesNotThrow(() -> validator.validateOperationalEnvelope(30.529505, 79.085957));
    }

    @Test
    void testB_DiscoveredBugInvalidLongitude() {
        // 29.580286 N, 82.808874 E is outside the 81.30 max longitude
        assertFalse(validator.isWithinOperationalEnvelope(29.580286, 82.808874));
        UnsupportedLocationException ex = assertThrows(
                UnsupportedLocationException.class,
                () -> validator.validateOperationalEnvelope(29.580286, 82.808874)
        );
        assertEquals("UNSUPPORTED_LOCATION", ex.getErrorCode());
        assertEquals(29.580286, ex.getLatitude());
        assertEquals(82.808874, ex.getLongitude());
    }

    @Test
    void testC_LongitudeLowerBoundary() {
        assertTrue(validator.isWithinOperationalEnvelope(30.0, 77.40));
        assertDoesNotThrow(() -> validator.validateOperationalEnvelope(30.0, 77.40));
    }

    @Test
    void testD_LongitudeUpperBoundary() {
        assertTrue(validator.isWithinOperationalEnvelope(30.0, 81.30));
        assertDoesNotThrow(() -> validator.validateOperationalEnvelope(30.0, 81.30));
    }

    @Test
    void testE_LongitudeJustOutsideUpperBoundary() {
        assertFalse(validator.isWithinOperationalEnvelope(30.0, 81.300001));
        assertThrows(
                UnsupportedLocationException.class,
                () -> validator.validateOperationalEnvelope(30.0, 81.300001)
        );
    }

    @Test
    void testF_LatitudeLowerBoundary() {
        assertTrue(validator.isWithinOperationalEnvelope(28.50, 79.0));
        assertDoesNotThrow(() -> validator.validateOperationalEnvelope(28.50, 79.0));
    }

    @Test
    void testG_LatitudeUpperBoundary() {
        assertTrue(validator.isWithinOperationalEnvelope(31.60, 79.0));
        assertDoesNotThrow(() -> validator.validateOperationalEnvelope(31.60, 79.0));
    }

    @Test
    void testH_LatitudeJustOutsideUpperBoundary() {
        assertFalse(validator.isWithinOperationalEnvelope(31.600001, 79.0));
        assertThrows(
                UnsupportedLocationException.class,
                () -> validator.validateOperationalEnvelope(31.600001, 79.0)
        );
    }

    @Test
    void testI_FarOutsideCoordinate() {
        assertFalse(validator.isWithinOperationalEnvelope(25.0, 90.0));
        assertThrows(
                UnsupportedLocationException.class,
                () -> validator.validateOperationalEnvelope(25.0, 90.0)
        );
    }

    @Test
    void testNullOrInvalidCoordinates() {
        assertFalse(validator.isWithinOperationalEnvelope(null, 79.0));
        assertFalse(validator.isWithinOperationalEnvelope(30.0, null));
        assertFalse(validator.isWithinOperationalEnvelope(Double.NaN, 79.0));
        assertThrows(UnsupportedLocationException.class, () -> validator.validateOperationalEnvelope(null, 79.0));
    }
}
