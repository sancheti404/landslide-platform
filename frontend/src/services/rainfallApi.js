import { apiRequest } from './api';

/**
 * Service module for CHIRPS rainfall monitoring
 * Currently operational rainfall features are returned via POST /api/risk/assess.
 * Dedicated rainfall time-series queries are defined here for future backend extensions.
 */

export async function getRainfallGridSummary() {
  // Future endpoint placeholder as documented in Phase 6
  return {
    source: 'UCSB CHIRPS v2.0',
    resolution: '0.05° (~5.5 km)',
    coverage: 'Uttarakhand State',
    temporalRange: '2013-2023 Gridded Daily Cache',
    status: 'OPERATIONAL_CACHED',
    notice: 'Antecedent rainfall metrics (3d, 7d, 14d, 30d) are computed on-demand via the multimodal assessment gateway.',
  };
}
