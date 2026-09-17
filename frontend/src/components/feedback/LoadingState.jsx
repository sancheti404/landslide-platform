import React from 'react';
import { LoadingSpinner } from '../common/LoadingSpinner';

export function LoadingState({ message = 'Loading geospatial telemetry...', description }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 1.5rem',
        textAlign: 'center',
      }}
    >
      <LoadingSpinner size="lg" label="" />
      <h4 style={{ fontSize: '1rem', fontWeight: 600, marginTop: '1rem', color: 'var(--text-primary)' }}>
        {message}
      </h4>
      {description && (
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.35rem', maxWidth: '420px' }}>
          {description}
        </p>
      )}
    </div>
  );
}
