import { getRiskLevelConfig } from '../constants/riskLevels';

/**
 * Returns complete risk level attributes and textual explanation
 */
export function evaluateRiskContext(score, triggerIndicator) {
  const config = getRiskLevelConfig(score);

  let guidance = 'Standard monitoring conditions. Regular slope inspection intervals apply.';
  if (config.key === 'CRITICAL') {
    guidance = 'CRITICAL: Severe risk triggered. Alert emergency operations center, prepare early warning advisories, and verify local shelter availability.';
  } else if (config.key === 'HIGH') {
    guidance = 'HIGH: Elevated risk detected. Reinforce real-time telemetry observation and restrict vehicular traffic on vulnerable cut-slopes.';
  } else if (config.key === 'MODERATE') {
    guidance = 'MODERATE: Heightened monitoring recommended. Track antecedent precipitation accumulation across the next 24–48 hours.';
  }

  return {
    ...config,
    score: typeof score === 'number' ? score : 0,
    triggerIndicator: triggerIndicator || 'NORMAL',
    guidance,
  };
}
