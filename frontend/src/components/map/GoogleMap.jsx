import React, { useState, useCallback } from 'react';
import { useLoadScript, GoogleMap as ReactGoogleMap, MarkerF, InfoWindowF } from '@react-google-maps/api';
import { MAP_CONFIG } from '../../constants/mapConfig';
import { UTTARAKHAND_ENVELOPE } from '../../constants/geographicBounds';
import { isWithinUttarakhand } from '../../utils/geoValidators';
import { MapControls } from './MapControls';
import { MapLegend } from './MapLegend';
import { LayerControl } from './LayerControl';
import { LocationButton } from './LocationButton';
import { MapPin, AlertTriangle } from 'lucide-react';

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

export function GoogleMap({
  selectedLocation,
  onLocationSelect,
  riskLevel = null,
  showLegend = true,
  showLayers = true,
  height = '560px',
  children,
  activeLayers: propActiveLayers,
  onToggleLayer: propToggleLayer,
  landslides = [],
  onLandslideClick,
  resources = [],
  onResourceClick,
  destinationLocation = null,
  mapTypeId = 'terrain',
}) {
  const [mapInstance, setMapInstance] = useState(null);
  const [internalActiveLayers, setInternalActiveLayers] = useState({
    operationalArea: true,
    boundary: true,
    landslides: true,
    riskZones: false,
    infrastructure: true,
  });

  const activeLayers = propActiveLayers || internalActiveLayers;

  const toggleLayer = propToggleLayer || useCallback((layerId) => {
    setInternalActiveLayers((prev) => ({
      ...prev,
      [layerId]: !prev[layerId],
    }));
  }, []);

  const [activeMarker, setActiveMarker] = useState(null);

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
    preventGoogleFontsLoading: true,
  });

  const handleMapClick = useCallback((e) => {
    if (!onLocationSelect) return;
    const lat = e.latLng.lat();
    const lng = e.latLng.lng();
    onLocationSelect({
      latitude: parseFloat(lat.toFixed(6)),
      longitude: parseFloat(lng.toFixed(6)),
      isInside: isWithinUttarakhand(lat, lng),
    });
    setActiveMarker(null);
  }, [onLocationSelect]);

  const handleZoomIn = () => mapInstance && mapInstance.setZoom(mapInstance.getZoom() + 1);
  const handleZoomOut = () => mapInstance && mapInstance.setZoom(mapInstance.getZoom() - 1);
  const handleResetView = () => {
    if (mapInstance) {
      mapInstance.panTo(MAP_CONFIG.defaultCenter);
      mapInstance.setZoom(MAP_CONFIG.defaultZoom);
    }
  };

  const handleLocationFound = (loc) => {
    if (onLocationSelect) {
      onLocationSelect({
        latitude: loc.latitude,
        longitude: loc.longitude,
        isInside: loc.isInsideUttarakhand,
      });
    }
    if (mapInstance) {
      mapInstance.panTo({ lat: loc.latitude, lng: loc.longitude });
      mapInstance.setZoom(11);
    }
  };

  // If no API key configured or script loading error -> render interactive preview fallback
  if (!GOOGLE_MAPS_API_KEY || loadError) {
    return (
      <div className="map-container-root" style={{ height }}>
        <MockMapFallback
          selectedLocation={selectedLocation}
          onLocationSelect={onLocationSelect}
          activeLayers={activeLayers}
          onToggleLayer={toggleLayer}
          onLocationFound={handleLocationFound}
          showLegend={showLegend}
          showLayers={showLayers}
          landslides={landslides}
          onLandslideClick={onLandslideClick}
          resources={resources}
          onResourceClick={onResourceClick}
          destinationLocation={destinationLocation}
        />
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="map-container-root" style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <div className="pulse-dot pulse-dot-green" style={{ marginBottom: '0.5rem' }} />
          <div>Initializing Google Maps Basemap...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="map-container-root" style={{ height }}>
      <ReactGoogleMap
        mapContainerStyle={{ width: '100%', height: '100%' }}
        center={selectedLocation ? { lat: selectedLocation.latitude, lng: selectedLocation.longitude } : MAP_CONFIG.defaultCenter}
        zoom={MAP_CONFIG.defaultZoom}
        options={{
          styles: MAP_CONFIG.styles,
          mapTypeId: mapTypeId || MAP_CONFIG.mapTypeId,
          disableDefaultUI: true,
          restriction: MAP_CONFIG.restriction,
        }}
        onLoad={setMapInstance}
        onClick={handleMapClick}
      >
        {selectedLocation && (
          <MarkerF
            position={{ lat: selectedLocation.latitude, lng: selectedLocation.longitude }}
            title={`Selected: ${selectedLocation.latitude}, ${selectedLocation.longitude}`}
          />
        )}

        {/* Destination Location Marker */}
        {destinationLocation && (
          <MarkerF
            position={{ lat: destinationLocation.latitude, lng: destinationLocation.longitude }}
            icon={{
              path: window.google?.maps?.SymbolPath?.BACKWARD_CLOSED_ARROW || 0,
              scale: 5,
              fillColor: '#dc2626',
              fillOpacity: 1,
              strokeColor: '#ffffff',
              strokeWeight: 2,
            }}
            title={`Destination: ${destinationLocation.name || 'Target'}`}
          />
        )}

        {/* Historical Landslide Markers */}
        {activeLayers.landslides && landslides.map((item) => (
          <MarkerF
            key={item.id || `${item.latitude}-${item.longitude}`}
            position={{ lat: item.latitude, lng: item.longitude }}
            icon={{
              path: window.google?.maps?.SymbolPath?.CIRCLE || 0,
              scale: 4.5,
              fillColor: '#ea580c',
              fillOpacity: 0.85,
              strokeColor: '#ffffff',
              strokeWeight: 1,
            }}
            onClick={() => {
              setActiveMarker({ ...item, category: 'landslide' });
              if (onLandslideClick) onLandslideClick(item);
              if (onLocationSelect) {
                onLocationSelect({
                  latitude: item.latitude,
                  longitude: item.longitude,
                  isInside: true,
                  landslide: item,
                });
              }
            }}
            title={`${item.district || 'Landslide'}: ${item.movementType || 'Slide'}`}
          />
        ))}

        {/* Emergency Resources Markers (Demo Data) */}
        {resources && resources.map((res) => (
          <MarkerF
            key={res.id || `${res.latitude}-${res.longitude}`}
            position={{ lat: res.latitude, lng: res.longitude }}
            icon={{
              path: window.google?.maps?.SymbolPath?.CIRCLE || 0,
              scale: 5.5,
              fillColor: res.type === 'HOSPITAL' ? '#059669' : '#0284c7',
              fillOpacity: 0.9,
              strokeColor: '#ffffff',
              strokeWeight: 1.5,
            }}
            onClick={() => {
              setActiveMarker({ ...res, category: 'resource' });
              if (onResourceClick) onResourceClick(res);
            }}
            title={`${res.name} (${res.type || 'Resource'}) — Demo data`}
          />
        ))}

        {/* InfoWindow for Clicked Marker */}
        {activeMarker && (
          <InfoWindowF
            position={{ lat: activeMarker.latitude, lng: activeMarker.longitude }}
            onCloseClick={() => setActiveMarker(null)}
          >
            <div style={{ color: '#0f172a', padding: '0.2rem 0.4rem', minWidth: '180px' }}>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: activeMarker.category === 'resource' ? '#0284c7' : '#0f766e', marginBottom: '0.25rem' }}>
                {activeMarker.category === 'resource' ? activeMarker.name : 'Historical Landslide'}
              </div>
              {activeMarker.category === 'resource' ? (
                <>
                  <div style={{ fontSize: '0.78rem' }}><strong>Type:</strong> {activeMarker.type || 'Facility'}</div>
                  <div style={{ fontSize: '0.72rem', color: '#d97706', marginTop: '0.25rem', fontWeight: 600 }}>Demo emergency resource data</div>
                </>
              ) : (
                <>
                  <div style={{ fontSize: '0.78rem', marginBottom: '0.15rem' }}>
                    <strong>District:</strong> {activeMarker.district || 'Unspecified'}
                  </div>
                  <div style={{ fontSize: '0.78rem', marginBottom: '0.15rem' }}>
                    <strong>Type:</strong> {activeMarker.movementType || 'Slide'}
                  </div>
                </>
              )}
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
                <strong>Location:</strong> {activeMarker.latitude?.toFixed(4)}°N, {activeMarker.longitude?.toFixed(4)}°E
              </div>
            </div>
          </InfoWindowF>
        )}

        {children}
      </ReactGoogleMap>

      {/* Overlays */}
      <MapControls
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onResetView={handleResetView}
        onCenterLocation={() => {
          if (selectedLocation && mapInstance) {
            mapInstance.panTo({ lat: selectedLocation.latitude, lng: selectedLocation.longitude });
          }
        }}
        hasLocation={!!selectedLocation}
      />

      {showLayers && (
        <LayerControl activeLayers={activeLayers} onToggleLayer={toggleLayer} />
      )}

      {showLegend && <MapLegend />}

      <div style={{ position: 'absolute', bottom: '1.5rem', left: '1rem', zIndex: 10 }}>
        <LocationButton onLocationFound={handleLocationFound} />
      </div>
    </div>
  );
}

