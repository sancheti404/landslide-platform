/**
 * Uttarakhand Operational Geospatial Bounds
 * Validated against FastAPI and Spring Boot validator:
 * Lat: [28.50, 31.60] N
 * Lon: [77.40, 81.30] E
 */
export const UTTARAKHAND_ENVELOPE = {
  MIN_LAT: 28.50,
  MAX_LAT: 31.60,
  MIN_LON: 77.40,
  MAX_LON: 81.30,
};

/**
 * Recommended presets for testing and quick access
 */
export const PRESET_LOCATIONS = [
  {
    name: 'Kedarnath Valley',
    district: 'Rudraprayag',
    latitude: 30.7346,
    longitude: 79.0669,
    description: 'High-altitude glaciated valley with severe monsoon triggering vulnerability.',
  },
  {
    name: 'Joshimath Urban Slope',
    district: 'Chamoli',
    latitude: 30.5564,
    longitude: 79.5658,
    description: 'Active subsidence and slope distress sector along the Alaknanda corridor.',
  },
  {
    name: 'Badrinath Highway Sector',
    district: 'Chamoli',
    latitude: 30.529505,
    longitude: 79.085957,
    description: 'Steep slope section adjacent to NH-7 with documented historical slide records.',
  },
  {
    name: 'Nainital Lake Slopes',
    district: 'Nainital',
    latitude: 29.3919,
    longitude: 79.4542,
    description: 'Steep limestone slopes prone to rotational failures during heavy rain.',
  },
  {
    name: 'Uttarkashi Bhagirathi Valley',
    district: 'Uttarkashi',
    latitude: 30.7268,
    longitude: 78.4354,
    description: 'Complex metamorphic terrain with recurrent debris flow history.',
  }
];
