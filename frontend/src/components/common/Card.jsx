import React from 'react';

export function Card({
  title,
  subtitle,
  action,
  children,
  className = '',
  footer,
  style = {},
  ...props
}) {
  return (
    <div
      className={`glass-panel ${className}`}
      style={{
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        background: '#ffffff',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-sm)',
        ...style,
      }}
      {...props}
    >
      {(title || subtitle || action) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem' }}>
          <div>
            {title && (
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
                {title}
              </h3>
            )}
            {subtitle && (
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                {subtitle}
              </p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div style={{ flex: 1 }}>{children}</div>
      {footer && (
        <div style={{ paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          {footer}
        </div>
      )}
    </div>
  );
}
