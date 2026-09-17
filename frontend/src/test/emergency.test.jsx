import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Emergency } from '../pages/Emergency/Emergency';
import * as infraApi from '../services/infrastructureApi';

vi.mock('../services/infrastructureApi', () => ({
  getNearbyInfrastructure: vi.fn(),
}));

const mockFacilities = [
  {
    id: 1,
    name: 'Chamoli District Hospital',
    type: 'HOSPITAL',
    latitude: 30.5500,
    longitude: 79.1000,
    description: 'Emergency trauma center',
  },
  {
    id: 2,
    name: 'Joshimath Community Shelter',
    type: 'SHELTER',
    latitude: 30.5600,
    longitude: 79.1100,
    description: 'Designated civil relief refuge',
  },
];

describe('Emergency & Evacuation (/emergency) Page Refactor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header and location card with non-technical text', async () => {
    infraApi.getNearbyInfrastructure.mockResolvedValueOnce([]);

    render(
      <MemoryRouter initialEntries={['/emergency']}>
        <Emergency />
      </MemoryRouter>
    );

    expect(screen.getByText('Emergency & Evacuation')).toBeInTheDocument();
    expect(screen.getByText('Find nearby emergency resources and plan your response when landslide risk is elevated.')).toBeInTheDocument();
    expect(screen.getByText('Your location')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('Find Nearby Resources')).toBeInTheDocument();
    });
    expect(screen.getAllByText('Use My Location').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Demo emergency resource data/i).length).toBeGreaterThan(0);
  });

  it('displays nearby resources and labels them clearly as demo data', async () => {
    infraApi.getNearbyInfrastructure.mockResolvedValueOnce(mockFacilities);

    render(
      <MemoryRouter initialEntries={['/emergency']}>
        <Emergency />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Chamoli District Hospital')).toBeInTheDocument();
      expect(screen.getByText('Joshimath Community Shelter')).toBeInTheDocument();
    });

    // Check synthetic / demo data badges
    expect(screen.getAllByText(/Demo data/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Emergency locations shown here are demo data for platform testing/i)).toBeInTheDocument();
  });

  it('allows planning an evacuation and labels it as a Reference Route with critical safety notice', async () => {
    infraApi.getNearbyInfrastructure.mockResolvedValueOnce(mockFacilities);

    render(
      <MemoryRouter initialEntries={['/emergency']}>
        <Emergency />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Chamoli District Hospital')).toBeInTheDocument();
    });

    // Click "Plan Evacuation" button for Chamoli Hospital
    const planButtons = screen.getAllByText('Plan Evacuation');
    fireEvent.click(planButtons[0]);

    // Check Reference Route title
    expect(screen.getByText('Reference Route')).toBeInTheDocument();

    // Verify it is NOT called "Safe Route" or "Safest Route"
    expect(screen.queryByText('Safe Route')).not.toBeInTheDocument();
    expect(screen.queryByText('Safest Route')).not.toBeInTheDocument();

    // Verify critical disclaimer
    expect(screen.getByText(/Route geometry does not account for landslide hazards unless hazard-aware analysis is explicitly available/i)).toBeInTheDocument();
  });

  it('renders risk-aware response guidance section', () => {
    infraApi.getNearbyInfrastructure.mockResolvedValueOnce([]);

    render(
      <MemoryRouter initialEntries={['/emergency']}>
        <Emergency />
      </MemoryRouter>
    );

    expect(screen.getByText('During elevated landslide risk')).toBeInTheDocument();
    expect(screen.getByText('Avoid unstable slopes and recently affected areas.')).toBeInTheDocument();
    expect(screen.getByText('Follow instructions from local authorities.')).toBeInTheDocument();
    expect(screen.getByText('Do not enter an active landslide area.')).toBeInTheDocument();
  });

  it('handles empty results and displays clear empty notice', async () => {
    infraApi.getNearbyInfrastructure.mockResolvedValueOnce([]);

    render(
      <MemoryRouter initialEntries={['/emergency']}>
        <Emergency />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No nearby resources were returned for this location.')).toBeInTheDocument();
    });
  });

  it('rejects unsupported locations outside operational area and clears stale results', async () => {
    infraApi.getNearbyInfrastructure.mockResolvedValueOnce(mockFacilities);

    render(
      <MemoryRouter initialEntries={['/emergency']}>
        <Emergency />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Chamoli District Hospital')).toBeInTheDocument();
    });

    // Change latitude to outside Uttarakhand
    const latInput = screen.getByPlaceholderText('e.g. 30.5295');
    fireEvent.change(latInput, { target: { value: '25.0000' } });

    expect(screen.getByText('Location outside supported area.')).toBeInTheDocument();
    // Stale resources must be cleared
    expect(screen.queryByText('Chamoli District Hospital')).not.toBeInTheDocument();
  });
});
