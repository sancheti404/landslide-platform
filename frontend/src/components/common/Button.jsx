import React from 'react';

export function Button({
  children,
  variant = 'primary', // primary, secondary, danger, outline, ghost
  size = 'md',        // sm, md, lg
  className = '',
  disabled = false,
  loading = false,
  icon = null,
  onClick,
  type = 'button',
  ...props
}) {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    borderRadius: 'var(--radius-sm)',
    fontWeight: 600,
    transition: 'all 0.15s ease',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    opacity: disabled || loading ? 0.6 : 1,
    fontFamily: 'inherit',
    border: 'none',
  };

  const sizes = {
    sm: { padding: '0.35rem 0.75rem', fontSize: '0.8rem' },
    md: { padding: '0.5rem 1rem', fontSize: '0.875rem' },
    lg: { padding: '0.65rem 1.35rem', fontSize: '0.95rem' },
  };

  const variants = {
    primary: {
      background: '#0f766e',
      color: '#ffffff',
      boxShadow: '0 1px 2px rgba(0, 0, 0, 0.08)',
      border: '1px solid #0d655e',
    },
    secondary: {
      background: '#ffffff',
      color: 'var(--text-secondary)',
      border: '1px solid var(--border-medium)',
      boxShadow: '0 1px 2px rgba(0, 0, 0, 0.04)',
    },
    outline: {
      background: 'transparent',
      color: '#0f766e',
      border: '1px solid #0f766e',
    },
    danger: {
      background: '#fef2f2',
      color: '#dc2626',
      border: '1px solid #fecaca',
    },
    ghost: {
      background: 'transparent',
      color: 'var(--text-secondary)',
      border: '1px solid transparent',
    }
  };

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      style={{
        ...baseStyles,
        ...sizes[size],
        ...variants[variant],
      }}
      className={`btn-component ${className}`}
      {...props}
    >
      {loading && (
        <span
          style={{
            width: '14px',
            height: '14px',
            border: '2px solid rgba(0,0,0,0.15)',
            borderTopColor: 'currentColor',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            display: 'inline-block',
          }}
        />
      )}
      {!loading && icon}
      {children}
    </button>
  );
}
