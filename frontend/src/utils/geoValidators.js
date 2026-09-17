import { UTTARAKHAND_ENVELOPE } from '../constants/geographicBounds';

/**
 * Validates whether a coordinate pair falls strictly within the Uttarakhand operational envelope
 * [28.50 <= lat <= 31.60] and [77.40 <= lon <= 81.30]
 */
export function isWithinUttarakhand(lat, lon) {
  const latitude = typeof lat === 'number' ? lat : parseFloat(lat);
  const longitude = typeof lon === 'number' ? lon : parseFloat(lon);

  if (isNaN(latitude) || isNaN(longitude)) {
    return false;
  }

  return (
    latitude >= UTTARAKHAND_ENVELOPE.MIN_LAT &&
    latitude <= UTTARAKHAND_ENVELOPE.MAX_LAT &&
    longitude >= UTTARAKHAND_ENVELOPE.MIN_LON &&
    longitude <= UTTARAKHAND_ENVELOPE.MAX_LON
  );
}

/**
 * Returns a detailed validation result with error messages if invalid
 */
export function validateCoordinates(lat, lon) {
  const latitude = typeof lat === 'number' ? lat : parseFloat(lat);
  const longitude = typeof lon === 'number' ? lon : parseFloat(lon);

  if (isNaN(latitude) || isNaN(longitude)) {
    return {
      isValid: false,
      reason: 'INVALID_NUMBERS',
      message: 'Latitude and Longitude must be valid decimal numbers.',
    };
  }

  if (latitude < -90 || latitude > 90) {
    return {
      isValid: false,
      reason: 'LAT_RANGE',
      message: 'Latitude must be between -90.0 and 90.0 degrees.',
    };
  }

  if (longitude < -180 || longitude > 180) {
    return {
      isValid: false,
      reason: 'LON_RANGE',
      message: 'Longitude must be between -180.0 and 180.0 degrees.',
    };
  }

  if (!isWithinUttarakhand(latitude, longitude)) {
    return {
      isValid: false,
      reason: 'OUTSIDE_OPERATIONAL_ENVELOPE',
      message: `Coordinate (${latitude.toFixed(4)}, ${longitude.toFixed(4)}) is outside the Uttarakhand operational envelope [${UTTARAKHAND_ENVELOPE.MIN_LAT}–${UTTARAKHAND_ENVELOPE.MAX_LAT}°N, ${UTTARAKHAND_ENVELOPE.MIN_LON}–${UTTARAKHAND_ENVELOPE.MAX_LON}°E].`,
    };
  }

  return {
    isValid: true,
    latitude,
    longitude,
  };
}
