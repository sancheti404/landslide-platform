/**
 * Formatting utility functions
 */

export function formatCoordinate(val, decimals = 5) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return Number(val).toFixed(decimals);
}

export function formatScore(score, decimals = 4) {
  if (score === null || score === undefined || isNaN(score)) return '—';
  return Number(score).toFixed(decimals);
}

export function formatPercentage(val, decimals = 1) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return `${(Number(val) * 100).toFixed(decimals)}%`;
}

export function formatRainfallMm(val) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return `${Number(val).toFixed(1)} mm`;
}

export function formatLatency(ms) {
  if (ms === null || ms === undefined || isNaN(ms)) return '—';
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

export function formatIsoDate(isoString) {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return isoString;
  }
}
