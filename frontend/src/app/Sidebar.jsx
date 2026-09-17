import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { NAVIGATION_GROUPS, ROUTES } from '../constants/routes';
import {
  Home,
  Map,
  Crosshair,
  Database,
  Shield,
  HelpCircle,
  X,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const ICON_MAP = {
  Home,
  Map,
  Crosshair,
  Database,
  Shield,
  HelpCircle,
};

export function Sidebar({
  isOpen,
  onClose,
  isCollapsed = false,
  onToggleCollapse,
}) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="mobile-backdrop"
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.4)',
            backdropFilter: 'blur(2px)',
            zIndex: 110,
          }}
        />
      )}

      {/* Sidebar Element */}
      <aside
        className={`app-sidebar ${isCollapsed ? 'collapsed' : ''} ${isOpen ? 'mobile-open' : ''}`}
        style={{
          width: isCollapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)',
          background: '#ffffff',
          borderRight: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          position: 'sticky',
          top: 0,
          zIndex: 120,
          transition: 'width 0.2s ease, transform 0.25s ease',
          flexShrink: 0,
        }}
      >
        {/* Brand Header */}
        <div
          style={{
            height: 'var(--nav-height)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: isCollapsed ? 'center' : 'space-between',
            padding: isCollapsed ? '0' : '0 1rem',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <Link
            to={ROUTES.HOME}
            onClick={onClose}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.65rem',
              textDecoration: 'none',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-sm)',
                background: 'linear-gradient(135deg, #0f766e 0%, #0284c7 100%)',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: '0.85rem',
                letterSpacing: '-0.02em',
                flexShrink: 0,
              }}
            >
              UK
            </div>
            {!isCollapsed && (
              <div>
                <div
                  style={{
                    fontSize: '0.9rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    lineHeight: 1.2,
                    letterSpacing: '-0.01em',
                  }}
                >
                  UK-LIP
                </div>
                <div
                  style={{
                    fontSize: '0.68rem',
                    color: 'var(--text-muted)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Geospatial Intelligence
                </div>
              </div>
            )}
          </Link>

          {/* Close button for mobile drawer */}
          <button
            type="button"
            onClick={onClose}
            className="mobile-close-btn"
            aria-label="Close navigation sidebar"
            style={{
              background: 'transparent',
              color: 'var(--text-muted)',
              display: 'none',
              padding: '0.25rem',
              cursor: 'pointer',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation Content */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            overflowX: 'hidden',
            padding: isCollapsed ? '0.75rem 0.4rem' : '0.75rem 0.65rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          {NAVIGATION_GROUPS.map((group, idx) => (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              {!isCollapsed && (
                <div
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    color: 'var(--text-dim)',
                    letterSpacing: '0.06em',
                    padding: '0.2rem 0.65rem',
                  }}
                >
                  {group.title}
                </div>
              )}
              {isCollapsed && idx > 0 && (
                <div
                  style={{
                    height: '1px',
                    background: 'var(--border-subtle)',
                    margin: '0.4rem 0.25rem',
                  }}
                />
              )}

              {group.items.map((item) => {
                const Icon = ICON_MAP[item.icon] || Map;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={onClose}
                    title={isCollapsed ? item.label : undefined}
                    style={({ isActive }) => ({
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: isCollapsed ? 'center' : 'flex-start',
                      gap: '0.65rem',
                      padding: isCollapsed ? '0.55rem' : '0.45rem 0.65rem',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.825rem',
                      fontWeight: isActive ? 600 : 500,
                      textDecoration: 'none',
                      color: isActive ? '#0f766e' : 'var(--text-secondary)',
                      backgroundColor: isActive ? '#f0fdf4' : 'transparent',
                      border: `1px solid ${isActive ? '#bbf7d0' : 'transparent'}`,
                      transition: 'all 0.15s ease',
                    })}
                  >
                    <Icon size={16} style={{ flexShrink: 0 }} />
                    {!isCollapsed && <span>{item.label}</span>}
                  </NavLink>
                );
              })}
            </div>
          ))}
        </div>

        {/* Desktop Collapse / Expand Toggle Button */}
        {onToggleCollapse && (
          <div
            className="collapse-toggle-bar"
            style={{
              padding: '0.4rem',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: isCollapsed ? 'center' : 'flex-end',
            }}
          >
            <button
              type="button"
              onClick={onToggleCollapse}
              title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              style={{
                background: 'transparent',
                color: 'var(--text-muted)',
                padding: '0.35rem',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                alignItems: 'center',
                cursor: 'pointer',
              }}
            >
              {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>
          </div>
        )}

        {/* Status Indicator at Bottom */}
        <div
          style={{
            padding: isCollapsed ? '0.6rem 0.2rem' : '0.75rem 0.85rem',
            borderTop: '1px solid var(--border-subtle)',
            background: '#fafafa',
            fontSize: '0.72rem',
          }}
        >
          {isCollapsed ? (
            <div style={{ display: 'flex', justifyContent: 'center' }} title="Systems Operational">
              <span className="pulse-dot pulse-dot-green" />
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                <span className="pulse-dot pulse-dot-green" />
                <span>Systems Operational</span>
              </div>
              <div style={{ color: 'var(--text-dim)', fontSize: '0.68rem', paddingLeft: '1rem' }}>
                All services connected
              </div>
            </div>
          )}
        </div>
      </aside>

      <style>{`
        @media (max-width: 1023px) {
          .app-sidebar {
            position: fixed !important;
            top: 0;
            left: 0;
            bottom: 0;
            width: 260px !important;
            transform: translateX(-100%);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
          }
          .app-sidebar.mobile-open {
            transform: translateX(0) !important;
          }
          .mobile-close-btn {
            display: flex !important;
          }
          .collapse-toggle-bar {
            display: none !important;
          }
        }
      `}</style>
    </>
  );
}
