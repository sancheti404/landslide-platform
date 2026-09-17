import React from 'react';

export function LoadingSpinner({ size = 'md', label = 'Loading intelligence...', className = '' }) {
  const sizes = {
    sm: 18,
    md: 32,
    lg: 48,
  };

  const px = sizes[size] || 32;

  return (
    <div
      className={`loading-spinner-container ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.75rem',
        padding: '1.5rem',
      }}
    >
      <div
        style={{
          width: `${px}px`,
          height: `${px}px`,
          border: '3px solid rgba(56, 189, 248, 0.2)',
          borderTopColor: 'var(--brand-cyan)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      {label && (
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          {label}
        </span>
      )}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