/**
 * High-fidelity interactive preview map canvas used when Google API key is absent
 */
function MockMapFallback({
  selectedLocation,
  onLocationSelect,
  activeLayers,
  onToggleLayer,
  onLocationFound,
  showLegend,
  showLayers,
  landslides = [],
  onLandslideClick,
  resources = [],
  onResourceClick,
  destinationLocation = null,
}) {
  const [activeMarker, setActiveMarker] = useState(null);

  const handleFallbackClick = (e) => {
    if (!onLocationSelect) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const xRatio = (e.clientX - rect.left) / rect.width;
    const yRatio = (e.clientY - rect.top) / rect.height;

    // Project click into Uttarakhand geographic envelope
    const lat = UTTARAKHAND_ENVELOPE.MAX_LAT - yRatio * (UTTARAKHAND_ENVELOPE.MAX_LAT - UTTARAKHAND_ENVELOPE.MIN_LAT);
    const lng = UTTARAKHAND_ENVELOPE.MIN_LON + xRatio * (UTTARAKHAND_ENVELOPE.MAX_LON - UTTARAKHAND_ENVELOPE.MIN_LON);

    setActiveMarker(null);
    onLocationSelect({
      latitude: parseFloat(lat.toFixed(6)),
      longitude: parseFloat(lng.toFixed(6)),
      isInside: isWithinUttarakhand(lat, lng),
    });
  };

  const showOperationalEnvelope = activeLayers.operationalArea !== false && activeLayers.boundary !== false && activeLayers.envelope !== false;

  return (
    <div className="mock-map-fallback" onClick={handleFallbackClick}>
      <div className="mock-map-grid" />

      {/* Top Banner Notice */}
      <div
        style={{
          position: 'absolute',
          top: '1rem',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 15,
          background: 'rgba(15, 23, 42, 0.88)',
          backdropFilter: 'var(--glass-blur)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-full)',
          padding: '0.35rem 1rem',
          fontSize: '0.75rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          color: 'var(--text-secondary)',
          boxShadow: 'var(--shadow-md)',
          maxWidth: '90%',
        }}
      >
        <AlertTriangle size={14} style={{ color: '#0284c7', flexShrink: 0 }} />
        <span>Interactive map preview</span>
      </div>

      {/* Operational Area Envelope Outline */}
      <div
        style={{
          position: 'relative',
          width: '78%',
          height: '68%',
          border: showOperationalEnvelope ? '2px dashed #0284c7' : 'none',
          backgroundColor: showOperationalEnvelope ? 'rgba(2, 132, 199, 0.04)' : 'transparent',
          borderRadius: 'var(--radius-lg)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}
      >
        {showOperationalEnvelope && (
          <>
            <div style={{ color: 'var(--brand-cyan)', fontSize: '0.85rem', fontWeight: 600, opacity: 0.85 }}>
              UK-LIP Operational Area
            </div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem', marginTop: '0.2rem' }}>
              28.50°N – 31.60°N &nbsp;|&nbsp; 77.40°E – 81.30°E
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', marginTop: '0.5rem' }}>
              (Click anywhere on this canvas to inspect or place coordinates)
            </div>
          </>
        )}

        {/* Selected coordinate pin */}
        {selectedLocation && (
          <div
            style={{
              position: 'absolute',
              transform: 'translate(-50%, -100%)',
              top: '50%',
              left: '50%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              color: '#f87171',
              pointerEvents: 'auto',
            }}
          >
            <MapPin size={28} style={{ filter: 'drop-shadow(0 2px 6px rgba(239,68,68,0.6))' }} />
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                background: 'rgba(15, 23, 42, 0.9)',
                padding: '0.2rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                marginTop: '2px',
                color: '#fff',
                whiteSpace: 'nowrap',
              }}
            >
              {selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}
            </span>
          </div>
        )}

        {/* Destination Pin */}
        {destinationLocation && (
          <div
            style={{
              position: 'absolute',
              transform: 'translate(-50%, -100%)',
              top: '40%',
              left: '60%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              color: '#dc2626',
              pointerEvents: 'auto',
              zIndex: 12,
            }}
          >
            <MapPin size={26} style={{ filter: 'drop-shadow(0 2px 6px rgba(220,38,38,0.6))' }} />
            <span
              style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                background: '#dc2626',
                padding: '0.15rem 0.4rem',
                borderRadius: 'var(--radius-sm)',
                color: '#fff',
                whiteSpace: 'nowrap',
              }}
            >
              Destination
            </span>
          </div>
        )}

        {/* Historical Landslide markers on fallback canvas */}
        {activeLayers.landslides && landslides && landslides.length > 0 && (
          <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
            {landslides.slice(0, 120).map((item) => {
              const yPct = ((UTTARAKHAND_ENVELOPE.MAX_LAT - item.latitude) / (UTTARAKHAND_ENVELOPE.MAX_LAT - UTTARAKHAND_ENVELOPE.MIN_LAT)) * 100;
              const xPct = ((item.longitude - UTTARAKHAND_ENVELOPE.MIN_LON) / (UTTARAKHAND_ENVELOPE.MAX_LON - UTTARAKHAND_ENVELOPE.MIN_LON)) * 100;
              if (yPct < 0 || yPct > 100 || xPct < 0 || xPct > 100) return null;

              return (
                <div
                  key={item.id || `${item.latitude}-${item.longitude}`}
                  style={{
                    position: 'absolute',
                    top: `${yPct}%`,
                    left: `${xPct}%`,
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#ea580c',
                    border: '1.5px solid #ffffff',
                    transform: 'translate(-50%, -50%)',
                    cursor: 'pointer',
                    pointerEvents: 'auto',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                    zIndex: 6,
                  }}
                  title={`Historical Landslide: ${item.district || 'Uttarakhand'} (${item.movementType || 'Slide'})`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveMarker({ ...item, category: 'landslide' });
                    if (onLandslideClick) onLandslideClick(item);
                    if (onLocationSelect) {
                      onLocationSelect({
                        latitude: item.latitude,
                        longitude: item.longitude,
                        isInside: true,
                        landslide: item,
                      });
                    }
                  }}
                />
              );
            })}
          </div>
        )}

        {/* Emergency Resources markers on fallback canvas */}
        {resources && resources.length > 0 && (
          <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
            {resources.map((res) => {
              const yPct = ((UTTARAKHAND_ENVELOPE.MAX_LAT - res.latitude) / (UTTARAKHAND_ENVELOPE.MAX_LAT - UTTARAKHAND_ENVELOPE.MIN_LAT)) * 100;
              const xPct = ((res.longitude - UTTARAKHAND_ENVELOPE.MIN_LON) / (UTTARAKHAND_ENVELOPE.MAX_LON - UTTARAKHAND_ENVELOPE.MIN_LON)) * 100;
              if (yPct < 0 || yPct > 100 || xPct < 0 || xPct > 100) return null;

              return (
                <div
                  key={res.id || `${res.latitude}-${res.longitude}`}
                  style={{
                    position: 'absolute',
                    top: `${yPct}%`,
                    left: `${xPct}%`,
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor: res.type === 'HOSPITAL' ? '#059669' : '#0284c7',
                    border: '1.5px solid #ffffff',
                    transform: 'translate(-50%, -50%)',
                    cursor: 'pointer',
                    pointerEvents: 'auto',
                    boxShadow: '0 1px 4px rgba(0,0,0,0.4)',
                    zIndex: 9,
                  }}
                  title={`${res.name} (${res.type || 'Facility'}) — Demo data`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveMarker({ ...res, category: 'resource' });
                    if (onResourceClick) onResourceClick(res);
                  }}
                />
              );
            })}
          </div>
        )}
      </div>

      {/* Marker detail popup on fallback */}
      {activeMarker && (
        <div
          style={{
            position: 'absolute',
            bottom: '4.5rem',
            left: '50%',
            transform: 'translateX(-50%)',
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem 1rem',
            boxShadow: 'var(--shadow-lg)',
            zIndex: 25,
            minWidth: '220px',
            color: 'var(--text-primary)',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
            <span style={{ fontWeight: 700, fontSize: '0.825rem', color: activeMarker.category === 'resource' ? '#0284c7' : '#0f766e' }}>
              {activeMarker.category === 'resource' ? activeMarker.name : 'Historical Landslide'}
            </span>
            <button
              type="button"
              onClick={() => setActiveMarker(null)}
              style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.9rem' }}
            >
              &times;
            </button>
          </div>
          {activeMarker.category === 'resource' ? (
            <>
              <div style={{ fontSize: '0.78rem' }}><strong>Type:</strong> {activeMarker.type || 'Facility'}</div>
              <div style={{ fontSize: '0.72rem', color: '#d97706', marginTop: '0.2rem', fontWeight: 600 }}>Demo emergency resource data</div>
            </>
          ) : (
            <>
              <div style={{ fontSize: '0.78rem', marginBottom: '0.15rem' }}>
                <strong>District:</strong> {activeMarker.district || 'Chamoli'}
              </div>
              <div style={{ fontSize: '0.78rem', marginBottom: '0.15rem' }}>
                <strong>Type:</strong> {activeMarker.movementType || 'Slide'}
              </div>
            </>
          )}
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            <strong>Location:</strong> {activeMarker.latitude?.toFixed(4)}°N, {activeMarker.longitude?.toFixed(4)}°E
          </div>
        </div>
      )}

      {showLayers && (
        <div onClick={(e) => e.stopPropagation()}>
          <LayerControl activeLayers={activeLayers} onToggleLayer={onToggleLayer} />
        </div>
      )}

      {showLegend && (
        <div onClick={(e) => e.stopPropagation()}>
          <MapLegend />
        </div>
      )}

      <div
        style={{ position: 'absolute', bottom: '1.5rem', left: '1rem', zIndex: 15 }}
        onClick={(e) => e.stopPropagation()}
      >
        <LocationButton onLocationFound={onLocationFound} />
      </div>
    </div>
  );
}
