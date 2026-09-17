import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { RiskAssessment } from '../pages/RiskAssessment/RiskAssessment';
import * as riskApi from '../services/riskApi';

vi.mock('../services/riskApi', () => ({
  assessLandslideRisk: vi.fn(),
}));

const mockAssessmentData = {
  operational_landslide_risk_score: 0.92,
  risk_level: 'CRITICAL',
  xgboost_probability: 0.88,
  swin_probability: 0.94,
  static_visual_fusion_score: 0.91,
  dynamic_rainfall_trigger_score: 0.85,
  trigger_indicator: 'CRITICAL',
  rainfall_3d_mm: 45.2,
  rainfall_7d_mm: 112.4,
  rainfall_14d_mm: 180.0,
  rainfall_30d_mm: 240.5,
  intersecting_risk_zone_name: 'Alaknanda High Hazard Sector',
  intersecting_risk_zone_level: 'CRITICAL',
  nearby_hospitals_count: 2,
  nearby_shelters_count: 4,
  model_version: '1.0.0',
  status: 'success',
};

describe('Check a Location (/assess) Page Refactor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header and location input card with simple headings', () => {
    render(
      <MemoryRouter initialEntries={['/assess']}>
        <RiskAssessment />
      </MemoryRouter>
    );

    expect(screen.getByText('Check a Location')).toBeInTheDocument();
    expect(screen.getByText('See landslide risk and recent rainfall conditions for a specific location.')).toBeInTheDocument();
    expect(screen.getByText('Where would you like to check?')).toBeInTheDocument();
    expect(screen.getByText('Use My Location')).toBeInTheDocument();
    expect(screen.getByText('Check Risk')).toBeInTheDocument();
  });

  it('populates coordinates from URL search parameters', async () => {
    riskApi.assessLandslideRisk.mockResolvedValueOnce(mockAssessmentData);

    render(
      <MemoryRouter initialEntries={['/assess?lat=30.7346&lon=79.0669']}>
        <RiskAssessment />
      </MemoryRouter>
    );

    const latInput = screen.getByDisplayValue('30.7346');
    const lonInput = screen.getByDisplayValue('79.0669');
    expect(latInput).toBeInTheDocument();
    expect(lonInput).toBeInTheDocument();
  });

  it('displays semantic risk result after successful assessment', async () => {
    riskApi.assessLandslideRisk.mockResolvedValueOnce(mockAssessmentData);

    render(
      <MemoryRouter initialEntries={['/assess']}>
        <RiskAssessment />
      </MemoryRouter>
    );

    const checkBtn = screen.getByText('Check Risk');
    fireEvent.click(checkBtn);

    await waitFor(() => {
      expect(screen.getByText('LANDSLIDE RISK')).toBeInTheDocument();
      expect(screen.getByText('CRITICAL')).toBeInTheDocument();
      expect(screen.getByText('Very high operational risk')).toBeInTheDocument();
      expect(screen.getByText(/Operational Risk Score:/i)).toBeInTheDocument();
    });

    // Check contributing conditions
    expect(screen.getByText("What's contributing?")).toBeInTheDocument();
    expect(screen.getByText('Recent Rainfall')).toBeInTheDocument();
    expect(screen.getByText('Location Information')).toBeInTheDocument();
    expect(screen.getByText('Why this result?')).toBeInTheDocument();

    // Check technical details collapsed by default
    expect(screen.getByText('View technical details')).toBeInTheDocument();
    expect(screen.queryByText(/0.38 XGBoost \+ 0.62 Swin/i)).not.toBeInTheDocument();

    // Expand technical details
    fireEvent.click(screen.getByText('View technical details'));
    expect(screen.getByText(/0.38 XGBoost \+ 0.62 Swin/i)).toBeInTheDocument();
    expect(screen.getByText(/SRTM GL1 30m DEM/i)).toBeInTheDocument();
  });

  it('rejects unsupported out-of-envelope location and clears stale results', async () => {
    render(
      <MemoryRouter initialEntries={['/assess']}>
        <RiskAssessment />
      </MemoryRouter>
    );

    const latInput = screen.getByPlaceholderText('e.g. 30.5295');
    // Change to Delhi (28.6139, 77.2090) which is west of 77.40E
    fireEvent.change(latInput, { target: { value: '25.0000' } });

    expect(screen.getByText('Location outside supported area')).toBeInTheDocument();
    expect(screen.getByText('Please choose a location within the supported Uttarakhand area.')).toBeInTheDocument();

    // Check Risk button should be disabled
    const checkBtn = screen.getByText('Check Risk');
    expect(checkBtn).toBeDisabled();
    expect(riskApi.assessLandslideRisk).not.toHaveBeenCalled();
  });

  it('clears stale results when user edits coordinate inputs', async () => {
    riskApi.assessLandslideRisk.mockResolvedValueOnce(mockAssessmentData);

    render(
      <MemoryRouter initialEntries={['/assess']}>
        <RiskAssessment />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText('Check Risk'));

    await waitFor(() => {
      expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    });

    // Edit latitude
    const latInput = screen.getByPlaceholderText('e.g. 30.5295');
    fireEvent.change(latInput, { target: { value: '30.6000' } });

    // Result should be cleared
    expect(screen.queryByText('CRITICAL')).not.toBeInTheDocument();
    expect(screen.queryByText("What's contributing?")).not.toBeInTheDocument();
  });
});
