import React from 'react';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Alert } from '../../components/common/Alert';
import { Activity, Clock, Play, AlertTriangle } from 'lucide-react';

export function Simulation() {
  return (
    <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto', padding: '1.5rem 1.75rem', width: '100%' }}>
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Evacuation Simulation Engine
          </h1>
          <Badge variant="warning">Simulation Specification</Badge>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Temporal evacuation simulation specifications modeling vehicular congestion, debris blockages, and clearance times.
        </p>
      </div>

      <Alert variant="warning" title="Functional Specification Boundary">
        Per the civil defense roadmap, Evacuation Simulation executes following the GIS and corridor routing engine. No simulated traffic is currently running in this environment.
      </Alert>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem', marginTop: '1.5rem' }}>
        <Card title="Simulation Engine Parameters (Roadmap)">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>1. Dynamic Blockage Injection:</strong>
              <p style={{ fontSize: '0.78rem', marginTop: '0.1rem', color: 'var(--text-muted)' }}>Simulates sudden debris deposition blocking key highway links, triggering real-time vehicle re-routing.</p>
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>2. Pilgrim & Local Traffic Flow:</strong>
              <p style={{ fontSize: '0.78rem', marginTop: '0.1rem', color: 'var(--text-muted)' }}>Models variable tourist vehicle densities during peak monsoon pilgrimage seasons (Char Dham yatra).</p>
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>3. Clearance Time Estimation:</strong>
              <p style={{ fontSize: '0.78rem', marginTop: '0.1rem', color: 'var(--text-muted)' }}>Computes expected hours to evacuate vulnerable valley segments to secure base camps.</p>
            </div>
          </div>
        </Card>

        <Card title="Future Integration Contract">
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Future simulation runs will be triggered through the Spring Boot orchestrator via:
          </p>
          <div
            style={{
              background: '#f8fafc',
              padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              fontFamily: 'ui-monospace, SFMono-Regular, monospace',
              fontSize: '0.8rem',
              color: 'var(--brand-primary)',
              margin: '0.75rem 0',
              border: '1px solid var(--border-subtle)',
              fontWeight: 600,
            }}
          >
            POST /api/simulation/run<br/>
            GET /api/simulation/:id/telemetry
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Simulation outputs will stream telemetry updates directly to the frontend via Server-Sent Events (SSE) or WebSockets.
          </p>
        </Card>
      </div>
    </div>
  );
}
