import React from 'react';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Alert } from '../../components/common/Alert';
import { Satellite as SatelliteIcon, Eye, Image as ImageIcon, CheckCircle } from 'lucide-react';

export function Satellite() {
  return (
    <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto', padding: '1.5rem 1.75rem', width: '100%' }}>
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Satellite Visual Intelligence
          </h1>
          <Badge variant="default">Sentinel-2 L2A · 10m</Badge>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Multispectral optical imagery intelligence and Swin Transformer deep vision representations from Sentinel-2 L2A.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <Card>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>CONSTELLATION</div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '0.35rem', color: '#0284c7' }}>
            Sentinel-2 L2A
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            European Space Agency (ESA) multispectral optical mission
          </div>
        </Card>

        <Card>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>SPECTRAL BANDS</div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '0.35rem', color: '#059669' }}>
            B4, B3, B2, B8
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Red, Green, Blue, and Near-Infrared (NIR)
          </div>
        </Card>

        <Card>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>VISION ARCHITECTURE</div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '0.35rem', color: '#0f766e' }}>
            Swin-T (Frozen)
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Hierarchical Vision Transformer with Shifted Windows &bull; Weight: 0.62
          </div>
        </Card>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <Card title="Swin Transformer Feature Extraction Pipeline">
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            The optical visual model inspects 224&times;224 multispectral terrain patches to detect vegetation disturbance, exposed scars, talus accumulations, and geotechnical scarp formations.
          </p>
          <ul style={{ paddingLeft: '1.25rem', fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
            <li><strong>Input Dimension:</strong> 4 channels (Red, Green, Blue, NIR) normalized to 224&times;224 pixels.</li>
            <li><strong>Model Weight in Fusion:</strong> Frozen weight w_swin = 0.62 in late fusion.</li>
            <li><strong>Pre-extracted Cache:</strong> 11,046 total patches (8,836 training, 2,210 held-out test).</li>
            <li><strong>Zero Test Sample Leakage:</strong> Held-out test samples are strictly excluded from runtime spatial feature lookups.</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
