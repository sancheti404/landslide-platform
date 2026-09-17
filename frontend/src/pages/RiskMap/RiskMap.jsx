import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleMap } from '../../components/map/GoogleMap';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { DemoDataNotice } from '../../components/feedback/DemoDataNotice';
import { UnsupportedLocation } from '../../components/feedback/UnsupportedLocation';
import { PRESET_LOCATIONS } from '../../constants/geographicBounds';
import { isWithinUttarakhand } from '../../utils/geoValidators';
import { ROUTES } from '../../constants/routes';
import { getHistoricalLandslides } from '../../services/gisApi';
import { useGeolocation } from '../../hooks/useGeolocation';
import {
  Crosshair,
  MapPin,
  Layers,
  Navigation,
  Loader2,
  CheckSquare,
  Square,
} from 'lucide-react';

export function RiskMap() {
  const navigate = useNavigate();
  const [selectedCoord, setSelectedCoord] = useState({
    latitude: 30.529505,
    longitude: 79.085957,
    isInside: true,
  });

  const [landslides, setLandslides] = useState([]);
  const [basemapType, setBasemapType] = useState('terrain');

  const [activeLayers, setActiveLayers] = useState({
    operationalArea: true,
    landslides: true,
    riskZones: false,
    infrastructure: false,
  });

  const { location: geoLoc, loading: geoLoading, error: geoError, requestLocation } = useGeolocation();

  // Load authentic GSI NLSM records for map markers
  useEffect(() => {
    let isMounted = true;
    async function loadLandslides() {
      try {
        const data = await getHistoricalLandslides({ limit: 150 });
        if (isMounted && Array.isArray(data)) {
          setLandslides(data);
        }
      } catch (err) {
        console.error('Failed to load historical landslides for map:', err);
      }
    }
    loadLandslides();
    return () => {
      isMounted = false;
    };
  }, []);

  // Update selected location when user clicks "Use My Location"
  useEffect(() => {
    if (geoLoc) {
      const inside = isWithinUttarakhand(geoLoc.latitude, geoLoc.longitude);
      setSelectedCoord({
        latitude: geoLoc.latitude,
        longitude: geoLoc.longitude,
        isInside: inside,
      });
    }
  }, [geoLoc]);

  const toggleLayer = useCallback((layerKey) => {
    setActiveLayers((prev) => ({
      ...prev,
      [layerKey]: !prev[layerKey],
    }));
  }, []);

  const handleLocationSelect = useCallback((loc) => {
    setSelectedCoord({
      latitude: loc.latitude,
      longitude: loc.longitude,
      isInside: isWithinUttarakhand(loc.latitude, loc.longitude),
      landslide: loc.landslide || null,
    });
  }, []);

  const handleAssessClick = () => {
    if (!selectedCoord || !selectedCoord.isInside) return;
    navigate(`${ROUTES.ASSESS}?lat=${selectedCoord.latitude}&lon=${selectedCoord.longitude}`);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      {/* Top GIS Workspace Bar */}
      <div
        style={{
          background: '#ffffff',
          borderBottom: '1px solid var(--border-subtle)',
          padding: '0.75rem 1.5rem',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
            Live Risk Map
          </h1>
          <Badge variant="default">UK-LIP Operational Area</Badge>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span>Envelope: 28.50°N – 31.60°N, 77.40°E – 81.30°E</span>
        </div>
      </div>

      {/* 3-Part GIS Workspace Layout */}
      <div className="risk-map-workspace">
        {/* LEFT: Layer Controls Panel */}
        <aside className="risk-map-panel risk-map-panel-left" aria-label="Map Layers">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-subtle)' }}>
            <Layers size={18} style={{ color: 'var(--brand-primary)' }} />
            <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Map Layers
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <LayerToggleItem
              id="operationalArea"
              label="Operational Area"
              desc="UK-LIP operational boundary (28.50–31.60°N, 77.40–81.30°E)."
              checked={activeLayers.operationalArea}
              onChange={() => toggleLayer('operationalArea')}
              color="#0284c7"
            />
            <LayerToggleItem
              id="landslides"
              label="Historical Landslides"
              desc="Recorded landslide locations from the GSI inventory."
              checked={activeLayers.landslides}
              onChange={() => toggleLayer('landslides')}
              color="#ea580c"
              badge={landslides.length > 0 ? `${landslides.length} records` : '5,523 records'}
            />
            <LayerToggleItem
              id="riskZones"
              label="Risk Zones"
              desc="Development/demo spatial zones where available."
              checked={activeLayers.riskZones}
              onChange={() => toggleLayer('riskZones')}
              color="#dc2626"
              isDemo
            />
            <LayerToggleItem
              id="infrastructure"
              label="Emergency Resources"
              desc="Nearby facilities available in the current dataset."
              checked={activeLayers.infrastructure}
              onChange={() => toggleLayer('infrastructure')}
              color="#059669"
              isDemo
            />
          </div>

          {(activeLayers.riskZones || activeLayers.infrastructure) && (
            <div style={{ marginTop: '1.25rem' }}>
              <DemoDataNotice entity="Risk zones & emergency facilities" />
            </div>
          )}

          {/* Basemap Options */}
          <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Basemap
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <button
                type="button"
                onClick={() => setBasemapType('terrain')}
                style={{
                  padding: '0.45rem 0.6rem',
                  borderRadius: 'var(--radius-sm)',
                  border: `1px solid ${basemapType === 'terrain' ? 'var(--brand-primary)' : 'var(--border-subtle)'}`,
                  background: basemapType === 'terrain' ? '#f0fdf4' : '#ffffff',
                  color: basemapType === 'terrain' ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                Terrain
              </button>
              <button
                type="button"
                onClick={() => setBasemapType('satellite')}
                style={{
                  padding: '0.45rem 0.6rem',
                  borderRadius: 'var(--radius-sm)',
                  border: `1px solid ${basemapType === 'satellite' ? 'var(--brand-primary)' : 'var(--border-subtle)'}`,
                  background: basemapType === 'satellite' ? '#f0fdf4' : '#ffffff',
                  color: basemapType === 'satellite' ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                Satellite
              </button>
            </div>
          </div>
        </aside>

        {/* CENTER: Large Dominant Interactive Map */}
        <main className="risk-map-map-col" aria-label="Interactive Map Canvas">
          <GoogleMap
            height="100%"
            selectedLocation={selectedCoord}
            onLocationSelect={handleLocationSelect}
            activeLayers={activeLayers}
            onToggleLayer={toggleLayer}
            landslides={landslides}
            mapTypeId={basemapType}
            showLayers={false}
          />
        </main>

        {/* RIGHT: Location Information & Inspector Panel */}
        <aside className="risk-map-panel risk-map-panel-right" aria-label="Location Inspector">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Crosshair size={18} style={{ color: 'var(--brand-primary)' }} />
              <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                Location
              </h2>
            </div>
            {selectedCoord && (
              <button
                type="button"
                onClick={() => setSelectedCoord(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '0.75rem', cursor: 'pointer' }}
              >
                Clear
              </button>
            )}
          </div>

          {/* "Use My Location" Action */}
          <div style={{ marginBottom: '1rem' }}>
            <Button
              variant="secondary"
              size="sm"
              onClick={requestLocation}
              disabled={geoLoading}
              icon={geoLoading ? <Loader2 size={14} className="animate-spin" /> : <Navigation size={14} />}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {geoLoading ? 'Locating...' : 'Use My Location'}
            </Button>
            {geoError && (
              <div style={{ marginTop: '0.4rem', fontSize: '0.72rem', color: '#dc2626', lineHeight: 1.3 }}>
                {geoError.message}
              </div>
            )}
          </div>

          {/* Selected Location State */}
          {!selectedCoord ? (
            <div
              style={{
                padding: '2rem 1rem',
                textAlign: 'center',
                background: '#f8fafc',
                borderRadius: 'var(--radius-md)',
                border: '1px dashed var(--border-subtle)',
              }}
            >
              <MapPin size={28} style={{ color: 'var(--text-muted)', margin: '0 auto 0.5rem' }} />
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.4, margin: 0 }}>
                Select a location on the map to see more information.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div
                style={{
                  background: '#f8fafc',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1rem',
                }}
              >
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
                  SELECTED LOCATION
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Latitude</div>
                    <div className="font-mono" style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {selectedCoord.latitude.toFixed(4)}°N
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Longitude</div>
                    <div className="font-mono" style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {selectedCoord.longitude.toFixed(4)}°E
                    </div>
                  </div>
                </div>

                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                    Operational Area
                  </div>
                  {selectedCoord.isInside ? (
                    <Badge variant="success">Inside UK-LIP area</Badge>
                  ) : (
                    <Badge variant="danger">Outside UK-LIP area</Badge>
                  )}
                </div>

                {/* Historical Landslide Record Details if marker was clicked */}
                {selectedCoord.landslide && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#ea580c', marginBottom: '0.35rem' }}>
                      Historical Landslide
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                      <div><strong>District:</strong> {selectedCoord.landslide.district || 'Unspecified'}</div>
                      <div><strong>Type:</strong> {selectedCoord.landslide.movementType || 'Slide'}</div>
                    </div>
                  </div>
                )}

                {/* Assessment action or out-of-bounds warning */}
                {selectedCoord.isInside ? (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleAssessClick}
                    icon={<Crosshair size={14} />}
                    style={{ marginTop: '0.85rem', width: '100%', justifyContent: 'center' }}
                  >
                    Check Location Risk
                  </Button>
                ) : (
                  <div style={{ marginTop: '0.85rem' }}>
                    <div style={{ fontSize: '0.78rem', color: '#dc2626', fontWeight: 600, marginBottom: '0.5rem' }}>
                      Location outside the UK-LIP operational area.
                    </div>
                    <UnsupportedLocation
                      latitude={selectedCoord.latitude}
                      longitude={selectedCoord.longitude}
                      onSelectPreset={(p) => handleLocationSelect({ latitude: p.latitude, longitude: p.longitude, isInside: true })}
                    />
                  </div>
                )}
              </div>

              {/* Reference Locations */}
              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '0.4rem' }}>
                  REFERENCE LOCATIONS
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {PRESET_LOCATIONS.slice(0, 4).map((loc) => (
                    <button
                      key={loc.name}
                      type="button"
                      onClick={() => handleLocationSelect({ latitude: loc.latitude, longitude: loc.longitude, isInside: true })}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.45rem 0.6rem',
                        borderRadius: 'var(--radius-sm)',
                        background: '#ffffff',
                        border: '1px solid var(--border-subtle)',
                        color: 'var(--text-primary)',
                        cursor: 'pointer',
                        textAlign: 'left',
                        fontSize: '0.78rem',
                        transition: 'all 0.15s ease',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--brand-primary)')}
                      onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                    >
                      <div>
                        <span style={{ fontWeight: 600 }}>{loc.name}</span>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginLeft: '0.35rem' }}>{loc.district}</span>
                      </div>
                      <span style={{ color: 'var(--brand-primary)', fontSize: '0.72rem', fontWeight: 600 }}>Inspect</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>

      <style>{`
        .risk-map-workspace {
          display: grid;
          grid-template-columns: 270px minmax(0, 1fr) 290px;
          flex: 1;
          min-height: calc(100vh - var(--nav-height) - 100px);
          background: #f8fafc;
        }

        .risk-map-panel {
          background: #ffffff;
          padding: 1rem;
          overflow-y: auto;
        }

        .risk-map-panel-left {
          border-right: 1px solid var(--border-subtle);
        }

        .risk-map-panel-right {
          border-left: 1px solid var(--border-subtle);
        }

        .risk-map-map-col {
          position: relative;
          min-height: 520px;
          height: 100%;
        }

        @media (max-width: 1024px) {
          .risk-map-workspace {
            display: flex;
            flex-direction: column;
          }
          .risk-map-map-col {
            min-height: 480px;
            height: 480px;
            order: 1;
          }
          .risk-map-panel-right {
            border-left: none;
            border-top: 1px solid var(--border-subtle);
            order: 2;
          }
          .risk-map-panel-left {
            border-right: none;
            border-top: 1px solid var(--border-subtle);
            order: 3;
          }
        }
      `}</style>
    </div>
  );
}

function LayerToggleItem({ id, label, desc, checked, onChange, color, badge, isDemo }) {
  return (
    <div
      onClick={onChange}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.55rem',
        padding: '0.55rem 0.65rem',
        borderRadius: 'var(--radius-sm)',
        cursor: 'pointer',
        border: `1px solid ${checked ? '#cbd5e1' : '#f1f5f9'}`,
        background: checked ? '#f8fafc' : '#ffffff',
        transition: 'all 0.15s ease',
      }}
    >
      <div style={{ color: checked ? 'var(--brand-primary)' : 'var(--text-dim)', marginTop: '2px' }}>
        {checked ? <CheckSquare size={16} /> : <Square size={16} />}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: color, flexShrink: 0 }} />
          <span>{label}</span>
          {isDemo && (
            <span
              style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                color: '#d97706',
                background: '#fef3c7',
                padding: '0.1rem 0.35rem',
                borderRadius: 'var(--radius-full)',
                marginLeft: 'auto',
              }}
            >
              Demo data
            </span>
          )}
          {badge && !isDemo && (
            <span
              style={{
                fontSize: '0.65rem',
                color: 'var(--text-muted)',
                background: '#f1f5f9',
                padding: '0.1rem 0.35rem',
                borderRadius: 'var(--radius-full)',
                marginLeft: 'auto',
              }}
            >
              {badge}
            </span>
          )}
        </div>
        {desc && (
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '0.2rem', lineHeight: 1.35 }}>
            {desc}
          </div>
        )}
      </div>
    </div>
  );
}
