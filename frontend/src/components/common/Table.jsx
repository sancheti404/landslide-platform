import React from 'react';

export function Table({ headers = [], children, className = '' }) {
  return (
    <div style={{ overflowX: 'auto', width: '100%', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
      <table
        className={`custom-table ${className}`}
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '0.825rem',
          textAlign: 'left',
        }}
      >
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-medium)', background: '#f8fafc' }}>
            {headers.map((h, idx) => (
              <th
                key={idx}
                style={{
                  padding: '0.65rem 0.85rem',
                  color: 'var(--text-secondary)',
                  fontWeight: 700,
                  fontSize: '0.72rem',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {children}
        </tbody>
      </table>
    </div>
  );
}

export function TableRow({ children, onClick, style = {} }) {
  return (
    <tr
      onClick={onClick}
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'background-color 0.15s ease',
        ...style,
      }}
      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f8fafc')}
      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
    >
      {children}
    </tr>
  );
}

export function TableCell({ children, style = {}, className = '' }) {
  return (
    <td
      className={className}
      style={{
        padding: '0.65rem 0.85rem',
        color: 'var(--text-primary)',
        verticalAlign: 'middle',
        ...style,
      }}
    >
      {children}
    </td>
  );
}
