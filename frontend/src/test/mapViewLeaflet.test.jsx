import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MapView } from '../components/map/MapView';
import { GoogleMap } from '../components/map/GoogleMap';

describe('Leaflet + OpenStreetMap MapView Migration (Part 8)', () => {
  const mockLandslides = [
    {
      id: 101,
      latitude: 30.5500,
      longitude: 79.1000,
      district: 'Chamoli',
      movementType: 'Debris Slide',
      materialInvolved: 'Overburden / Soil',
    },
    {
      id: 102,
      latitude: 30.7300,
      longitude: 79.0600,
      district: 'Rudraprayag',
      movementType: 'Rock Fall',
      materialInvolved: 'Gneiss / Quartzite',
    },
  ];

  const mockResources = [
    {
      id: 201,
      name: 'Chamoli District Hospital',
      type: 'HOSPITAL',
      latitude: 30.5520,
      longitude: 79.1020,
    },
    {
      id: 202,
      name: 'Joshimath Community Shelter',
      type: 'SHELTER',
      latitude: 30.5580,
      longitude: 79.1080,
    },
  ];

  it('renders Leaflet map container and OpenStreetMap tile layer with attribution', () => {
    render(
      <MapView
        height="500px"
        selectedLocation={{ latitude: 30.5295, longitude: 79.0860, isInside: true }}
      />
    );

    // Leaflet container rendered
    const container = screen.getByTestId('leaflet-map-container');
    expect(container).toBeInTheDocument();

    // Tile layer with OpenStreetMap URL rendered
    const tileLayer = screen.getByTestId('leaflet-tile-layer');
    expect(tileLayer).toBeInTheDocument();
    expect(tileLayer.getAttribute('data-url')).toContain('openstreetmap.org');

    // Official OpenStreetMap attribution present
    expect(screen.getByText(/OpenStreetMap/i)).toBeInTheDocument();
    expect(screen.getByText(/contributors/i)).toBeInTheDocument();
  });

  it('works seamlessly through backward-compatible GoogleMap re-export without API key', () => {
    // Both MapView and GoogleMap are identical implementations
    expect(GoogleMap).toBe(MapView);

    render(
      <GoogleMap
        height="400px"
        selectedLocation={{ latitude: 30.5295, longitude: 79.0860, isInside: true }}
      />
    );

    expect(screen.getByTestId('leaflet-map-container')).toBeInTheDocument();
    expect(screen.getByText(/OpenStreetMap/i)).toBeInTheDocument();
  });

  it('captures map click coordinates and respects geographic validation', () => {
    const handleSelect = vi.fn();

    render(
      <MapView
        onLocationSelect={handleSelect}
      />
    );

    // Simulate click event inside Uttarakhand bounds
    window.dispatchEvent(
      new CustomEvent('test:map-click', {
        detail: { latlng: { lat: 30.529505, lng: 79.085957 } },
      })
    );

    expect(handleSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        latitude: 30.529505,
        longitude: 79.085957,
        isInside: true,
      })
    );

    // Simulate click outside Uttarakhand bounds
    window.dispatchEvent(
      new CustomEvent('test:map-click', {
        detail: { latlng: { lat: 25.000000, lng: 75.000000 } },
      })
    );

    expect(handleSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        latitude: 25,
        longitude: 75,
        isInside: false,
      })
    );
  });

  it('renders selected location marker and reveals popup on click', () => {
    render(
      <MapView
        selectedLocation={{ latitude: 30.5295, longitude: 79.0860, isInside: true }}
      />
    );

    // Selected location marker rendered
    const markers = screen.getAllByTestId('leaflet-marker');
    expect(markers.length).toBeGreaterThan(0);

    // Click marker to toggle popup open
    fireEvent.click(markers[0]);

    expect(screen.getByText('Selected Location')).toBeInTheDocument();
    expect(screen.getByText(/30.5295°N, 79.0860°E/i)).toBeInTheDocument();
    expect(screen.getByText('Inside UK-LIP operational area')).toBeInTheDocument();
  });

  it('renders authentic historical landslide markers and handles selection', () => {
    const handleLandslideClick = vi.fn();
    const handleLocationSelect = vi.fn();

    render(
      <MapView
        landslides={mockLandslides}
        activeLayers={{ landslides: true, operationalArea: true }}
        onLandslideClick={handleLandslideClick}
        onLocationSelect={handleLocationSelect}
      />
    );

    const markers = screen.getAllByTestId('leaflet-marker');
    // At least 2 landslide markers
    expect(markers.length).toBe(2);

    // Click first landslide marker
    fireEvent.click(markers[0]);

    expect(handleLandslideClick).toHaveBeenCalledWith(mockLandslides[0]);
    expect(handleLocationSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        latitude: 30.55,
        longitude: 79.1,
        isInside: true,
        landslide: mockLandslides[0],
      })
    );

    // Popup shows authentic GSI info
    expect(screen.getByText('Recorded Landslide')).toBeInTheDocument();
    expect(screen.getByText('Debris Slide')).toBeInTheDocument();
    expect(screen.getByText(/GSI NLSM Inventory Record/i)).toBeInTheDocument();
  });

  it('renders emergency resources markers and labels them as demo data', () => {
    const handleResourceClick = vi.fn();

    render(
      <MapView
        resources={mockResources}
        activeLayers={{ infrastructure: true }}
        onResourceClick={handleResourceClick}
      />
    );

    const markers = screen.getAllByTestId('leaflet-marker');
    expect(markers.length).toBe(2);

    // Click hospital marker
    fireEvent.click(markers[0]);
    expect(handleResourceClick).toHaveBeenCalledWith(mockResources[0]);

    expect(screen.getByText('Chamoli District Hospital')).toBeInTheDocument();
    expect(screen.getAllByText(/Demo emergency resource data/i).length).toBeGreaterThan(0);
  });

  it('renders destination marker for emergency route planning', () => {
    render(
      <MapView
        destinationLocation={{
          latitude: 30.5580,
          longitude: 79.1080,
          name: 'Joshimath Community Shelter',
        }}
      />
    );

    const markers = screen.getAllByTestId('leaflet-marker');
    expect(markers.length).toBe(1);

    // Click destination marker
    fireEvent.click(markers[0]);

    expect(screen.getByText('Destination Facility')).toBeInTheDocument();
    expect(screen.getByText('Joshimath Community Shelter')).toBeInTheDocument();
    expect(screen.getByText('Demo emergency resource data')).toBeInTheDocument();
  });

  it('controls layer visibility according to activeLayers prop', () => {
    const { rerender } = render(
      <MapView
        landslides={mockLandslides}
        resources={mockResources}
        activeLayers={{
          operationalArea: true,
          landslides: true,
          riskZones: true,
          infrastructure: true,
        }}
      />
    );

    // Operational area rectangle + 3 risk zones rectangles = 4 rectangles
    const rectangles = screen.getAllByTestId('leaflet-rectangle');
    expect(rectangles.length).toBe(4);

    // 2 landslides + 2 resources = 4 markers
    expect(screen.getAllByTestId('leaflet-marker').length).toBe(4);

    // Rerender with layers turned off
    rerender(
      <MapView
        landslides={mockLandslides}
        resources={mockResources}
        activeLayers={{
          operationalArea: false,
          landslides: false,
          riskZones: false,
          infrastructure: false,
        }}
      />
    );

    expect(screen.queryAllByTestId('leaflet-rectangle').length).toBe(0);
    expect(screen.queryAllByTestId('leaflet-marker').length).toBe(0);
  });

  it('provides explicit-action geolocation button without auto-requesting', () => {
    render(<MapView />);

    // Button is present in the DOM
    const locBtn = screen.getByRole('button', { name: /Use My Location/i });
    expect(locBtn).toBeInTheDocument();

    // Does NOT auto-trigger geolocation on render
    expect(screen.queryByText(/locating/i)).not.toBeInTheDocument();
  });
});
