/**
 * Operational Risk Levels and Multi-modal ML Classification
 */
export const RISK_LEVELS = {
  LOW: {
    key: 'LOW',
    label: 'Low Risk',
    scoreRange: [0.0, 0.35],
    color: '#059669',
    bgColor: '#ecfdf5',
    borderColor: '#a7f3d0',
    description: 'Slopes exhibit low susceptibility and rainfall remains beneath dynamic trigger thresholds.',
  },
  MODERATE: {
    key: 'MODERATE',
    label: 'Moderate Risk',
    scoreRange: [0.35, 0.65],
    color: '#d97706',
    bgColor: '#fffbeb',
    borderColor: '#fde68a',
    description: 'Noticeable terrain susceptibility or moderate antecedent rainfall accumulation detected.',
  },
  HIGH: {
    key: 'HIGH',
    label: 'High Risk',
    scoreRange: [0.65, 0.85],
    color: '#ea580c',
    bgColor: '#fff7ed',
    borderColor: '#fed7aa',
    description: 'Elevated operational risk indicating potential slope instability under current stress conditions.',
  },
  CRITICAL: {
    key: 'CRITICAL',
    label: 'Critical Risk',
    scoreRange: [0.85, 1.0],
    color: '#dc2626',
    bgColor: '#fef2f2',
    borderColor: '#fecaca',
    description: 'Severe operational susceptibility compounded with intense antecedent rainfall trigger. Immediate vigilance required.',
  }
};

/**
 * Returns the corresponding risk configuration from a score or level name
 */
export function getRiskLevelConfig(levelOrScore) {
  if (typeof levelOrScore === 'string') {
    const key = levelOrScore.toUpperCase();
    if (key === 'MEDIUM') return RISK_LEVELS.MODERATE;
    return RISK_LEVELS[key] || RISK_LEVELS.LOW;
  }
  
  if (typeof levelOrScore === 'number') {
    if (levelOrScore >= 0.85) return RISK_LEVELS.CRITICAL;
    if (levelOrScore >= 0.65) return RISK_LEVELS.HIGH;
    if (levelOrScore >= 0.35) return RISK_LEVELS.MODERATE;
    return RISK_LEVELS.LOW;
  }

  return RISK_LEVELS.LOW;
}
