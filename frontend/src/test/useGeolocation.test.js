import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useGeolocation } from '../hooks/useGeolocation';

describe('useGeolocation Hook (Phase 8)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('does NOT request location automatically upon initial mount', () => {
    const mockGetCurrentPosition = vi.fn();
    globalThis.navigator.geolocation = {
      getCurrentPosition: mockGetCurrentPosition,
    };

    const { result } = renderHook(() => useGeolocation());
    expect(result.current.location).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(mockGetCurrentPosition).not.toHaveBeenCalled();
  });

  it('successfully retrieves location and flags coordinate inside Uttarakhand', () => {
    const mockPosition = {
      coords: {
        latitude: 30.529505,
        longitude: 79.085957,
        accuracy: 10,
      },
      timestamp: 1234567890,
    };

    globalThis.navigator.geolocation = {
      getCurrentPosition: vi.fn((success) => success(mockPosition)),
    };

    const { result } = renderHook(() => useGeolocation());

    act(() => {
      result.current.requestLocation();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.location.latitude).toBe(30.529505);
    expect(result.current.isInsideUttarakhand).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('handles permission denied error gracefully', () => {
    const mockError = {
      code: 1, // PERMISSION_DENIED
      PERMISSION_DENIED: 1,
      POSITION_UNAVAILABLE: 2,
      TIMEOUT: 3,
      message: 'User denied geolocation prompt',
    };

    globalThis.navigator.geolocation = {
      getCurrentPosition: vi.fn((_, error) => error(mockError)),
    };

    const { result } = renderHook(() => useGeolocation());

    act(() => {
      result.current.requestLocation();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.location).toBeNull();
    expect(result.current.error.code).toBe('PERMISSION_DENIED');
  });

  it('detects coordinates outside Uttarakhand and warns the user without crashing', () => {
    const mockPosition = {
      coords: {
        latitude: 28.6139, // Delhi (outside UK envelope)
        longitude: 77.2090,
        accuracy: 15,
      },
      timestamp: 1234567890,
    };

    globalThis.navigator.geolocation = {
      getCurrentPosition: vi.fn((success) => success(mockPosition)),
    };

    const { result } = renderHook(() => useGeolocation());

    act(() => {
      result.current.requestLocation();
    });

    expect(result.current.isInsideUttarakhand).toBe(false);
    expect(result.current.error.code).toBe('OUTSIDE_OPERATIONAL_ENVELOPE');
  });
});
