import React from 'react';
import { RISK_LEVELS } from '../../constants/riskLevels';

export function MapLegend({ showLayers = true }) {
  return (
    <div className="map-legend">
      <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.4rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.25rem' }}>
        Geospatial Legend
      </div>

      <div style={{ fontWeight: 600, color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: '0.35rem' }}>
        OPERATIONAL RISK
      </div>
      {Object.values(RISK_LEVELS).map((lvl) => (
        <div key={lvl.key} className="legend-item">
          <span className="legend-swatch" style={{ backgroundColor: lvl.color }} />
          <span>{lvl.label} ({lvl.scoreRange[0].toFixed(2)}–{lvl.scoreRange[1].toFixed(2)})</span>
        </div>
      ))}

      {showLayers && (
        <>
          <div style={{ fontWeight: 600, color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: '0.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.35rem' }}>
            LAYERS & FEATURES
          </div>
          <div className="legend-item">
            <span className="legend-swatch" style={{ backgroundColor: '#e11d48', borderRadius: '50%' }} />
            <span>GSI Landslide Point (NLSM)</span>
          </div>
          <div className="legend-item">
            <span className="legend-swatch" style={{ backgroundColor: '#0284c7', border: '1px dashed #38bdf8' }} />
            <span>Operational Envelope (28.5–31.6°N)</span>
          </div>
          <div className="legend-item">
            <span className="legend-swatch" style={{ backgroundColor: '#10b981', borderRadius: '50%' }} />
            <span>Emergency Facility (Synthetic Demo)</span>
          </div>
        </>
      )}
    </div>
  );
}
