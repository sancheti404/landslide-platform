import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Provide default mock fetch for test environment
if (!globalThis.fetch || !globalThis.fetch._isMockFunction) {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = vi.fn().mockImplementation((url, options) => {
    return Promise.resolve({
      ok: true,
      status: 200,
      headers: { get: () => 'application/json' },
      json: async () => ({
        status: 'healthy',
        operational_landslide_risk_score: 0.5,
        risk_level: 'MODERATE',
        xgboost_probability: 0.5,
        swin_probability: 0.5,
        static_visual_fusion_score: 0.5,
        dynamic_rainfall_trigger_score: 0.5,
        trigger_indicator: 'NORMAL',
        rainfall_3d_mm: 10,
        rainfall_7d_mm: 20,
        rainfall_14d_mm: 30,
        rainfall_30d_mm: 40,
        layers: [],
      }),
      text: async () => JSON.stringify({ status: 'healthy' }),
    });
  });
}
