import React from 'react';
import { MapPinOff } from 'lucide-react';
import { UTTARAKHAND_ENVELOPE } from '../../constants/geographicBounds';
import { Button } from '../common/Button';

export function UnsupportedLocation({
  latitude,
  longitude,
  onSelectPreset,
}) {
  return (
    <div
      role="alert"
      style={{
        padding: '1.25rem',
        borderRadius: 'var(--radius-md)',
        background: '#fef2f2',
        border: '1px solid #fecaca',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: '#fee2e2',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#dc2626',
            flexShrink: 0,
          }}
        >
          <MapPinOff size={18} />
        </div>
        <div>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#991b1b' }}>
            Unsupported Geographic Coordinate
          </h4>
          <p style={{ fontSize: '0.78rem', color: '#b91c1c' }}>
            Operational risk calculations are restricted strictly to the Uttarakhand state envelope.
          </p>
        </div>
      </div>

      <div
        style={{
          background: '#ffffff',
          border: '1px solid #fee2e2',
          padding: '0.75rem 1rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.35rem',
        }}
      >
        <div>
          <strong>Requested Coordinates:</strong>{' '}
          <span className="font-mono" style={{ color: '#dc2626', fontWeight: 600 }}>
            {latitude !== undefined ? Number(latitude).toFixed(6) : '—'},{' '}
            {longitude !== undefined ? Number(longitude).toFixed(6) : '—'}
          </span>
        </div>
        <div>
          <strong>Supported Envelope:</strong>{' '}
          <span className="font-mono" style={{ color: '#0f766e', fontWeight: 600 }}>
            Lat {UTTARAKHAND_ENVELOPE.MIN_LAT}–{UTTARAKHAND_ENVELOPE.MAX_LAT}°N, Lon{' '}
            {UTTARAKHAND_ENVELOPE.MIN_LON}–{UTTARAKHAND_ENVELOPE.MAX_LON}°E
          </span>
        </div>
        <div style={{ color: '#b91c1c', fontWeight: 600, marginTop: '0.2rem', fontSize: '0.75rem' }}>
          * Evaluation Blocked: No machine learning inference or dynamic rainfall stress scoring was executed.
        </div>
      </div>

      {onSelectPreset && (
        <div style={{ marginTop: '0.25rem' }}>
          <Button variant="secondary" size="sm" onClick={onSelectPreset}>
            Switch to Kedarnath Valley (Preset)
          </Button>
        </div>
      )}
    </div>
  );
}
