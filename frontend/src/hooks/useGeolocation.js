import { useState, useCallback } from 'react';
import { isWithinUttarakhand } from '../utils/geoValidators';

/**
 * Hook for explicit, user-initiated browser geolocation
 * Handles permissions, timeouts, device errors, and envelope boundary verification.
 */
export function useGeolocation() {
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isInsideUttarakhand, setIsInsideUttarakhand] = useState(null);

  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setError({
        code: 'UNSUPPORTED',
        message: 'Geolocation is not supported by your current browser.',
      });
      return;
    }

    setLoading(true);
    setError(null);

    const options = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0,
    };

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const accuracy = position.coords.accuracy;

        const inside = isWithinUttarakhand(lat, lon);

        setLocation({
          latitude: lat,
          longitude: lon,
          accuracy,
          timestamp: position.timestamp,
        });
        setIsInsideUttarakhand(inside);
        setLoading(false);

        if (!inside) {
          setError({
            code: 'OUTSIDE_OPERATIONAL_ENVELOPE',
            message: `Your current location (${lat.toFixed(4)}, ${lon.toFixed(4)}) is outside the Uttarakhand operational envelope [28.50–31.60°N, 77.40–81.30°E]. Operational risk calculations are restricted to Uttarakhand.`,
            coordinates: { latitude: lat, longitude: lon },
          });
        }
      },
      (geoError) => {
        setLoading(false);
        let message = 'Unable to retrieve location.';
        let code = 'UNKNOWN_ERROR';

        switch (geoError.code) {
          case geoError.PERMISSION_DENIED:
            code = 'PERMISSION_DENIED';
            message = 'Location access was denied. Please allow location permissions in your browser settings to use this feature.';
            break;
          case geoError.POSITION_UNAVAILABLE:
            code = 'POSITION_UNAVAILABLE';
            message = 'Location information is currently unavailable from your device.';
            break;
          case geoError.TIMEOUT:
            code = 'TIMEOUT';
            message = 'Location request timed out. Please verify your connection or try again.';
            break;
          default:
            code = 'UNKNOWN_ERROR';
            message = geoError.message || 'An unknown error occurred while retrieving location.';
        }

        setError({ code, message });
      },
      options
    );
  }, []);

  const clearLocation = useCallback(() => {
    setLocation(null);
    setError(null);
    setIsInsideUttarakhand(null);
  }, []);

  return {
    location,
    loading,
    error,
    isInsideUttarakhand,
    requestLocation,
    clearLocation,
  };
}
