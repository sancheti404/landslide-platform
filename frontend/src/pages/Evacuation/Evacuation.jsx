import React from 'react';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Alert } from '../../components/common/Alert';
import { Route, ShieldAlert, CheckCircle2, Clock } from 'lucide-react';

export function Evacuation() {
  return (
    <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto', padding: '1.5rem 1.75rem', width: '100%' }}>
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Evacuation Corridor Planning
          </h1>
          <Badge variant="default">Civil Protection</Badge>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Strategic evacuation corridor determination routing civilian populations away from active landslide zones and cut-slope bottlenecks.
        </p>
      </div>

      <Alert variant="info" title="Functional Architecture Boundary">
        The Evacuation Planning module defines corridor calculation and routing specifications. Subsequent integration phases incorporate dynamic road network graph algorithms (e.g. pgRouting over Uttarakhand highway network) and agentic multi-route civil protection optimization.
      </Alert>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem', marginTop: '1.5rem' }}>
        <Card title="Evacuation Routing Pipeline Specification">
          <ul style={{ paddingLeft: '1.25rem', fontSize: '0.825rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            <li><strong>Risk-Avoidant Pathfinding:</strong> Penalize road segments intersecting high-susceptibility zones (Operational Risk &gt; 0.65).</li>
            <li><strong>Bottleneck Avoidance:</strong> Account for single-lane mountain passes and bridge pinch points along NH-7 and NH-107.</li>
            <li><strong>Shelter Capacity Matching:</strong> Route evacuees toward verified designated emergency relief shelters.</li>
            <li><strong>Multi-Hazard Dynamic Re-routing:</strong> Ingest real-time rainfall alerts to divert traffic before mass slope failures occur.</li>
          </ul>
        </Card>

        <Card title="Backend API Interface Specifications">
          <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <span className="font-mono" style={{ color: 'var(--brand-primary)', fontWeight: 700 }}>POST /api/evacuation/plan</span>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Computes optimal safe evacuation corridors between an incident coordinate and reachable relief facilities.
              </p>
            </div>

            <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <span className="font-mono" style={{ color: 'var(--brand-primary)', fontWeight: 700 }}>GET /api/evacuation/corridors</span>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Returns predefined civil protection primary and secondary evacuation corridors for major pilgrimage valleys.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
