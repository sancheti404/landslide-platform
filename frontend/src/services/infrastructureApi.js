import { apiRequest } from './api';

/**
 * Queries emergency infrastructure within specified radius (in METERS)
 * GET /api/infrastructure/nearby
 */
export async function getNearbyInfrastructure({ latitude, longitude, distance = 5000, type }) {
  const query = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    distance: String(distance),
  });
  if (type) query.append('type', type);

  return apiRequest(`/api/infrastructure/nearby?${query.toString()}`, {
    method: 'GET',
    timeout: 8000,
  });
}

/**
 * Finds if a coordinate lies within a mapped risk zone polygon
 * GET /api/risk-zones/locate
 */
export async function locateRiskZone({ latitude, longitude }) {
  const query = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
  });

  return apiRequest(`/api/risk-zones/locate?${query.toString()}`, {
    method: 'GET',
    timeout: 8000,
  });
}
