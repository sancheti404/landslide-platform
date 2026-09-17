import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiRequest } from '../services/api';

describe('Centralized API Service (Spring Boot Gateway)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('successfully handles 200 OK responses with JSON data', async () => {
    const mockData = { status: 'success', score: 0.95 };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => mockData,
    });

    const result = await apiRequest('/api/risk/ml-health');
    expect(result).toEqual(mockData);
    expect(globalThis.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/risk/ml-health'), expect.any(Object));
  });

  it('normalizes HTTP 400 UNSUPPORTED_LOCATION errors and sets isUnsupportedLocation flag', async () => {
    const errorBody = {
      error: 'UNSUPPORTED_LOCATION',
      message: 'Requested location is outside reliable terrain feature coverage.',
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      headers: { get: () => 'application/json' },
      json: async () => errorBody,
    });

    await expect(apiRequest('/api/risk/assess')).rejects.toThrow(
      'Requested location is outside reliable terrain feature coverage.'
    );

    try {
      await apiRequest('/api/risk/assess');
    } catch (err) {
      expect(err.status).toBe(400);
      expect(err.isUnsupportedLocation).toBe(true);
      expect(err.data).toEqual(errorBody);
    }
  });

  it('handles network failure or backend unavailability', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'));

    await expect(apiRequest('/api/health')).rejects.toThrow('Failed to fetch');
  });
});
