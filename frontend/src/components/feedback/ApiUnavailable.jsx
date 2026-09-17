import React from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '../common/Button';

export function ApiUnavailable({
  serviceName = 'Spring Boot Gateway (:8080)',
  onRetry,
}) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2.5rem 1.5rem',
        textAlign: 'center',
        background: 'rgba(239, 68, 68, 0.08)',
        border: '1px solid rgba(239, 68, 68, 0.25)',
        borderRadius: 'var(--radius-md)',
      }}
    >
      <div
        style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          background: 'rgba(239, 68, 68, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#f87171',
          marginBottom: '0.75rem',
        }}
      >
        <WifiOff size={22} />
      </div>
      <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#f87171' }}>
        Backend Connection Offline
      </h4>
      <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '0.35rem', maxWidth: '380px' }}>
        Unable to communicate with {serviceName}. Ensure Spring Boot is actively running on port 8080.
      </p>
      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          icon={<RefreshCw size={13} />}
          style={{ marginTop: '1rem' }}
        >
          Check Connection Again
        </Button>
      )}
    </div>
  );
}

export function NoDataAvailable({
  title = 'No Telemetry Available',
  message = 'There is currently no real-time telemetry or historical record available for the requested parameter.',
}) {
  return (
    <div
      style={{
        padding: '1.5rem',
        textAlign: 'center',
        color: 'var(--text-muted)',
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: 'var(--radius-md)',
        border: '1px dashed var(--border-subtle)',
      }}
    >
      <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
        {title}
      </div>
      <div style={{ fontSize: '0.8rem', marginTop: '0.3rem' }}>
        {message}
      </div>
    </div>
  );
}
