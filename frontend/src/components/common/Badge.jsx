import React from 'react';

export function Badge({
  children,
  variant = 'default', // default, success, warning, danger, info
  size = 'sm',        // sm, md
  className = '',
  style = {},
  icon = null,
}) {
  const variants = {
    default: {
      background: '#f1f5f9',
      color: '#475569',
      border: '1px solid #cbd5e1',
    },
    success: {
      background: '#ecfdf5',
      color: '#059669',
      border: '1px solid #a7f3d0',
    },
    warning: {
      background: '#fffbeb',
      color: '#d97706',
      border: '1px solid #fde68a',
    },
    danger: {
      background: '#fef2f2',
      color: '#dc2626',
      border: '1px solid #fecaca',
    },
    info: {
      background: '#f0f9ff',
      color: '#0284c7',
      border: '1px solid #bae6fd',
    }
  };

  const sizes = {
    sm: { padding: '0.15rem 0.55rem', fontSize: '0.72rem' },
    md: { padding: '0.25rem 0.75rem', fontSize: '0.8rem' },
  };

  return (
    <span
      className={`badge ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        borderRadius: 'var(--radius-full)',
        fontWeight: 600,
        fontFamily: 'inherit',
        ...sizes[size],
        ...variants[variant],
        ...style,
      }}
    >
      {icon}
      {children}
    </span>
  );
}
