import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Rectangle,
  useMap,
  useMapEvents,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MAP_CONFIG } from '../../constants/mapConfig';
import { UTTARAKHAND_ENVELOPE } from '../../constants/geographicBounds';
import { isWithinUttarakhand } from '../../utils/geoValidators';
import { MapControls } from './MapControls';
import { MapLegend } from './MapLegend';
import { LayerControl } from './LayerControl';
import { LocationButton } from './LocationButton';

// Custom SVG-based Leaflet DivIcons (pure CSS/SVG - no missing PNG assets)
const selectedLocationIcon = L.divIcon({
  className: 'custom-map-marker-selected',
  html: `
    <div style="display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%);">
      <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 2px 5px rgba(220, 38, 38, 0.45));">
        <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0Z"/>
        <circle cx="12" cy="10" r="3" fill="#dc2626"/>
      </svg>
    </div>
  `,
  iconSize: [30, 30],
  iconAnchor: [15, 30],
  popupAnchor: [0, -30],
});

const destinationIcon = L.divIcon({
  className: 'custom-map-marker-destination',
  html: `
    <div style="display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%);">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 2px 5px rgba(220, 38, 38, 0.5));">
        <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
        <line x1="4" x2="4" y1="22" y2="15"/>
      </svg>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -28],
});

const landslideIcon = L.divIcon({
  className: 'custom-map-marker-landslide',
  html: `
    <div style="
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background-color: #ea580c;
      border: 2px solid #ffffff;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
      cursor: pointer;
    "></div>
  `,
  iconSize: [10, 10],
  iconAnchor: [5, 5],
  popupAnchor: [0, -5],
});

const hospitalIcon = L.divIcon({
  className: 'custom-map-marker-hospital',
  html: `
    <div style="
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background-color: #059669;
      border: 2px solid #ffffff;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
      cursor: pointer;
    "></div>
  `,
  iconSize: [12, 12],
  iconAnchor: [6, 6],
  popupAnchor: [0, -6],
});

const resourceIcon = L.divIcon({
  className: 'custom-map-marker-resource',
  html: `
    <div style="
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background-color: #0284c7;
      border: 2px solid #ffffff;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
      cursor: pointer;
    "></div>
  `,
  iconSize: [12, 12],
  iconAnchor: [6, 6],
  popupAnchor: [0, -6],
});

// Reference risk zones for demonstration (Alaknanda, Mandakini corridors)
const REFERENCE_RISK_ZONES = [
  {
    id: 'ref-zone-1',
    name: 'Mandakini Valley Corridor (Reference Zone)',
    bounds: [[30.45, 78.95], [30.75, 79.18]],
    color: '#ea580c',
  },
  {
    id: 'ref-zone-2',
    name: 'Alaknanda Gorge Sector (Reference Zone)',
    bounds: [[30.38, 79.35], [30.65, 79.62]],
    color: '#dc2626',
  },
  {
    id: 'ref-zone-3',
    name: 'Kumaon Foothill Fault Zone (Reference Zone)',
    bounds: [[29.30, 79.35], [29.50, 79.60]],
    color: '#d97706',
  },
];

/**
 * MapEventsHandler: captures click coordinates on Leaflet canvas
 */
function MapEventsHandler({ onLocationSelect }) {
  useMapEvents({
    click(e) {
      if (!onLocationSelect) return;
      const lat = e.latlng?.lat ?? e.lat;
      const lng = e.latlng?.lng ?? e.lng;
      if (lat == null || lng == null) return;
      onLocationSelect({
        latitude: parseFloat(Number(lat).toFixed(6)),
        longitude: parseFloat(Number(lng).toFixed(6)),
        isInside: isWithinUttarakhand(lat, lng),
      });
    },
  });
  return null;
}

/**
 * MapController: binds map instance to ref and synchronizes selectedLocation
 */
function MapController({ selectedLocation, mapRef }) {
  const map = useMap();

  useEffect(() => {
    if (mapRef) {
      mapRef.current = map;
    }
  }, [map, mapRef]);

  useEffect(() => {
    if (selectedLocation?.latitude && selectedLocation?.longitude) {
      map.panTo([selectedLocation.latitude, selectedLocation.longitude], {
        animate: true,
      });
    }
  }, [selectedLocation?.latitude, selectedLocation?.longitude, map]);

  return null;
}

/**
 * MapView: Leaflet + OpenStreetMap map component for UK-LIP
 * Requires no Google Maps API key or proprietary service.
 */
export function MapView({
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
  const mapRef = useRef(null);

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

  const handleZoomIn = () => mapRef.current?.zoomIn();
  const handleZoomOut = () => mapRef.current?.zoomOut();
  const handleResetView = () => {
    if (mapRef.current) {
      mapRef.current.setView(
        [MAP_CONFIG.defaultCenter.lat, MAP_CONFIG.defaultCenter.lng],
        MAP_CONFIG.defaultZoom
      );
    }
  };

  const handleCenterLocation = () => {
    if (selectedLocation && mapRef.current) {
      mapRef.current.panTo([selectedLocation.latitude, selectedLocation.longitude]);
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
    if (mapRef.current) {
      mapRef.current.panTo([loc.latitude, loc.longitude]);
      mapRef.current.setZoom(11);
    }
  };

  const centerPos = selectedLocation
    ? [selectedLocation.latitude, selectedLocation.longitude]
    : [MAP_CONFIG.defaultCenter.lat, MAP_CONFIG.defaultCenter.lng];

  const operationalBounds = [
    [UTTARAKHAND_ENVELOPE.MIN_LAT, UTTARAKHAND_ENVELOPE.MIN_LON],
    [UTTARAKHAND_ENVELOPE.MAX_LAT, UTTARAKHAND_ENVELOPE.MAX_LON],
  ];

  return (
    <div className="map-container-root" style={{ height, position: 'relative' }}>
      <MapContainer
        center={centerPos}
        zoom={MAP_CONFIG.defaultZoom}
        minZoom={MAP_CONFIG.minZoom || 7}
        maxZoom={MAP_CONFIG.maxZoom || 18}
        zoomControl={false}
        attributionControl={true}
        style={{ width: '100%', height: '100%' }}
      >
        {/* OpenStreetMap Standard Tiles & Official Attribution */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        <MapEventsHandler onLocationSelect={onLocationSelect} />
        <MapController selectedLocation={selectedLocation} mapRef={mapRef} />

        {/* 1. Operational Area Boundary Envelope */}
        {activeLayers.operationalArea !== false && (
          <Rectangle
            bounds={operationalBounds}
            pathOptions={{
              color: '#0284c7',
              weight: 2,
              dashArray: '6, 6',
              fillColor: '#0284c7',
              fillOpacity: 0.04,
            }}
          >
            <Popup>
              <div style={{ fontSize: '0.8rem', color: '#0f172a' }}>
                <strong style={{ color: '#0284c7' }}>UK-LIP Operational Area</strong>
                <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem' }}>
                  Envelope: 28.50°N – 31.60°N, 77.40°E – 81.30°E
                </div>
              </div>
            </Popup>
          </Rectangle>
        )}

        {/* 2. Reference Risk Zones Layer */}
        {activeLayers.riskZones && REFERENCE_RISK_ZONES.map((zone) => (
          <Rectangle
            key={zone.id}
            bounds={zone.bounds}
            pathOptions={{
              color: zone.color,
              weight: 1.5,
              dashArray: '4, 4',
              fillColor: zone.color,
              fillOpacity: 0.12,
            }}
          >
            <Popup>
              <div style={{ fontSize: '0.8rem', color: '#0f172a' }}>
                <strong>{zone.name}</strong>
                <div style={{ fontSize: '0.72rem', color: '#d97706', marginTop: '0.2rem', fontWeight: 600 }}>
                  Demo reference zone
                </div>
                <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.15rem' }}>
                  Reference spatial zone for platform demonstration. Not an official government hazard declaration.
                </div>
              </div>
            </Popup>
          </Rectangle>
        ))}

        {/* 3. Historical Landslide Markers (GSI NLSM Records) */}
        {activeLayers.landslides !== false && landslides && landslides.map((item) => (
          <Marker
            key={item.id || `${item.latitude}-${item.longitude}`}
            position={[item.latitude, item.longitude]}
            icon={landslideIcon}
            eventHandlers={{
              click: () => {
                if (onLandslideClick) onLandslideClick(item);
                if (onLocationSelect) {
                  onLocationSelect({
                    latitude: item.latitude,
                    longitude: item.longitude,
                    isInside: true,
                    landslide: item,
                  });
                }
              },
            }}
          >
            <Popup>
              <div style={{ color: '#0f172a', padding: '0.15rem 0.25rem', minWidth: '170px' }}>
                <div style={{ fontWeight: 700, fontSize: '0.825rem', color: '#ea580c', marginBottom: '0.25rem' }}>
                  Recorded Landslide
                </div>
                <div style={{ fontSize: '0.75rem', marginBottom: '0.15rem' }}>
                  <strong>District:</strong> {item.district || 'Uttarakhand'}
                </div>
                <div style={{ fontSize: '0.75rem', marginBottom: '0.15rem' }}>
                  <strong>Movement:</strong> {item.movementType || 'Slide'}
                </div>
                {item.materialInvolved && (
                  <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: '0.15rem' }}>
                    <strong>Material:</strong> {item.materialInvolved}
                  </div>
                )}
                <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.25rem' }}>
                  {item.latitude?.toFixed(4)}°N, {item.longitude?.toFixed(4)}°E
                </div>
                <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                  GSI NLSM Inventory Record
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* 4. Emergency Resources Markers (Demo Facilities) */}
        {activeLayers.infrastructure !== false && resources && resources.map((res) => (
          <Marker
            key={res.id || `${res.latitude}-${res.longitude}`}
            position={[res.latitude, res.longitude]}
            icon={res.type === 'HOSPITAL' ? hospitalIcon : resourceIcon}
            eventHandlers={{
              click: () => {
                if (onResourceClick) onResourceClick(res);
              },
            }}
          >
            <Popup>
              <div style={{ color: '#0f172a', padding: '0.15rem 0.25rem', minWidth: '180px' }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', color: res.type === 'HOSPITAL' ? '#059669' : '#0284c7', marginBottom: '0.2rem' }}>
                  {res.name}
                </div>
                <div style={{ fontSize: '0.75rem', marginBottom: '0.2rem' }}>
                  <strong>Facility Type:</strong> {res.type || 'Emergency Resource'}
                </div>
                <div style={{ fontSize: '0.72rem', color: '#d97706', fontWeight: 600, marginTop: '0.2rem' }}>
                  Demo emergency resource data
                </div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem' }}>
                  {res.latitude?.toFixed(4)}°N, {res.longitude?.toFixed(4)}°E
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* 5. Destination Facility Marker (Emergency Route Planning) */}
        {destinationLocation && (
          <Marker
            position={[destinationLocation.latitude, destinationLocation.longitude]}
            icon={destinationIcon}
          >
            <Popup>
              <div style={{ color: '#0f172a', padding: '0.2rem', minWidth: '160px' }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#dc2626', marginBottom: '0.2rem' }}>
                  Destination Facility
                </div>
                <div style={{ fontSize: '0.78rem', fontWeight: 600 }}>{destinationLocation.name}</div>
                <div style={{ fontSize: '0.72rem', color: '#d97706', marginTop: '0.2rem', fontWeight: 600 }}>
                  Demo emergency resource data
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* 6. Selected Location Marker */}
        {selectedLocation && (
          <Marker
            position={[selectedLocation.latitude, selectedLocation.longitude]}
            icon={selectedLocationIcon}
          >
            <Popup>
              <div style={{ color: '#0f172a', padding: '0.2rem', minWidth: '170px' }}>
                <div style={{ fontWeight: 700, fontSize: '0.825rem', color: '#dc2626', marginBottom: '0.25rem' }}>
                  Selected Location
                </div>
                <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#0f172a' }}>
                  {selectedLocation.latitude.toFixed(4)}°N, {selectedLocation.longitude.toFixed(4)}°E
                </div>
                <div style={{ fontSize: '0.72rem', marginTop: '0.25rem' }}>
                  {selectedLocation.isInside ? (
                    <span style={{ color: '#059669', fontWeight: 600 }}>Inside UK-LIP operational area</span>
                  ) : (
                    <span style={{ color: '#dc2626', fontWeight: 600 }}>Outside UK-LIP area</span>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {children}
      </MapContainer>

      {/* Floating Map Controls */}
      <MapControls
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onResetView={handleResetView}
        onCenterLocation={handleCenterLocation}
        hasLocation={!!selectedLocation}
      />

      {/* Layer Control Drawer */}
      {showLayers && (
        <LayerControl activeLayers={activeLayers} onToggleLayer={toggleLayer} />
      )}

      {/* Map Legend */}
      {showLegend && <MapLegend />}

      {/* Floating Geolocation Button */}
      <div style={{ position: 'absolute', bottom: '1.5rem', left: '1rem', zIndex: 1000 }}>
        <LocationButton onLocationFound={handleLocationFound} />
      </div>
    </div>
  );
}

export default MapView;
