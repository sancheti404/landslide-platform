/**
 * Google Maps Configuration for Uttarakhand Geospatial Canvas
 */
export const MAP_CONFIG = {
  defaultCenter: {
    lat: 30.3165,
    lng: 78.9500,
  },
  defaultZoom: 8,
  minZoom: 7,
  maxZoom: 18,
  mapTypeId: 'terrain', // Default to topographic terrain
  restriction: {
    latLngBounds: {
      north: 31.80,
      south: 28.30,
      west: 77.10,
      east: 81.60,
    },
    strictBounds: false,
  },
  styles: [
    {
      featureType: 'all',
      elementType: 'geometry',
      stylers: [{ color: '#1a202c' }]
    },
    {
      featureType: 'water',
      elementType: 'geometry',
      stylers: [{ color: '#0f172a' }]
    },
    {
      featureType: 'water',
      elementType: 'labels.text.fill',
      stylers: [{ color: '#38bdf8' }]
    },
    {
      featureType: 'road',
      elementType: 'geometry',
      stylers: [{ color: '#2d3748' }]
    },
    {
      featureType: 'road.highway',
      elementType: 'geometry',
      stylers: [{ color: '#4a5568' }]
    }
  ]
};

export const MAP_LAYERS = {
  STATE_BOUNDARY: 'state_boundary',
  GSI_LANDSLIDES: 'gsi_landslides',
  RISK_ZONES: 'risk_zones',
  INFRASTRUCTURE: 'infrastructure',
  RAINFALL: 'rainfall',
  USER_LOCATION: 'user_location',
};
