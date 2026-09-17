import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ROUTES } from '../constants/routes';
import { Layout } from './Layout';

// Consolidated 6 Core Pages
import { Home } from '../pages/Home/Home';
import { RiskMap } from '../pages/RiskMap/RiskMap';
import { RiskAssessment } from '../pages/RiskAssessment/RiskAssessment';
import { HistoricalLandslides } from '../pages/HistoricalLandslides/HistoricalLandslides';
import { Emergency } from '../pages/Emergency/Emergency';
import { HowItWorks } from '../pages/HowItWorks/HowItWorks';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* 6 Consolidated Core Routes */}
          <Route index element={<Home />} />
          <Route path={ROUTES.RISK_MAP} element={<RiskMap />} />
          <Route path={ROUTES.ASSESS} element={<RiskAssessment />} />
          <Route path={ROUTES.LANDSLIDES} element={<HistoricalLandslides />} />
          <Route path={ROUTES.EMERGENCY} element={<Emergency />} />
          <Route path={ROUTES.HOW_IT_WORKS} element={<HowItWorks />} />

          {/* Legacy Routes Redirected to Consolidated Routes */}
          <Route path={ROUTES.RAINFALL} element={<Navigate to={ROUTES.ASSESS} replace />} />
          <Route path={ROUTES.SATELLITE} element={<Navigate to={ROUTES.HOW_IT_WORKS} replace />} />
          <Route path={ROUTES.TERRAIN} element={<Navigate to={ROUTES.HOW_IT_WORKS} replace />} />
          <Route path={ROUTES.RESOURCES} element={<Navigate to={ROUTES.EMERGENCY} replace />} />
          <Route path={ROUTES.EVACUATION} element={<Navigate to={ROUTES.EMERGENCY} replace />} />
          <Route path={ROUTES.SIMULATION} element={<Navigate to={ROUTES.EMERGENCY} replace />} />
          <Route path={ROUTES.ANALYTICS} element={<Navigate to={ROUTES.HOW_IT_WORKS} replace />} />
          <Route path={ROUTES.SYSTEM} element={<Navigate to={ROUTES.HOME} replace />} />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
