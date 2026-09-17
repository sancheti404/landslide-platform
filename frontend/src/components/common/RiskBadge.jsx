import React from 'react';
import { getRiskLevelConfig } from '../../constants/riskLevels';
import { ShieldCheck, AlertTriangle, AlertOctagon, ShieldAlert } from 'lucide-react';

/**
 * Accessible Risk Badge
 * Never relies on color alone: renders distinct iconography, textual category, and border styling.
 */
export function RiskBadge({ levelOrScore, size = 'md', showScore = false, score = null }) {
  const config = getRiskLevelConfig(levelOrScore);

  const icons = {
    LOW: <ShieldCheck size={size === 'sm' ? 13 : 15} aria-hidden="true" />,
    MODERATE: <AlertTriangle size={size === 'sm' ? 13 : 15} aria-hidden="true" />,
    HIGH: <AlertOctagon size={size === 'sm' ? 13 : 15} aria-hidden="true" />,
    CRITICAL: <ShieldAlert size={size === 'sm' ? 13 : 15} aria-hidden="true" />,
  };

  const currentScore = score !== null ? score : (typeof levelOrScore === 'number' ? levelOrScore : null);

  return (
    <span
      role="status"
      aria-label={`Risk Level: ${config.label}${currentScore !== null ? ` (Score: ${currentScore.toFixed(4)})` : ''}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        padding: size === 'sm' ? '0.15rem 0.55rem' : '0.25rem 0.7rem',
        fontSize: size === 'sm' ? '0.75rem' : '0.825rem',
        fontWeight: 700,
        borderRadius: 'var(--radius-full)',
        backgroundColor: config.bgColor,
        color: config.color,
        border: `1px solid ${config.borderColor}`,
        letterSpacing: '0.02em',
      }}
    >
      {icons[config.key]}
      <span>{config.label.toUpperCase()}</span>
      {showScore && currentScore !== null && (
        <span style={{ opacity: 0.85, fontWeight: 600 }}>
          ({currentScore.toFixed(3)})
        </span>
      )}
    </span>
  );
}
