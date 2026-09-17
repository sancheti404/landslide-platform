import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useRiskAssessment } from '../../hooks/useRiskAssessment';
import { useGeolocation } from '../../hooks/useGeolocation';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { UnsupportedLocation } from '../../components/feedback/UnsupportedLocation';
import { DemoDataNotice } from '../../components/feedback/DemoDataNotice';
import { ErrorState } from '../../components/feedback/ErrorState';
import { PRESET_LOCATIONS } from '../../constants/geographicBounds';
import { isWithinUttarakhand } from '../../utils/geoValidators';
import { getRiskLevelConfig } from '../../constants/riskLevels';
import { formatScore, formatRainfallMm } from '../../utils/formatters';
import {
  Crosshair,
  Navigation,
  Loader2,
  Calendar,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  MapPin,
  CheckCircle2,
  CloudRain,
  Mountain,
  Eye,
  Info,
} from 'lucide-react';

export function RiskAssessment() {
  const [searchParams] = useSearchParams();
  const queryLat = searchParams.get('lat');
  const queryLon = searchParams.get('lon');

  const [latitude, setLatitude] = useState(queryLat || '30.529505');
  const [longitude, setLongitude] = useState(queryLon || '79.085957');
  const [timestamp, setTimestamp] = useState('2023-07-15');
  const [techDetailsOpen, setTechDetailsOpen] = useState(false);
  const [inputError, setInputError] = useState(null);

  const { data, loading, error, assess, reset } = useRiskAssessment();
  const {
    location: geoLoc,
    loading: geoLoading,
    error: geoError,
    requestLocation,
  } = useGeolocation();

  // If query params change, update coordinates and assess
  useEffect(() => {
    if (queryLat && queryLon) {
      setLatitude(queryLat);
      setLongitude(queryLon);
      reset();
      if (isWithinUttarakhand(queryLat, queryLon)) {
        assess({
          latitude: parseFloat(queryLat),
          longitude: parseFloat(queryLon),
          timestamp,
          rainfallWeight: 0.5,
          combinationMode: 'multiplicative',
        });
      }
    }
  }, [queryLat, queryLon]);

  // Handle explicit geolocation acquisition
  useEffect(() => {
    if (geoLoc) {
      reset();
      setLatitude(geoLoc.latitude.toFixed(6));
      setLongitude(geoLoc.longitude.toFixed(6));
    }
  }, [geoLoc]);

  // Validation checks
  const parsedLat = parseFloat(latitude);
  const parsedLon = parseFloat(longitude);
  const isNumeric = !Number.isNaN(parsedLat) && !Number.isNaN(parsedLon);
  const isInside = isNumeric && isWithinUttarakhand(parsedLat, parsedLon);

  const handleLatChange = (e) => {
    setLatitude(e.target.value);
    setInputError(null);
    reset(); // Clear stale assessment results on edit
  };

  const handleLonChange = (e) => {
    setLongitude(e.target.value);
    setInputError(null);
    reset(); // Clear stale assessment results on edit
  };

  const handleAssess = async (e) => {
    if (e) e.preventDefault();

    if (!isNumeric) {
      setInputError('Please enter valid numeric coordinates.');
      reset();
      return;
    }

    if (!isInside) {
      setInputError('Location outside supported area');
      reset();
      return;
    }

    setInputError(null);

    try {
      await assess({
        latitude: parsedLat,
        longitude: parsedLon,
        timestamp,
        rainfallWeight: 0.5,
        combinationMode: 'multiplicative',
      });
    } catch (err) {
      console.error('Assessment evaluation error:', err);
    }
  };

  const handleSelectPreset = (preset) => {
    setLatitude(preset.latitude.toString());
    setLongitude(preset.longitude.toString());
    setInputError(null);
    reset();
  };

  // Semantic risk computation
  const semanticRisk = data ? getSemanticRisk(data.risk_level || data.operational_landslide_risk_score) : null;
  const terrainCondition = data ? getConditionLevel(data.xgboost_probability, 'terrain') : null;
  const satelliteCondition = data ? getConditionLevel(data.swin_probability, 'satellite') : null;
  const rainfallCondition = data ? getConditionLevel(data.trigger_indicator || data.dynamic_rainfall_trigger_score, 'rainfall') : null;

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', padding: '1.75rem 1.25rem', width: '100%' }}>
      {/* 1. Page Header */}
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '0.35rem' }}>
          Check a Location
        </h1>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0 }}>
          See landslide risk and recent rainfall conditions for a specific location.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* 2. Location Input Card */}
        <section
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.5rem',
            boxShadow: 'var(--shadow-xs)',
          }}
          aria-label="Location Selection"
        >
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1rem' }}>
            Where would you like to check?
          </h2>

          <form onSubmit={handleAssess} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
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
                  Assessment date
                </label>
                <input
                  type="date"
                  value={timestamp}
                  onChange={(e) => {
                    setTimestamp(e.target.value);
                    reset();
                  }}
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
            </div>

            {/* Date Context Note */}
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Historical assessments reflect recorded precipitation and satellite imagery on the selected date.
            </div>

            {/* Primary Action Buttons */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center', marginTop: '0.25rem' }}>
              <Button
                type="submit"
                variant="primary"
                size="md"
                disabled={!isInside || loading}
                loading={loading}
                icon={<Crosshair size={16} />}
              >
                {loading ? 'Checking Risk...' : 'Check Risk'}
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

            {/* 3. Validation Warnings */}
            {(!isInside && isNumeric) && (
              <div style={{ marginTop: '0.5rem' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#dc2626', marginBottom: '0.25rem' }}>
                  Location outside supported area
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  Please choose a location within the supported Uttarakhand area.
                </div>
                <UnsupportedLocation
                  latitude={parsedLat}
                  longitude={parsedLon}
                  onSelectPreset={(preset) => {
                    handleSelectPreset(preset);
                  }}
                />
              </div>
            )}

            {inputError && (
              <div style={{ fontSize: '0.8rem', color: '#dc2626', background: '#fef2f2', padding: '0.5rem', borderRadius: 'var(--radius-sm)' }}>
                {inputError}
              </div>
            )}
          </form>

          {/* Quick Presets Strip */}
          <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Sample Locations
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {PRESET_LOCATIONS.map((preset) => (
                <button
                  key={preset.name}
                  type="button"
                  onClick={() => handleSelectPreset(preset)}
                  style={{
                    padding: '0.35rem 0.65rem',
                    borderRadius: 'var(--radius-full)',
                    background: '#f8fafc',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.78rem',
                    color: 'var(--text-secondary)',
                    fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#ffffff';
                    e.currentTarget.style.borderColor = 'var(--brand-primary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#f8fafc';
                    e.currentTarget.style.borderColor = 'var(--border-subtle)';
                  }}
                >
                  {preset.name} ({preset.district})
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Loading Spinner */}
        {loading && (
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <LoadingSpinner label="Evaluating landslide risk for selected location..." />
          </div>
        )}

        {/* API Error State */}
        {error && !error.isUnsupportedLocation && (
          <ErrorState
            title="Assessment Failed"
            message={error.message || 'Unable to retrieve assessment data.'}
            onRetry={handleAssess}
          />
        )}

        {/* Assessment Results Section */}
        {data && !loading && (
          <>
            {/* 5. Result: LANDSLIDE RISK (Visually Dominant) */}
            <section
              style={{
                background: semanticRisk.bgColor,
                border: `1px solid ${semanticRisk.borderColor}`,
                borderRadius: 'var(--radius-md)',
                padding: '1.75rem',
                textAlign: 'center',
                boxShadow: 'var(--shadow-sm)',
              }}
              aria-label="Assessment Result"
            >
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.08em', marginBottom: '0.4rem' }}>
                LANDSLIDE RISK
              </div>
              <div
                style={{
                  fontSize: '2.5rem',
                  fontWeight: 900,
                  color: semanticRisk.color,
                  letterSpacing: '-0.02em',
                  lineHeight: 1.1,
                }}
              >
                {semanticRisk.label}
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.4rem' }}>
                {semanticRisk.semanticDesc}
              </div>
              {data.operational_landslide_risk_score != null && (
                <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '0.75rem' }}>
                  Operational Risk Score: <span className="font-mono" style={{ fontWeight: 700 }}>{data.operational_landslide_risk_score.toFixed(2)}</span>
                </div>
              )}
            </section>

            {/* 6. Contributing Conditions ("What's contributing?") */}
            <section
              style={{
                background: '#ffffff',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
                What's contributing?
              </h2>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.85rem' }}>
                <ConditionCard
                  title="Terrain"
                  subtitle="Slope & elevation factors"
                  level={terrainCondition}
                  icon={<Mountain size={18} style={{ color: '#0284c7' }} />}
                />
                <ConditionCard
                  title="Satellite"
                  subtitle="Surface vegetation & visual patterns"
                  level={satelliteCondition}
                  icon={<Eye size={18} style={{ color: '#0f766e' }} />}
                />
                <ConditionCard
                  title="Rainfall"
                  subtitle="Antecedent precipitation trigger"
                  level={rainfallCondition}
                  icon={<CloudRain size={18} style={{ color: '#6366f1' }} />}
                />
              </div>
            </section>

            {/* 7. Recent Rainfall */}
            <section
              style={{
                background: '#ffffff',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                  Recent Rainfall
                </h2>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--brand-primary)' }}>
                  Rainfall condition: {rainfallCondition || 'Normal'}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.65rem' }}>
                <RainfallItem label="Last 3 days" value={data.rainfall_3d_mm} />
                <RainfallItem label="Last 7 days" value={data.rainfall_7d_mm} />
                <RainfallItem label="Last 14 days" value={data.rainfall_14d_mm} />
                <RainfallItem label="Last 30 days" value={data.rainfall_30d_mm} />
              </div>
            </section>

            {/* 8. Location Context */}
            <section
              style={{
                background: '#ffffff',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
                Location Information
              </h2>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.85rem' }}>
                <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Supported area</div>
                  <div style={{ fontWeight: 700, fontSize: '0.875rem', color: '#059669', marginTop: '0.2rem' }}>
                    Inside UK-LIP area
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Risk zone</div>
                  <div style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                    {data.intersecting_risk_zone_name || 'Not currently mapped to a risk zone'}
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Nearby emergency resources</div>
                  <div style={{ fontWeight: 600, fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                    {data.nearby_hospitals_count != null ? (
                      `${data.nearby_hospitals_count} medical, ${data.nearby_shelters_count ?? 0} shelters within 5km`
                    ) : (
                      'No data available'
                    )}
                  </div>
                </div>
              </div>

              {data.nearby_hospitals_count != null && (
                <div style={{ marginTop: '0.75rem' }}>
                  <DemoDataNotice entity="Nearby facilities" />
                </div>
              )}
            </section>

            {/* 10. Explanation ("Why this result?") */}
            <section
              style={{
                background: '#f8fafc',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '1.15rem 1.25rem',
              }}
            >
              <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
                Why this result?
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                Terrain characteristics, satellite imagery, and recent rainfall are combined to estimate operational landslide risk.
              </p>
            </section>

            {/* 9. Technical Details (Collapsed by Default) */}
            <section style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
              <button
                type="button"
                onClick={() => setTechDetailsOpen((prev) => !prev)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.25rem 0',
                }}
              >
                <span>View technical details</span>
                {techDetailsOpen ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              </button>

              {techDetailsOpen && (
                <div
                  style={{
                    marginTop: '0.75rem',
                    background: '#ffffff',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem 1.25rem',
                    fontSize: '0.8rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.55rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Terrain model:</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      XGBoost ({formatScore(data.xgboost_probability, 4)})
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Satellite model:</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      Swin Transformer ({formatScore(data.swin_probability, 4)})
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Fusion:</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      0.38 XGBoost + 0.62 Swin ({formatScore(data.static_visual_fusion_score, 4)})
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Rainfall:</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      CHIRPS Daily (Trigger score: {formatScore(data.dynamic_rainfall_trigger_score, 4)})
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Terrain source:</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>SRTM GL1 30m DEM</span>
                  </div>

                  <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-subtle)', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                    Risk scores are decision-support heuristics and should not be interpreted as calibrated probabilities.
                  </div>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}

function ConditionCard({ title, subtitle, level, icon }) {
  const getBadgeStyle = (lvl) => {
    switch (lvl) {
      case 'High':
      case 'Severe':
        return { bg: '#fef2f2', text: '#dc2626', border: '#fecaca' };
      case 'Moderate':
      case 'Elevated':
        return { bg: '#fffbeb', text: '#d97706', border: '#fde68a' };
      case 'Low':
        return { bg: '#ecfdf5', text: '#059669', border: '#a7f3d0' };
      default:
        return { bg: '#f1f5f9', text: '#64748b', border: '#e2e8f0' };
    }
  };

  const badge = getBadgeStyle(level);

  return (
    <div
      style={{
        background: '#f8fafc',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-sm)',
        padding: '0.85rem 1rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>{title}</span>
        {icon}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.25rem' }}>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{subtitle}</span>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            background: badge.bg,
            color: badge.text,
            border: `1px solid ${badge.border}`,
            padding: '0.15rem 0.5rem',
            borderRadius: 'var(--radius-full)',
          }}
        >
          {level || 'Not available'}
        </span>
      </div>
    </div>
  );
}

function RainfallItem({ label, value }) {
  return (
    <div style={{ background: '#f8fafc', padding: '0.75rem 0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
      <div className="font-mono" style={{ fontWeight: 800, fontSize: '1rem', color: '#0284c7' }}>
        {value != null ? formatRainfallMm(value) : '—'}
      </div>
      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>{label}</div>
    </div>
  );
}

function getSemanticRisk(levelOrScore) {
  const config = getRiskLevelConfig(levelOrScore);
  const key = config.key || 'LOW';

  let label = 'LOW';
  let semanticDesc = 'Low operational risk';

  if (key === 'CRITICAL') {
    label = 'CRITICAL';
    semanticDesc = 'Very high operational risk';
  } else if (key === 'HIGH') {
    label = 'HIGH';
    semanticDesc = 'High operational risk';
  } else if (key === 'MODERATE') {
    label = 'MODERATE';
    semanticDesc = 'Moderate operational risk';
  } else {
    label = 'LOW';
    semanticDesc = 'Low operational risk';
  }

  return {
    key,
    label,
    semanticDesc,
    color: config.color,
    bgColor: config.bgColor,
    borderColor: config.borderColor,
  };
}

function getConditionLevel(val, type) {
  if (val == null) return 'Not available';

  if (type === 'rainfall') {
    if (typeof val === 'string') {
      const s = val.toUpperCase();
      if (s === 'CRITICAL') return 'Severe';
      if (s === 'WARNING' || s === 'ELEVATED') return 'Elevated';
      if (s === 'MODERATE') return 'Moderate';
      if (s === 'NORMAL' || s === 'LOW') return 'Low';
      return s;
    }
    if (val >= 0.75) return 'Severe';
    if (val >= 0.45) return 'Elevated';
    if (val >= 0.25) return 'Moderate';
    return 'Low';
  }

  if (val >= 0.65) return 'High';
  if (val >= 0.35) return 'Moderate';
  return 'Low';
}
