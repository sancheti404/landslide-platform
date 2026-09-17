import { apiRequest } from './api';

/**
 * Executes multimodal landslide risk assessment through Spring Boot gateway
 * POST /api/risk/assess
 */
export async function assessLandslideRisk({
  latitude,
  longitude,
  timestamp,
  rainfallWeight = 0.50,
  combinationMode = 'multiplicative'
}) {
  return apiRequest('/api/risk/assess', {
    method: 'POST',
    body: JSON.stringify({
      latitude: Number(latitude),
      longitude: Number(longitude),
      timestamp: timestamp || new Date().toISOString().split('T')[0],
      rainfallWeight,
      combinationMode,
    }),
  });
}

/**
 * Queries health status of the ML inference subsystem via Spring Boot
 * GET /api/risk/ml-health
 */
export async function getMlHealth() {
  return apiRequest('/api/risk/ml-health', {
    method: 'GET',
    timeout: 5000,
  });
}
