import { useState, useEffect } from 'react';
import { getStateBoundary, getDistrictSummary } from '../services/gisApi';

/**
 * Hook to fetch and cache state boundary and district summaries
 */
export function useGisLayers() {
  const [boundary, setBoundary] = useState(null);
  const [districtSummary, setDistrictSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        setLoading(true);
        const [boundaryData, summaryData] = await Promise.allSettled([
          getStateBoundary(),
          getDistrictSummary(),
        ]);

        if (isMounted) {
          if (boundaryData.status === 'fulfilled') {
            setBoundary(boundaryData.value);
          }
          if (summaryData.status === 'fulfilled') {
            setDistrictSummary(summaryData.value);
          }
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          setError(err);
          setLoading(false);
        }
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, []);

  return { boundary, districtSummary, loading, error };
}
