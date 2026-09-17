import React, { useState, useEffect } from 'react';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Alert } from '../../components/common/Alert';
import { getRainfallGridSummary } from '../../services/rainfallApi';
import { CloudRain, Droplets, Info, Compass } from 'lucide-react';

export function Rainfall() {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    getRainfallGridSummary().then(setSummary);
  }, []);

  return (
    <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto', padding: '1.5rem 1.75rem', width: '100%' }}>
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Dynamic Rainfall Intelligence
          </h1>
          <Badge variant="default">CHIRPS Daily · 0.05°</Badge>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Daily and antecedent hydrometeorological stress modeling powered by gridded UCSB CHIRPS daily precipitation.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <Card>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>PRECIPITATION SOURCE</div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '0.35rem', color: '#0284c7' }}>
            CHIRPS v2.0
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Climate Hazards Group InfraRed Precipitation with Station data
          </div>
        </Card>

        <Card>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>GRID RESOLUTION</div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '0.35rem', color: '#0f766e' }}>
            0.05° (~5.5 km)
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Interpolated daily precipitation grid across Uttarakhand
          </div>
        </Card>

        <Card>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>TRIGGER STATUS</div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '0.35rem', color: '#059669' }}>
            Active Causal Engine
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Operational triggering stress, not supervised historical target
          </div>
        </Card>
      </div>

      {/* Methodology Description */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <Card title="Causal Dynamic Rainfall Formulation">
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Because the historical landslide inventory lacks precise event timestamps, rainfall is modeled as an
            <strong> operational physical stress trigger</strong> rather than a supervised predictive feature.
            This ensures mathematical causality and prevents temporal target leakage.
          </p>

          <div
            style={{
              background: '#f8fafc',
              padding: '1rem 1.25rem',
              borderRadius: 'var(--radius-sm)',
              fontFamily: 'ui-monospace, SFMono-Regular, monospace',
              fontSize: '0.875rem',
              color: '#0284c7',
              margin: '0.85rem 0',
              border: '1px solid var(--border-subtle)',
              fontWeight: 600,
            }}
          >
            R_op = min(1.0, P_static_visual * (1.0 + 0.50 * S_rain))
          </div>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Where <span className="font-mono">P_static_visual = 0.38 * P_xgb + 0.62 * P_swin</span>, and
            <span className="font-mono"> S_rain</span> is the antecedent stress indicator computed from 3-day, 7-day, 14-day,
            and 30-day precipitation accumulations benchmarked against local historical anomaly distributions.
          </p>
        </Card>

        <Alert variant="info" title="Operational Hydrological Coverage">
          Rainfall data is accessed on-demand during coordinate risk evaluation. Gridded daily aggregates across all 13 districts in Uttarakhand are cached in Parquet format in the backend data lake.
        </Alert>
      </div>
    </div>
  );
}
