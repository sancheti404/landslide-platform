import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ROUTES } from '../constants/routes';
import { Menu, ChevronRight } from 'lucide-react';

const ROUTE_LABELS = {
  [ROUTES.HOME]: 'Home',
  [ROUTES.RISK_MAP]: 'Live Risk Map',
  [ROUTES.ASSESS]: 'Check a Location',
  [ROUTES.LANDSLIDES]: 'Landslide History',
  [ROUTES.EMERGENCY]: 'Emergency & Evacuation',
  [ROUTES.HOW_IT_WORKS]: 'How It Works',
};

export function Navbar({ onToggleMobileSidebar }) {
  const location = useLocation();
  const currentTitle = ROUTE_LABELS[location.pathname] || 'Geospatial Intelligence';

  return (
    <header
      style={{
        height: 'var(--nav-height)',
        background: '#ffffff',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1.25rem',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Left: Mobile Toggle & Page Context */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        <button
          type="button"
          onClick={onToggleMobileSidebar}
          className="mobile-hamburger-btn"
          aria-label="Open navigation menu"
          style={{
            background: 'transparent',
            color: 'var(--text-secondary)',
            display: 'none',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0.35rem',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
          }}
        >
          <Menu size={20} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.85rem' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>UK-LIP</span>
          <ChevronRight size={14} style={{ color: 'var(--text-dim)' }} />
          <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{currentTitle}</span>
        </div>
      </div>

      {/* Right: Operational Status Indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <Link
          to={ROUTES.HOME}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.45rem',
            padding: '0.25rem 0.65rem',
            borderRadius: 'var(--radius-full)',
            background: '#ecfdf5',
            border: '1px solid #a7f3d0',
            color: '#059669',
            fontSize: '0.75rem',
            fontWeight: 600,
            textDecoration: 'none',
          }}
        >
          <span className="pulse-dot pulse-dot-green" />
          <span>GATEWAY ONLINE</span>
        </Link>
      </div>

      <style>{`
        @media (max-width: 1023px) {
          .mobile-hamburger-btn {
            display: flex !important;
          }
        }
      `}</style>
    </header>
  );
}
