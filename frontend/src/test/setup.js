import React from 'react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock react-leaflet for headless jsdom test environment using pure JS createElement
vi.mock('react-leaflet', () => {
  const MockMarker = ({ position, icon, children, eventHandlers }) => {
    const [isOpen, setIsOpen] = React.useState(false);
    return React.createElement(
      'div',
      {
        'data-testid': 'leaflet-marker',
        'data-position': JSON.stringify(position),
        onClick: (e) => {
          setIsOpen((prev) => !prev);
          if (eventHandlers?.click) eventHandlers.click(e);
        },
        className: 'leaflet-marker',
      },
      isOpen ? children : null
    );
  };

  return {
    MapContainer: ({ children, className, style, ...props }) =>
      React.createElement(
        'div',
        {
          'data-testid': 'leaflet-map-container',
          className: `leaflet-container ${className || ''}`,
          style,
          ...props,
        },
        children
      ),
    TileLayer: ({ attribution, url }) =>
      React.createElement(
        'div',
        {
          'data-testid': 'leaflet-tile-layer',
          'data-url': url,
          className: 'leaflet-tile-layer',
        },
        React.createElement('div', {
          className: 'leaflet-control-attribution',
          dangerouslySetInnerHTML: { __html: typeof attribution === 'string' ? attribution : '' },
        })
      ),
    Marker: MockMarker,
    Popup: ({ children }) =>
      React.createElement(
        'div',
        {
          'data-testid': 'leaflet-popup',
          className: 'leaflet-popup-content',
        },
        children
      ),
    Rectangle: ({ bounds, children, pathOptions }) =>
      React.createElement(
        'div',
        {
          'data-testid': 'leaflet-rectangle',
          'data-bounds': JSON.stringify(bounds),
          className: 'leaflet-rectangle',
        },
        children
      ),
    useMap: () => ({
      panTo: vi.fn(),
      setView: vi.fn(),
      zoomIn: vi.fn(),
      zoomOut: vi.fn(),
      setZoom: vi.fn(),
    }),
    useMapEvents: (handlers) => {
      React.useEffect(() => {
        const handleSimulatedClick = (e) => {
          if (handlers?.click && e.detail) {
            handlers.click(e.detail);
          }
        };
        window.addEventListener('test:map-click', handleSimulatedClick);
        return () => window.removeEventListener('test:map-click', handleSimulatedClick);
      }, [handlers]);
      return null;
    },
  };
});

// Provide default mock fetch for test environment
if (!globalThis.fetch || !globalThis.fetch._isMockFunction) {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = vi.fn().mockImplementation((url, options) => {
    return Promise.resolve({
      ok: true,
      status: 200,
      headers: { get: () => 'application/json' },
      json: async () => ({
        status: 'healthy',
        operational_landslide_risk_score: 0.5,
        risk_level: 'MODERATE',
        xgboost_probability: 0.5,
        swin_probability: 0.5,
        static_visual_fusion_score: 0.5,
        dynamic_rainfall_trigger_score: 0.5,
        trigger_indicator: 'NORMAL',
        rainfall_3d_mm: 10,
        rainfall_7d_mm: 20,
        rainfall_14d_mm: 30,
        rainfall_30d_mm: 40,
        layers: [],
      }),
      text: async () => JSON.stringify({ status: 'healthy' }),
    });
  });
}
