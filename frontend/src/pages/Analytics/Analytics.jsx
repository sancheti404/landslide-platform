import React from 'react';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Alert } from '../../components/common/Alert';
import { BarChart3, CheckCircle, PieChart, ShieldCheck, Activity } from 'lucide-react';

export function Analytics() {
  const modelMetrics = [
    { name: 'XGBoost Terrain ROC-AUC', value: '0.864', description: 'Tuned gradient-boosted trees on 10 terrain geomorphometrics' },
    { name: 'Swin-T Optical Visual ROC-AUC', value: '0.942', description: 'Deep hierarchical vision transformer on Sentinel-2 L2A optical patches' },
    { name: 'Multimodal Fusion ROC-AUC', value: '0.958', description: 'Late fusion combining 0.38 XGBoost + 0.62 Swin Transformer' },
    { name: 'Frozen Test Samples Leakage', value: '0.00%', description: 'Held-out test set strictly isolated from all runtime lookups' },
  ];

  return (
    <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto', padding: '1.5rem 1.75rem', width: '100%' }}>
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            How It Works
          </h1>
          <Badge variant="default">Frozen Pipeline</Badge>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Frozen multimodal architecture evaluation, ablation benchmarks, and statistical validation metrics.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {modelMetrics.map((m) => (
          <Card key={m.name}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>{m.name}</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, marginTop: '0.35rem', color: '#0f766e' }}>
              {m.value}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              {m.description}
            </div>
          </Card>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Fusion Architecture Card */}
        <Card title="Frozen Multimodal Late Fusion Architecture">
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            The operational pipeline utilizes the optimal multimodal late-fusion formula, which is strictly <strong>frozen</strong> in production:
          </p>

          <div
            style={{
              background: '#f8fafc',
              padding: '1rem 1.25rem',
              borderRadius: 'var(--radius-sm)',
              fontFamily: 'ui-monospace, SFMono-Regular, monospace',
              fontSize: '0.875rem',
              color: '#0f766e',
              margin: '0.85rem 0',
              border: '1px solid var(--border-subtle)',
              lineHeight: 1.6,
              fontWeight: 600,
            }}
          >
            static_visual_fusion_score = 0.38 * P_xgboost + 0.62 * P_swin<br />
            operational_risk_score = min(1.0, static_visual_fusion_score * (1.0 + 0.50 * S_rain))
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginTop: '0.75rem' }}>
            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 700, color: '#0284c7', marginBottom: '0.3rem', fontSize: '0.85rem' }}>XGBoost Weight: 0.38</div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Provides robust long-term geological and topographic baseline susceptibility from SRTM GL1 30m DEM slope, aspect, and curvature.
              </p>
            </div>

            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 700, color: '#0f766e', marginBottom: '0.3rem', fontSize: '0.85rem' }}>Swin Transformer Weight: 0.62</div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Captures optical surface changes, scar morphology, vegetation clearing, and active scarp movements from Sentinel-2.
              </p>
            </div>
          </div>
        </Card>

        {/* Causal Trigger Statement */}
        <Card title="Hydrometeorological Causality Guarantee">
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            <strong>Temporal Integrity:</strong> Because the GSI landslide inventory does not provide reliable historical timestamps, Temporal Fusion Transformers (TFT) was explicitly not trained. Dynamic CHIRPS precipitation is mathematically formulated as an operational stress multiplier, guaranteeing that no past events are modeled with future weather data.
          </p>
        </Card>
      </div>
    </div>
  );
}
