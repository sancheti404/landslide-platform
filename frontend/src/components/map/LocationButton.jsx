import React from 'react';
import { Navigation, Loader2 } from 'lucide-react';
import { useGeolocation } from '../../hooks/useGeolocation';
import { Button } from '../common/Button';

/**
 * Phase 8: Reusable "Use My Location" button.
 * Only requests browser geolocation upon explicit click.
 * Validates whether the obtained location is inside the Uttarakhand operational envelope.
 */
export function LocationButton({ onLocationFound, className = '', variant = 'secondary' }) {
  const { location, loading, error, isInsideUttarakhand, requestLocation } = useGeolocation();

  const handleClick = () => {
    requestLocation();
  };

  React.useEffect(() => {
    if (location && onLocationFound) {
      onLocationFound({
        latitude: location.latitude,
        longitude: location.longitude,
        accuracy: location.accuracy,
        isInsideUttarakhand,
      });
    }
  }, [location, isInsideUttarakhand, onLocationFound]);

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'flex-start' }}>
      <Button
        variant={variant}
        size="sm"
        onClick={handleClick}
        disabled={loading}
        icon={loading ? <Loader2 size={14} className="animate-spin" /> : <Navigation size={14} />}
        className={className}
        title="Acquire current device coordinates via browser geolocation"
      >
        {loading ? 'Locating...' : 'Use My Location'}
      </Button>

      {error && (
        <div
          role="alert"
          style={{
            marginTop: '0.4rem',
            fontSize: '0.72rem',
            color: '#f87171',
            maxWidth: '260px',
            lineHeight: 1.3,
          }}
        >
          {error.message}
        </div>
      )}
    </div>
  );
}
