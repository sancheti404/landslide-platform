import { useState, useCallback } from 'react';
import { assessLandslideRisk } from '../services/riskApi';
import { isWithinUttarakhand } from '../utils/geoValidators';

/**
 * Hook for managing multimodal landslide risk evaluation state
 */
export function useRiskAssessment() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [latencyMs, setLatencyMs] = useState(null);

  const assess = useCallback(async (params) => {
    const { latitude, longitude, timestamp, rainfallWeight, combinationMode } = params;

    // Client-side envelope validation guard
    if (!isWithinUttarakhand(latitude, longitude)) {
      const envelopeError = new Error(
        `Coordinate (${Number(latitude).toFixed(4)}, ${Number(longitude).toFixed(4)}) is outside Uttarakhand operational envelope [28.50–31.60°N, 77.40–81.30°E]. Assessment blocked.`
      );
      envelopeError.isUnsupportedLocation = true;
      setError(envelopeError);
      setData(null);
      return null;
    }

    setLoading(true);
    setError(null);
    const t0 = performance.now();

    try {
      const result = await assessLandslideRisk({
        latitude,
        longitude,
        timestamp,
        rainfallWeight,
        combinationMode,
      });

      const elapsed = performance.now() - t0;
      setLatencyMs(elapsed);
      setData(result);
      setLoading(false);
      return result;
    } catch (err) {
      setLoading(false);
      setError(err);
      setData(null);
      throw err;
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLatencyMs(null);
  }, []);

  return {
    data,
    loading,
    error,
    latencyMs,
    assess,
    reset,
  };
}
