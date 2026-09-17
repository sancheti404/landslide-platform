import { apiRequest } from './api';

/**
 * Fetches Uttarakhand state boundary GeoJSON from Spring Boot
 * GET /api/gis/state-boundary
 */
export async function getStateBoundary() {
  return apiRequest('/api/gis/state-boundary', {
    method: 'GET',
    timeout: 10000,
  });
}

/**
 * Queries historical landslides from GSI NLSM inventory
 * GET /api/gis/historical-landslides
 */
export async function getHistoricalLandslides(params = {}) {
  const query = new URLSearchParams();
  if (params.district) query.append('district', params.district);
  if (params.movementType) query.append('movementType', params.movementType);
  if (params.minLon) query.append('minLon', params.minLon);
  if (params.minLat) query.append('minLat', params.minLat);
  if (params.maxLon) query.append('maxLon', params.maxLon);
  if (params.maxLat) query.append('maxLat', params.maxLat);
  if (params.limit) query.append('limit', params.limit);

  const qs = query.toString();
  return apiRequest(`/api/gis/historical-landslides${qs ? `?${qs}` : ''}`, {
    method: 'GET',
    timeout: 15000,
  });
}

/**
 * Retrieves landslide count breakdown per district
 * GET /api/gis/district-summary
 */
export async function getDistrictSummary() {
  return apiRequest('/api/gis/district-summary', {
    method: 'GET',
    timeout: 5000,
  });
}

/**
 * Retrieves GIS layer catalog and provenance metadata
 * GET /api/gis/metadata
 */
export async function getGisMetadata() {
  return apiRequest('/api/gis/metadata', {
    method: 'GET',
    timeout: 5000,
  });
}
