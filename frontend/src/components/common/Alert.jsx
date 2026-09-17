import React from 'react';
import { Info, AlertTriangle, AlertCircle, CheckCircle2 } from 'lucide-react';

export function Alert({
  variant = 'info', // info, warning, danger, success
  title,
  children,
  action,
  className = '',
}) {
  const configs = {
    info: {
      bg: 'rgba(6, 182, 212, 0.12)',
      border: 'rgba(6, 182, 212, 0.35)',
      color: '#38bdf8',
      icon: <Info size={18} />,
    },
    warning: {
      bg: 'rgba(245, 158, 11, 0.12)',
      border: 'rgba(245, 158, 11, 0.35)',
      color: '#fbbf24',
      icon: <AlertTriangle size={18} />,
    },
    danger: {
      bg: 'rgba(239, 68, 68, 0.12)',
      border: 'rgba(239, 68, 68, 0.35)',
      color: '#f87171',
      icon: <AlertCircle size={18} />,
    },
    success: {
      bg: 'rgba(16, 185, 129, 0.12)',
      border: 'rgba(16, 185, 129, 0.35)',
      color: '#34d399',
      icon: <CheckCircle2 size={18} />,
    }
  };

  const cfg = configs[variant] || configs.info;

  return (
    <div
      role="alert"
      className={`alert-box ${className}`}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
        padding: '0.85rem 1rem',
        borderRadius: 'var(--radius-md)',
        background: cfg.bg,
        border: `1px solid ${cfg.border}`,
        color: 'var(--text-primary)',
        fontSize: '0.875rem',
      }}
    >
      <span style={{ color: cfg.color, marginTop: '2px', flexShrink: 0 }}>{cfg.icon}</span>
      <div style={{ flex: 1 }}>
        {title && <div style={{ fontWeight: 600, color: cfg.color, marginBottom: '0.2rem' }}>{title}</div>}
        <div style={{ color: 'var(--text-secondary)' }}>{children}</div>
      </div>
      {action && <div style={{ flexShrink: 0 }}>{action}</div>}
    </div>
  );
}
