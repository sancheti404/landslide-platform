import React from 'react';
import { Plus, Minus, RotateCcw, Crosshair } from 'lucide-react';

export function MapControls({ onZoomIn, onZoomOut, onResetView, onCenterLocation, hasLocation }) {
  return (
    <div className="map-controls-overlay">
      <button
        type="button"
        className="map-control-btn"
        onClick={onZoomIn}
        title="Zoom In"
        aria-label="Zoom In"
      >
        <Plus size={18} />
      </button>
      <button
        type="button"
        className="map-control-btn"
        onClick={onZoomOut}
        title="Zoom Out"
        aria-label="Zoom Out"
      >
        <Minus size={18} />
      </button>
      <button
        type="button"
        className="map-control-btn"
        onClick={onResetView}
        title="Reset Uttarakhand View"
        aria-label="Reset View"
      >
        <RotateCcw size={16} />
      </button>
      {hasLocation && (
        <button
          type="button"
          className="map-control-btn"
          onClick={onCenterLocation}
          title="Center on My Location"
          aria-label="Center on My Location"
          style={{ color: 'var(--brand-cyan)' }}
        >
          <Crosshair size={16} />
        </button>
      )}
    </div>
  );
}
