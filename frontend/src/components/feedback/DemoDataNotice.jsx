import React from 'react';
import { AlertCircle } from 'lucide-react';

/**
 * Notice required whenever synthetic development GIS data (e.g. sample risk zones, sample infrastructure) is shown.
 */
export function DemoDataNotice({
  entity = 'Infrastructure and local risk zones',
  className = '',
}) {
  return (
    <div
      role="note"
      className={`demo-data-notice ${className}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.6rem',
        padding: '0.55rem 0.85rem',
        borderRadius: 'var(--radius-sm)',
        background: '#fffbeb',
        border: '1px solid #fde68a',
        fontSize: '0.78rem',
        color: '#92400e',
        lineHeight: 1.4,
      }}
    >
      <AlertCircle size={16} style={{ color: '#d97706', flexShrink: 0 }} />
      <div>
        <strong>DEMO DATA:</strong> {entity} shown in this environment contains synthetic development records and does not represent real emergency facilities or government-declared evacuation points.
      </div>
    </div>
  );
}
