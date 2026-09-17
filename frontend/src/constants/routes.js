/**
 * Application Route Paths - Consolidated 6 Core Routes + Legacy Redirects
 */
export const ROUTES = {
  HOME: '/',
  RISK_MAP: '/risk-map',
  ASSESS: '/assess',
  LANDSLIDES: '/landslides',
  EMERGENCY: '/emergency',
  HOW_IT_WORKS: '/how-it-works',

  // Legacy route aliases (redirected to preserved targets)
  RAINFALL: '/rainfall',
  SATELLITE: '/satellite',
  TERRAIN: '/terrain',
  RESOURCES: '/resources',
  EVACUATION: '/evacuation',
  SIMULATION: '/simulation',
  ANALYTICS: '/analytics',
  SYSTEM: '/system',
};

export const NAVIGATION_GROUPS = [
  {
    title: 'OVERVIEW',
    items: [
      { label: 'Home', path: ROUTES.HOME, icon: 'Home' },
      { label: 'Live Risk Map', path: ROUTES.RISK_MAP, icon: 'Map' },
      { label: 'Check a Location', path: ROUTES.ASSESS, icon: 'Crosshair' },
    ]
  },
  {
    title: 'HISTORY',
    items: [
      { label: 'Landslide History', path: ROUTES.LANDSLIDES, icon: 'Database' },
    ]
  },
  {
    title: 'RESPONSE',
    items: [
      { label: 'Emergency & Evacuation', path: ROUTES.EMERGENCY, icon: 'Shield' },
    ]
  },
  {
    title: 'INFORMATION',
    items: [
      { label: 'How It Works', path: ROUTES.HOW_IT_WORKS, icon: 'HelpCircle' },
    ]
  }
];
