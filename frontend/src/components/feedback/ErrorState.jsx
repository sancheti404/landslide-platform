import React from 'react';
import { AlertOctagon, RotateCw } from 'lucide-react';
import { Button } from '../common/Button';

export function ErrorState({
  title = 'Service Query Failed',
  message = 'An unexpected error occurred while communicating with the platform API.',
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
        background: '#fef2f2',
        border: '1px solid #fecaca',
        borderRadius: 'var(--radius-md)',
      }}
    >
      <div
        style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          background: '#fee2e2',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#dc2626',
          marginBottom: '0.75rem',
        }}
      >
        <AlertOctagon size={22} />
      </div>
      <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#991b1b' }}>
        {title}
      </h4>
      <p style={{ fontSize: '0.85rem', color: '#b91c1c', marginTop: '0.35rem', maxWidth: '440px' }}>
        {message}
      </p>
      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          icon={<RotateCw size={14} />}
          style={{ marginTop: '1rem' }}
        >
          Retry Request
        </Button>
      )}
    </div>
  );
}
