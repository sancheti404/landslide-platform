import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getNearbyInfrastructure } from '../../services/infrastructureApi';
import { useGeolocation } from '../../hooks/useGeolocation';
import { MapView } from '../../components/map/MapView';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { UnsupportedLocation } from '../../components/feedback/UnsupportedLocation';
import { isWithinUttarakhand } from '../../utils/geoValidators';
import { PRESET_LOCATIONS } from '../../constants/geographicBounds';
import {
  Shield,
  Hospital,
  Home,
  Navigation,
  Loader2,
  Search,
  AlertTriangle,
  MapPin,
  Route as RouteIcon,
  ExternalLink,
  PhoneCall,
  CheckCircle2,
  AlertCircle,
  Building2,
} from 'lucide-react';

export function Emergency() {
  const [searchParams] = useSearchParams();
  const initialLat = searchParams.get('lat') || '30.529505';
  const initialLon = searchParams.get('lon') || '79.085957';

  const [latitude, setLatitude] = useState(initialLat);
  const [longitude, setLongitude] = useState(initialLon);
  const [radiusMeters, setRadiusMeters] = useState('10000'); // 10 km default
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasQueried, setHasQueried] = useState(false);

  // Evacuation Planning state
  const [selectedDestination, setSelectedDestination] = useState(null);

  const {
    location: geoLoc,
    loading: geoLoading,
    error: geoError,
    requestLocation,
  } = useGeolocation();

  // Populate coordinates if geolocation acquired
  useEffect(() => {
    if (geoLoc) {
      setLatitude(geoLoc.latitude.toFixed(6));
      setLongitude(geoLoc.longitude.toFixed(6));
      setResources([]);
      setHasQueried(false);
      setSelectedDestination(null);
    }
  }, [geoLoc]);

  // Validation
  const parsedLat = parseFloat(latitude);
  const parsedLon = parseFloat(longitude);
  const isNumeric = !Number.isNaN(parsedLat) && !Number.isNaN(parsedLon);
  const isInside = isNumeric && isWithinUttarakhand(parsedLat, parsedLon);

  const handleLatChange = (e) => {
    setLatitude(e.target.value);
    setResources([]);
    setHasQueried(false);
    setSelectedDestination(null);
  };

  const handleLonChange = (e) => {
    setLongitude(e.target.value);
    setResources([]);
    setHasQueried(false);
    setSelectedDestination(null);
  };

  const fetchResources = useCallback(async () => {
    if (!isInside) return;

    try {
      setLoading(true);
      setError(null);
      const data = await getNearbyInfrastructure({
        latitude: parsedLat,
        longitude: parsedLon,
        distance: parseInt(radiusMeters, 10),
      });
      setResources(Array.isArray(data) ? data : []);
      setHasQueried(true);
    } catch (err) {
      console.error('Failed to fetch emergency resources:', err);
      setError('Emergency resource information is temporarily unavailable.');
    } finally {
      setLoading(false);
    }
  }, [isInside, parsedLat, parsedLon, radiusMeters]);

  // Initial fetch if valid coordinate exists
  useEffect(() => {
    if (isInside) {
      fetchResources();
    }
  }, []);

  const handleSelectPreset = (preset) => {
    setLatitude(preset.latitude.toString());
    setLongitude(preset.longitude.toString());
    setResources([]);
    setHasQueried(false);
    setSelectedDestination(null);
  };

  // Filter resources by simple user-friendly categories
  const filteredResources = resources.filter((item) => {
    if (selectedCategory === 'ALL') return true;
    if (selectedCategory === 'HOSPITAL') return item.type === 'HOSPITAL';
    if (selectedCategory === 'SHELTER') return item.type === 'SHELTER';
    if (selectedCategory === 'POLICE') return item.type === 'POLICE_STATION';
    if (selectedCategory === 'FIRE') return item.type === 'FIRE_STATION';
    return true;
  });

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', padding: '1.75rem 1.25rem', width: '100%' }}>
      {/* 1. Header */}
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '0.35rem' }}>
              Emergency & Evacuation
            </h1>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0 }}>
              Find nearby emergency resources and plan your response when landslide risk is elevated.
            </p>
          </div>
          <Badge variant="warning">Demo emergency resource data</Badge>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* 2. Location Card ("Your location") */}
        <section
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem 1.5rem',
            boxShadow: 'var(--shadow-xs)',
          }}
          aria-label="Location Input"
        >
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
            Your location
          </h2>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              fetchResources();
            }}
            style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.85rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
                  Latitude (°N)
                </label>
                <input
                  type="number"
                  step="any"
                  value={latitude}
                  onChange={handleLatChange}
                  placeholder="e.g. 30.5295"
                  required
                  style={{
                    width: '100%',
                    padding: '0.55rem 0.75rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.9rem',
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
                  Longitude (°E)
                </label>
                <input
                  type="number"
                  step="any"
                  value={longitude}
                  onChange={handleLonChange}
                  placeholder="e.g. 79.0860"
                  required
                  style={{
                    width: '100%',
                    padding: '0.55rem 0.75rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.9rem',
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
                  Search Radius
                </label>
                <select
                  value={radiusMeters}
                  onChange={(e) => setRadiusMeters(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.55rem 0.75rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.9rem',
                    background: '#ffffff',
                  }}
                >
                  <option value="5000">Within 5 km</option>
                  <option value="10000">Within 10 km</option>
                  <option value="25000">Within 25 km</option>
                  <option value="50000">Within 50 km</option>
                </select>
              </div>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center', marginTop: '0.25rem' }}>
              <Button
                type="submit"
                variant="primary"
                size="md"
                disabled={!isInside || loading}
                loading={loading}
                icon={<Search size={15} />}
              >
                {loading ? 'Finding Resources...' : 'Find Nearby Resources'}
              </Button>

              <Button
                type="button"
                variant="secondary"
                size="md"
                onClick={requestLocation}
                disabled={geoLoading}
                icon={geoLoading ? <Loader2 size={15} className="animate-spin" /> : <Navigation size={15} />}
              >
                {geoLoading ? 'Locating...' : 'Use My Location'}
              </Button>
            </div>

            {/* Geolocation Feedback */}
            {geoError && (
              <div style={{ fontSize: '0.78rem', color: '#dc2626', background: '#fef2f2', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid #fecaca' }}>
                {geoError.message}
              </div>
            )}

            {/* Unsupported location error */}
            {!isInside && isNumeric && (
              <div style={{ marginTop: '0.5rem' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#dc2626', marginBottom: '0.25rem' }}>
                  Location outside supported area.
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                  Please choose a location within the supported Uttarakhand area.
                </div>
                <UnsupportedLocation
                  latitude={parsedLat}
                  longitude={parsedLon}
                  onSelectPreset={handleSelectPreset}
                />
              </div>
            )}
          </form>

          {/* Sample Presets */}
          <div style={{ marginTop: '1rem', paddingTop: '0.85rem', borderTop: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.35rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Sample Locations
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {PRESET_LOCATIONS.map((preset) => (
                <button
                  key={preset.name}
                  type="button"
                  onClick={() => handleSelectPreset(preset)}
                  style={{
                    padding: '0.3rem 0.6rem',
                    borderRadius: 'var(--radius-full)',
                    background: '#f8fafc',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.75rem',
                    color: 'var(--text-secondary)',
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* 6. Simple Map Canvas */}
        <section
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem',
            boxShadow: 'var(--shadow-xs)',
          }}
          aria-label="Map Overview"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Location & Resource Map
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {resources.length} facilities mapped
            </span>
          </div>

          <div style={{ height: '360px', borderRadius: 'var(--radius-sm)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
            <MapView
              height="100%"
              showLegend={false}
              showLayers={false}
              selectedLocation={isInside ? { latitude: parsedLat, longitude: parsedLon, isInside: true } : null}
              resources={resources}
              destinationLocation={selectedDestination}
              onResourceClick={(res) => setSelectedDestination(res)}
            />
          </div>
        </section>

        {/* 3. Nearby Emergency Resources */}
        <section
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem 1.5rem',
            boxShadow: 'var(--shadow-xs)',
          }}
          aria-label="Nearby Resources List"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Nearby Emergency Resources
            </h2>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#d97706', background: '#fef3c7', padding: '0.15rem 0.5rem', borderRadius: 'var(--radius-full)' }}>
              Demo emergency resource data
            </span>
          </div>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Emergency locations shown here are demo data for platform testing. Never present synthetic facilities as verified government emergency centers or official shelters.
          </p>

          {/* Category Filter Pills */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '1rem' }}>
            {[
              { id: 'ALL', label: 'All Resources' },
              { id: 'HOSPITAL', label: 'Hospitals' },
              { id: 'SHELTER', label: 'Shelters / Relief' },
              { id: 'POLICE', label: 'Police' },
              { id: 'FIRE', label: 'Fire & Rescue' },
            ].map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => setSelectedCategory(cat.id)}
                style={{
                  padding: '0.35rem 0.75rem',
                  borderRadius: 'var(--radius-full)',
                  border: `1px solid ${selectedCategory === cat.id ? 'var(--brand-primary)' : 'var(--border-subtle)'}`,
                  background: selectedCategory === cat.id ? '#f0fdf4' : '#ffffff',
                  color: selectedCategory === cat.id ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* 7. Empty & Error States */}
          {loading && (
            <div style={{ padding: '2rem 1rem', textAlign: 'center' }}>
              <LoadingSpinner label="Searching nearby emergency resources..." />
            </div>
          )}

          {error && (
            <div style={{ padding: '1.5rem', textAlign: 'center', color: '#dc2626', background: '#fef2f2', borderRadius: 'var(--radius-sm)', border: '1px solid #fecaca', fontSize: '0.85rem' }}>
              {error}
            </div>
          )}

          {!loading && !error && !hasQueried && (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-muted)' }}>
              <Building2 size={32} style={{ color: 'var(--text-dim)', margin: '0 auto 0.5rem' }} />
              <div style={{ fontSize: '0.875rem' }}>Choose a location to find nearby resources.</div>
            </div>
          )}

          {!loading && !error && hasQueried && filteredResources.length === 0 && (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-muted)' }}>
              <AlertCircle size={32} style={{ color: 'var(--text-dim)', margin: '0 auto 0.5rem' }} />
              <div style={{ fontSize: '0.875rem' }}>No nearby resources were returned for this location.</div>
            </div>
          )}

          {/* Resource List Items */}
          {!loading && !error && filteredResources.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {filteredResources.map((item) => (
                <div
                  key={item.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.85rem 1rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    background: selectedDestination?.id === item.id ? '#f0fdf4' : '#ffffff',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                        {item.name}
                      </span>
                      <Badge variant={item.type === 'HOSPITAL' ? 'success' : 'info'}>
                        {item.type || 'Facility'}
                      </Badge>
                      <span style={{ fontSize: '0.68rem', color: '#d97706', background: '#fef3c7', padding: '0.1rem 0.35rem', borderRadius: 'var(--radius-full)', fontWeight: 600 }}>
                        Demo data
                      </span>
                    </div>

                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      Location: {item.latitude?.toFixed(4)}°N, {item.longitude?.toFixed(4)}°E &bull; {item.description || 'Emergency facility'}
                    </div>
                  </div>

                  <Button
                    variant={selectedDestination?.id === item.id ? 'primary' : 'secondary'}
                    size="sm"
                    onClick={() => setSelectedDestination(item)}
                    icon={<RouteIcon size={14} />}
                  >
                    {selectedDestination?.id === item.id ? 'Selected Target' : 'Plan Evacuation'}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* 4. Evacuation Planning ("Plan an evacuation") */}
        <section
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem 1.5rem',
            boxShadow: 'var(--shadow-xs)',
          }}
          aria-label="Evacuation Planning"
        >
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
            Plan an evacuation
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ background: '#f8fafc', padding: '0.85rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                Origin (Current/Selected Location)
              </div>
              <div className="font-mono" style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                {isInside ? `${parsedLat.toFixed(4)}°N, ${parsedLon.toFixed(4)}°E` : 'None selected'}
              </div>
            </div>

            <div style={{ background: '#f8fafc', padding: '0.85rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                Destination Facility
              </div>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: selectedDestination ? 'var(--brand-primary)' : 'var(--text-secondary)', marginTop: '0.25rem' }}>
                {selectedDestination ? `${selectedDestination.name} (${selectedDestination.type})` : 'Select a facility from the list above'}
              </div>
            </div>
          </div>

          {/* Reference Route Display */}
          {selectedDestination ? (
            <div
              style={{
                background: '#f8fafc',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '1rem 1.25rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <RouteIcon size={16} style={{ color: 'var(--brand-primary)' }} />
                  <span>Reference Route</span>
                </div>
                <a
                  href={`https://www.google.com/maps/dir/?api=1&origin=${parsedLat},${parsedLon}&destination=${selectedDestination.latitude},${selectedDestination.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    fontSize: '0.78rem',
                    color: 'var(--brand-primary)',
                    fontWeight: 600,
                    textDecoration: 'none',
                  }}
                >
                  <span>Open Directions in Google Maps</span>
                  <ExternalLink size={13} />
                </a>
              </div>

              {/* Required Critical Safety Disclaimer */}
              <div
                style={{
                  background: '#fffbeb',
                  border: '1px solid #fde68a',
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.78rem',
                  color: '#92400e',
                  lineHeight: 1.45,
                  marginTop: '0.5rem',
                }}
              >
                <strong>Important Notice:</strong> Route geometry does not account for landslide hazards unless hazard-aware analysis is explicitly available. This is a standard reference route and must not be assumed safe during active slope instability or extreme rainfall events.
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              Select any nearby hospital or shelter above to preview a reference route.
            </div>
          )}
        </section>

        {/* 5. Risk-Aware Response Guidance ("During elevated landslide risk") */}
        <section
          style={{
            background: '#f8fafc',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem 1.5rem',
          }}
          aria-label="Safety Guidance"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <Shield size={18} style={{ color: '#0f766e' }} />
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              During elevated landslide risk
            </h2>
          </div>

          <ul style={{ paddingLeft: '1.25rem', margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.5rem', lineHeight: 1.45 }}>
            <li>Avoid unstable slopes and recently affected areas.</li>
            <li>Follow instructions from local authorities.</li>
            <li>Avoid blocked or damaged roads.</li>
            <li>Move to a confirmed safe location if authorities advise evacuation.</li>
            <li>Do not enter an active landslide area.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}

export default Emergency;
