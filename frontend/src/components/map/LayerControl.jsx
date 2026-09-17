import React from 'react';
import { Layers, Eye, EyeOff } from 'lucide-react';

export function LayerControl({ activeLayers, onToggleLayer, className = '' }) {
  const layers = [
    { id: 'boundary', label: 'Uttarakhand State Boundary', source: 'geoBoundaries gbOpen' },
    { id: 'landslides', label: 'GSI Landslide Inventory', source: '5,523 Historical Points' },
    { id: 'riskZones', label: 'Local Risk Zones', source: 'Reference Zones' },
    { id: 'infrastructure', label: 'Emergency Facilities', source: 'Demo Data' },
  ];

  return (
    <div className={`map-layer-control ${className}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 600, fontSize: '0.85rem' }}>
        <Layers size={16} style={{ color: 'var(--brand-cyan)' }} />
        <span>Map Layers</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        {layers.map((layer) => {
          const isActive = activeLayers[layer.id];
          return (
            <button
              key={layer.id}
              type="button"
              onClick={() => onToggleLayer(layer.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.35rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                background: isActive ? 'rgba(56, 189, 248, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                border: `1px solid ${isActive ? 'rgba(56, 189, 248, 0.35)' : 'transparent'}`,
                color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                fontSize: '0.75rem',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div>
                <div style={{ fontWeight: 600 }}>{layer.label}</div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>{layer.source}</div>
              </div>
              {isActive ? (
                <Eye size={14} style={{ color: 'var(--brand-cyan)' }} />
              ) : (
                <EyeOff size={14} style={{ opacity: 0.5 }} />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
