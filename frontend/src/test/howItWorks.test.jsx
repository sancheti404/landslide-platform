import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { HowItWorks } from '../pages/HowItWorks/HowItWorks';

describe('How It Works (/how-it-works) Educational Page Refactor', () => {
  it('renders page header with clear educational title and subtitle', () => {
    render(
      <MemoryRouter>
        <HowItWorks />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { level: 1, name: 'How It Works' })).toBeInTheDocument();
    expect(
      screen.getByText(
        'UK-LIP combines terrain, satellite imagery, and recent rainfall conditions to provide landslide risk information.'
      )
    ).toBeInTheDocument();
  });

  it('renders simple overview visual flow with plain-language labels', () => {
    render(
      <MemoryRouter>
        <HowItWorks />
      </MemoryRouter>
    );

    expect(screen.getByText('Terrain')).toBeInTheDocument();
    expect(screen.getByText('Satellite Imagery')).toBeInTheDocument();
    expect(screen.getByText('Rainfall Conditions')).toBeInTheDocument();
    expect(screen.getAllByText('Combined Risk').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Location Information')).toBeInTheDocument();
  });

  it('renders the three primary input factors with accurate educational descriptions', () => {
    render(
      <MemoryRouter>
        <HowItWorks />
      </MemoryRouter>
    );

    expect(screen.getByText('What the System Looks At')).toBeInTheDocument();
    expect(screen.getByText('TERRAIN')).toBeInTheDocument();
    expect(screen.getByText('SATELLITE IMAGERY')).toBeInTheDocument();
    expect(screen.getByText('RAINFALL CONDITIONS')).toBeInTheDocument();

    // Check descriptions
    expect(
      screen.getByText(/slope and elevation are used to identify areas with terrain conditions associated with landslides/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/recent satellite imagery is analyzed for visual patterns/i)
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/operational trigger\/stress signal/i).length
    ).toBeGreaterThanOrEqual(1);
  });

  it('renders Combined Risk explanation and prominent heuristic disclaimer', () => {
    render(
      <MemoryRouter>
        <HowItWorks />
      </MemoryRouter>
    );

    expect(
      screen.getByText(
        'Terrain and satellite-based signals are combined, then recent rainfall conditions can increase the operational risk level.'
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /Risk scores are decision-support heuristics and should not be interpreted as calibrated probabilities/i
      )
    ).toBeInTheDocument();
  });

  it('renders user-facing risk categories without implying certainty', () => {
    render(
      <MemoryRouter>
        <HowItWorks />
      </MemoryRouter>
    );

    expect(screen.getByText('LOW')).toBeInTheDocument();
    expect(screen.getByText('Lower operational risk under the assessed conditions.')).toBeInTheDocument();

    expect(screen.getByText('MODERATE')).toBeInTheDocument();
    expect(screen.getByText('Moderate operational risk under the assessed conditions.')).toBeInTheDocument();

    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('High operational risk under the assessed conditions.')).toBeInTheDocument();

    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('Very high operational risk under the assessed conditions.')).toBeInTheDocument();
  });

  it('renders data sources with accurate project names', () => {
    render(
      <MemoryRouter>
        <HowItWorks />
      </MemoryRouter>
    );

    expect(screen.getByText('GSI NLSM Landslide Inventory')).toBeInTheDocument();
    expect(screen.getByText(/5,523 historical records used by the project/i)).toBeInTheDocument();

    expect(screen.getByText('SRTM GL1 30m DEM')).toBeInTheDocument();
    expect(screen.queryByText(/Copernicus/i)).not.toBeInTheDocument();

    expect(screen.getByText('Sentinel-2 satellite imagery')).toBeInTheDocument();
    expect(screen.getByText('CHIRPS Daily rainfall data')).toBeInTheDocument();
  });

  it('renders the limitations section ("What this system cannot tell you")', () => {
    render(
      <MemoryRouter>
        <HowItWorks />
      </MemoryRouter>
    );

    expect(screen.getByText('What this system cannot tell you')).toBeInTheDocument();
    expect(
      screen.getByText('A risk score is not a guarantee that a landslide will or will not occur.')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Satellite imagery may not represent the exact current ground condition.')
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Rainfall conditions are an operational trigger\/stress signal, not a standalone landslide prediction./i).length
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText('Results are limited to the supported Uttarakhand operating area and available training-data coverage.')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Reference map routes do not automatically account for landslide hazards.')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Emergency resources shown in the platform may be synthetic demo data.')
    ).toBeInTheDocument();
  });

  it('keeps technical details collapsed by default, and reveals models and weights on toggle', () => {
    render(
      <MemoryRouter>
        <HowItWorks />
      </MemoryRouter>
    );

    // Collapsed by default: formulas and internal details are not rendered
    expect(screen.queryByText(/static_visual_fusion_score = 0.38/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Swin Transformer/i)).not.toBeInTheDocument();

    // Click toggle button
    const toggleButton = screen.getByRole('button', { name: /technical details/i });
    expect(toggleButton).toBeInTheDocument();
    fireEvent.click(toggleButton);

    // Now technical details are revealed
    expect(screen.getByText(/0.38 \* P_xgboost \+ 0.62 \* P_swin/i)).toBeInTheDocument();
    expect(screen.getByText(/Terrain Model: XGBoost/i)).toBeInTheDocument();
    expect(screen.getByText(/0.9481/i)).toBeInTheDocument();
    expect(screen.getByText(/Satellite Model: Swin Transformer/i)).toBeInTheDocument();
    expect(screen.getByText(/0.9666/i)).toBeInTheDocument();
    expect(screen.getByText(/Weighted Late Fusion/i)).toBeInTheDocument();
    expect(screen.getByText(/0.9707/i)).toBeInTheDocument();
    expect(screen.getByText(/128×128 Sentinel-2 optical patches resized to 224×224/i)).toBeInTheDocument();
    expect(screen.getByText(/Rainfall Trigger: CHIRPS Daily/i)).toBeInTheDocument();

    // Verify superseded metrics and leakage claims are NOT present
    expect(screen.queryByText(/0\.00% leakage/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/0\.864/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/0\.942/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/0\.958/i)).not.toBeInTheDocument();

    // Collapse again
    fireEvent.click(toggleButton);
    expect(screen.queryByText(/static_visual_fusion_score = 0.38/i)).not.toBeInTheDocument();
  });
});
