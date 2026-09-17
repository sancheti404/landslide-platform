import React from 'react';
import { Shield, Info } from 'lucide-react';

export function Footer() {
  return (
    <footer
      style={{
        marginTop: 'auto',
        borderTop: '1px solid var(--border-subtle)',
        background: '#ffffff',
        padding: '1.25rem 2rem',
        fontSize: '0.8rem',
        color: 'var(--text-muted)',
      }}
    >
      <div
        style={{
          maxWidth: 'var(--max-content-width)',
          margin: '0 auto',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Shield size={16} style={{ color: 'var(--brand-primary)' }} />
          <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
            Uttarakhand Landslide Intelligence Platform &copy; 2026
          </span>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.25rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          <span>GSI NLSM Inventory · 5,523 Records</span>
          <span>SRTM GL1 · 30m DEM</span>
          <span>CHIRPS Daily · 0.05°</span>
          <span>geoBoundaries ADM1</span>
        </div>
      </div>

      <div
        style={{
          maxWidth: 'var(--max-content-width)',
          margin: '0.65rem auto 0',
          paddingTop: '0.65rem',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: '0.72rem',
          color: 'var(--text-muted)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
        }}
      >
        <Info size={13} style={{ flexShrink: 0 }} />
        <span>
          Risk scores are decision-support heuristics and should not be interpreted as calibrated probabilities.
        </span>
      </div>
    </footer>
  );
}
