import { describe, it, expect } from 'vitest';
import { isWithinUttarakhand, validateCoordinates } from '../utils/geoValidators';

describe('Geographic Boundary Validation (Uttarakhand Operational Envelope)', () => {
  it('accepts valid coordinates inside Uttarakhand envelope [28.50-31.60°N, 77.40-81.30°E]', () => {
    // Benchmark Kedarnath / Badrinath
    expect(isWithinUttarakhand(30.529505, 79.085957)).toBe(true);
    // Dehradun
    expect(isWithinUttarakhand(30.3165, 78.0322)).toBe(true);
    // Boundary corners
    expect(isWithinUttarakhand(28.50, 77.40)).toBe(true);
    expect(isWithinUttarakhand(31.60, 81.30)).toBe(true);
  });

  it('rejects the discovered bug coordinate (Lat 29.580286, Lon 82.808874) with longitude > 81.30', () => {
    expect(isWithinUttarakhand(29.580286, 82.808874)).toBe(false);
    const result = validateCoordinates(29.580286, 82.808874);
    expect(result.isValid).toBe(false);
    expect(result.reason).toBe('OUTSIDE_OPERATIONAL_ENVELOPE');
  });

  it('rejects coordinates south of latitude 28.50 (e.g. Delhi, 28.6139, 77.2090)', () => {
    expect(isWithinUttarakhand(28.49, 79.00)).toBe(false);
    const result = validateCoordinates(28.49, 79.00);
    expect(result.isValid).toBe(false);
  });

  it('rejects coordinates north of latitude 31.60', () => {
    expect(isWithinUttarakhand(31.61, 79.00)).toBe(false);
  });

  it('rejects invalid or non-numeric values', () => {
    expect(isWithinUttarakhand('invalid', 79.0)).toBe(false);
    expect(isWithinUttarakhand(NaN, 79.0)).toBe(false);
    expect(isWithinUttarakhand(null, null)).toBe(false);
    const result = validateCoordinates('not_a_number', 'also_not');
    expect(result.isValid).toBe(false);
    expect(result.reason).toBe('INVALID_NUMBERS');
  });
});
