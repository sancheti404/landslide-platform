import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ROUTES } from '../../constants/routes';
import { getMlHealth } from '../../services/riskApi';
import { getDistrictSummary } from '../../services/gisApi';
import { Button } from '../../components/common/Button';
import { GoogleMap } from '../../components/map/GoogleMap';
import {
  Map,
  Crosshair,
  CloudRain,
  Database,
  Shield,
  HelpCircle,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';

export function Home() {
  const navigate = useNavigate();
  const [mlStatus, setMlStatus] = useState(null);
  const [, setDistrictCounts] = useState(null);

  useEffect(() => {
    async function loadTelemetry() {
      try {
        const [healthRes, distRes] = await Promise.allSettled([
          getMlHealth(),
          getDistrictSummary(),
        ]);
        if (healthRes.status === 'fulfilled') setMlStatus(healthRes.value);
        if (distRes.status === 'fulfilled') setDistrictCounts(distRes.value);
      } catch (e) {
        console.error('Home telemetry load error:', e);
      }
    }
    loadTelemetry();
  }, []);

  return (
    <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto', padding: '1.5rem 1.75rem', width: '100%' }}>
      {/* 1. Hero Section */}
      <div
        style={{
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '1rem',
        }}
      >
        <div>
          <h1
            style={{
              fontSize: '1.65rem',
              fontWeight: 800,
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
              marginBottom: '0.35rem',
            }}
          >
            Uttarakhand Landslide Intelligence Platform
          </h1>
          <p style={{ fontSize: '0.925rem', color: 'var(--text-secondary)' }}>
            Check landslide conditions, explore risk areas, and understand recent rainfall across Uttarakhand.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.45rem',
              padding: '0.35rem 0.85rem',
              borderRadius: 'var(--radius-full)',
              background: '#ecfdf5',
              border: '1px solid #a7f3d0',
              color: '#059669',
              fontSize: '0.8rem',
              fontWeight: 700,
            }}
          >
            <span className="pulse-dot pulse-dot-green" />
            <span>Systems Operational</span>
          </div>
        </div>
      </div>

      {/* 2. Quick Status (4 simple cards) */}
      <section
        aria-label="Platform Status"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <StatusCard
          title="Landslide Monitoring"
          description="Location-based risk assessment available"
          icon={<Crosshair size={18} style={{ color: 'var(--brand-primary)' }} />}
        />
        <StatusCard
          title="Rainfall Conditions"
          description="Daily rainfall information available"
          icon={<CloudRain size={18} style={{ color: '#0284c7' }} />}
        />
        <StatusCard
          title="Landslide History"
          description="5,523 GSI records"
          icon={<Database size={18} style={{ color: '#6366f1' }} />}
        />
        <StatusCard
          title="System Status"
          description="Connected services available"
          icon={<CheckCircle2 size={18} style={{ color: '#059669' }} />}
          connected={mlStatus?.status === 'healthy'}
        />
      </section>

      {/* 3. Main Map Section */}
      <section
        style={{
          background: '#ffffff',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
          boxShadow: 'var(--shadow-sm)',
          marginBottom: '1.75rem',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem',
            flexWrap: 'wrap',
            gap: '0.75rem',
          }}
        >
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Explore Landslide Risk Across Uttarakhand
            </h2>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
              Select a location on the map to inspect available information.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
            <Link to={ROUTES.RISK_MAP} style={{ textDecoration: 'none' }}>
              <Button size="sm" icon={<Map size={15} />}>
                Explore Live Risk Map
              </Button>
            </Link>
            <Link to={ROUTES.ASSESS} style={{ textDecoration: 'none' }}>
              <Button variant="secondary" size="sm" icon={<Crosshair size={15} />}>
                Check a Location
              </Button>
            </Link>
          </div>
        </div>

        {/* Map Canvas */}
        <div
          style={{
            height: '460px',
            borderRadius: 'var(--radius-sm)',
            overflow: 'hidden',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <GoogleMap
            height="100%"
            showLegend={false}
            showLayers={false}
            selectedLocation={{ latitude: 30.529505, longitude: 79.085957, isInside: true }}
            onLocationSelect={(loc) => navigate(`${ROUTES.ASSESS}?lat=${loc.latitude}&lon=${loc.longitude}`)}
          />
        </div>
      </section>

      {/* 4. Quick Actions */}
      <section style={{ marginBottom: '1.5rem' }}>
        <div style={{ marginBottom: '0.85rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            What would you like to do?
          </h2>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '1rem',
          }}
        >
          <ActionCard
            title="Check a Location"
            description="See landslide risk for a specific place."
            path={ROUTES.ASSESS}
            icon={<Crosshair size={20} style={{ color: 'var(--brand-primary)' }} />}
          />
          <ActionCard
            title="Explore Live Risk Map"
            description="Explore Uttarakhand on the map."
            path={ROUTES.RISK_MAP}
            icon={<Map size={20} style={{ color: '#0284c7' }} />}
          />
          <ActionCard
            title="View Landslide History"
            description="Explore 5,523 recorded GSI landslides."
            path={ROUTES.LANDSLIDES}
            icon={<Database size={20} style={{ color: '#6366f1' }} />}
          />
          <ActionCard
            title="Emergency & Evacuation"
            description="Find available nearby resources and planning tools."
            path={ROUTES.EMERGENCY}
            icon={<Shield size={20} style={{ color: '#059669' }} />}
          />
          <ActionCard
            title="How It Works"
            description="Learn how terrain, satellite imagery, and rainfall are evaluated."
            path={ROUTES.HOW_IT_WORKS}
            icon={<HelpCircle size={20} style={{ color: '#0f766e' }} />}
          />
        </div>
      </section>
    </div>
  );
}

function StatusCard({ title, description, icon, connected }) {
  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: '1.1rem 1.25rem',
        boxShadow: 'var(--shadow-xs)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
        <span style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
          {title}
        </span>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-sm)',
            background: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {icon}
        </div>
      </div>
      <div>
        <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.35 }}>
          {description}
        </div>
      </div>
    </div>
  );
}

function ActionCard({ title, description, path, icon }) {
  return (
    <Link to={path} style={{ textDecoration: 'none' }}>
      <div
        className="glass-panel-interactive"
        style={{
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          height: '100%',
          minHeight: '120px',
          background: '#ffffff',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-xs)',
          transition: 'all 0.18s ease',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-sm)',
              background: '#f1f5f9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {icon}
          </div>
          <div style={{ flex: 1 }}>
            <div
              style={{
                fontSize: '0.95rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: '0.25rem',
              }}
            >
              {title}
            </div>
            <div
              style={{
                fontSize: '0.8rem',
                color: 'var(--text-secondary)',
                lineHeight: 1.4,
              }}
            >
              {description}
            </div>
          </div>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            marginTop: '0.85rem',
            fontSize: '0.78rem',
            fontWeight: 600,
            color: 'var(--brand-primary)',
          }}
        >
          <span>Open</span>
          <ArrowRight size={13} />
        </div>
      </div>
    </Link>
  );
}
