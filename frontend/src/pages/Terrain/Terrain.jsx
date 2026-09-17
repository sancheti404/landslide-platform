import React from 'react';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Mountain, Layers, Compass, BarChart } from 'lucide-react';

export function Terrain() {
  const terrainFeatures = [
    { name: 'Elevation (DEM)', desc: 'Absolute topographic height in meters above sea level derived from SRTM GL1 30m DEM.' },
    { name: 'Slope Gradient', desc: 'Steepness of terrain in degrees; primary mechanical driver of gravitational shear stress.' },
    { name: 'Slope Aspect', desc: 'Compass orientation of slope face governing solar insolation, weathering, and moisture retention.' },
    { name: 'Plan Curvature', desc: 'Horizontal surface curvature indicating converging or diverging overland water runoff.' },
    { name: 'Profile Curvature', desc: 'Vertical slope curvature governing acceleration and deceleration of downslope mass movement.' },
    { name: 'Topographic Wetness Index (TWI)', desc: 'Hydrological equilibrium index quantifying steady-state soil moisture accumulation.' },
  ];

  return (
    <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto', padding: '1.5rem 1.75rem', width: '100%' }}>
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Terrain & Susceptibility Intelligence
          </h1>
          <Badge variant="default">SRTM GL1 30m DEM</Badge>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          SRTM GL1 30m Digital Elevation Model geomorphometrics and frozen XGBoost tabular susceptibility modeling.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <Card>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>DEM RASTER SOURCE</div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '0.35rem', color: '#0284c7' }}>
            SRTM GL1 30m DEM
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            NASA/USGS 1-arcsecond global elevation model (WGS84)
          </div>
        </Card>

        <Card>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>SUSCEPTIBILITY ENGINE</div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '0.35rem', color: '#0f766e' }}>
            XGBoost (Frozen)
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Tuned Gradient Boosted Trees &bull; Weight: 0.38
          </div>
        </Card>

        <Card>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>SPATIAL LOOKUP</div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '0.35rem', color: '#059669' }}>
            KDTree (&lt; 16.6 km)
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Strict distance threshold preventing arbitrary distant queries
          </div>
        </Card>
      </div>

      {/* Geomorphometric Feature Table */}
      <Card title="Geomorphometric Terrain Feature Pipeline">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.85rem', marginTop: '0.5rem' }}>
          {terrainFeatures.map((feat) => (
            <div
              key={feat.name}
              style={{
                background: '#f8fafc',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.85rem 1rem',
              }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                {feat.name}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.3rem', lineHeight: 1.4 }}>
                {feat.desc}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
