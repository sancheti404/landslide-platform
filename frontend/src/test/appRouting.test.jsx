import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '../app/Layout';
import { Home } from '../pages/Home/Home';
import { RiskMap } from '../pages/RiskMap/RiskMap';
import { RiskAssessment } from '../pages/RiskAssessment/RiskAssessment';
import { HistoricalLandslides } from '../pages/HistoricalLandslides/HistoricalLandslides';
import { Emergency } from '../pages/Emergency/Emergency';
import { HowItWorks } from '../pages/HowItWorks/HowItWorks';
import { ROUTES } from '../constants/routes';

function renderWithRouter(initialRoute = '/') {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* 6 Core Consolidated Routes */}
          <Route index element={<Home />} />
          <Route path={ROUTES.RISK_MAP} element={<RiskMap />} />
          <Route path={ROUTES.ASSESS} element={<RiskAssessment />} />
          <Route path={ROUTES.LANDSLIDES} element={<HistoricalLandslides />} />
          <Route path={ROUTES.EMERGENCY} element={<Emergency />} />
          <Route path={ROUTES.HOW_IT_WORKS} element={<HowItWorks />} />

          {/* Legacy Redirect Routes */}
          <Route path={ROUTES.RAINFALL} element={<Navigate to={ROUTES.ASSESS} replace />} />
          <Route path={ROUTES.SATELLITE} element={<Navigate to={ROUTES.HOW_IT_WORKS} replace />} />
          <Route path={ROUTES.TERRAIN} element={<Navigate to={ROUTES.HOW_IT_WORKS} replace />} />
          <Route path={ROUTES.RESOURCES} element={<Navigate to={ROUTES.EMERGENCY} replace />} />
          <Route path={ROUTES.EVACUATION} element={<Navigate to={ROUTES.EMERGENCY} replace />} />
          <Route path={ROUTES.SIMULATION} element={<Navigate to={ROUTES.EMERGENCY} replace />} />
          <Route path={ROUTES.ANALYTICS} element={<Navigate to={ROUTES.HOW_IT_WORKS} replace />} />
          <Route path={ROUTES.SYSTEM} element={<Navigate to={ROUTES.HOME} replace />} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

describe('Consolidated Navigation and Multi-Page Routing', () => {
  it('renders Home page at route "/" with header and operational highlights', () => {
    renderWithRouter('/');
    expect(screen.getAllByText(/Uttarakhand Landslide/i).length).toBeGreaterThan(0);
    expect(screen.getByText('Explore Landslide Risk Across Uttarakhand')).toBeInTheDocument();
    expect(screen.getByText('What would you like to do?')).toBeInTheDocument();
    expect(screen.getByText('Landslide Monitoring')).toBeInTheDocument();
    expect(screen.getByText('Rainfall Conditions')).toBeInTheDocument();
    expect(screen.getAllByText(/Live Risk Map/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Check a Location/i).length).toBeGreaterThan(0);
  });

  it('renders Live Risk Map page at "/risk-map" with 3-part GIS workspace and layer controls', () => {
    renderWithRouter('/risk-map');
    expect(screen.getAllByText('Live Risk Map').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Map Layers').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Location').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Use My Location').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Operational Area').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Historical Landslides').length).toBeGreaterThan(0);
  });

  it('renders Check a Location page at "/assess"', () => {
    renderWithRouter('/assess');
    expect(screen.getAllByText('Check a Location').length).toBeGreaterThan(0);
    expect(screen.getByText('Check Risk')).toBeInTheDocument();
  });

  it('renders Landslide History page at "/landslides"', () => {
    renderWithRouter('/landslides');
    expect(screen.getAllByText('Landslide History').length).toBeGreaterThan(0);
  });

  it('renders Emergency & Evacuation page at "/emergency"', () => {
    renderWithRouter('/emergency');
    expect(screen.getAllByText('Emergency & Evacuation').length).toBeGreaterThan(0);
  });

  it('renders How It Works page at "/how-it-works"', () => {
    renderWithRouter('/how-it-works');
    expect(screen.getAllByText('How It Works').length).toBeGreaterThan(0);
    expect(screen.getByText('What the System Looks At')).toBeInTheDocument();
    expect(screen.getByText('What this system cannot tell you')).toBeInTheDocument();
  });

  // Legacy Redirect Compatibility Tests
  it('redirects legacy "/rainfall" to "/assess"', () => {
    renderWithRouter('/rainfall');
    expect(screen.getAllByText('Check a Location').length).toBeGreaterThan(0);
  });

  it('redirects legacy "/resources" to "/emergency"', () => {
    renderWithRouter('/resources');
    expect(screen.getAllByText('Emergency & Evacuation').length).toBeGreaterThan(0);
  });

  it('redirects legacy "/evacuation" to "/emergency"', () => {
    renderWithRouter('/evacuation');
    expect(screen.getAllByText('Emergency & Evacuation').length).toBeGreaterThan(0);
  });

  it('redirects legacy "/analytics" to "/how-it-works"', () => {
    renderWithRouter('/analytics');
    expect(screen.getAllByText('How It Works').length).toBeGreaterThan(0);
  });

  it('redirects legacy "/satellite" to "/how-it-works"', () => {
    renderWithRouter('/satellite');
    expect(screen.getAllByText('How It Works').length).toBeGreaterThan(0);
  });

  it('redirects legacy "/system" to "/"', () => {
    renderWithRouter('/system');
    expect(screen.getAllByText(/Uttarakhand Landslide/i).length).toBeGreaterThan(0);
  });
});
