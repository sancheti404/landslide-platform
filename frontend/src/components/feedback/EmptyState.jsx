import React from 'react';
import { Inbox } from 'lucide-react';

export function EmptyState({
  title = 'No Records Found',
  message = 'There are no active items matching your current filters or query criteria.',
  action,
  icon = <Inbox size={28} />,
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
        color: 'var(--text-muted)',
      }}
    >
      <div
        style={{
          width: '50px',
          height: '50px',
          borderRadius: '50%',
          background: '#f1f5f9',
          border: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          marginBottom: '0.75rem',
        }}
      >
        {icon}
      </div>
      <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
        {title}
      </h4>
      <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginTop: '0.3rem', maxWidth: '380px' }}>
        {message}
      </p>
      {action && <div style={{ marginTop: '1rem' }}>{action}</div>}
    </div>
  );
}
