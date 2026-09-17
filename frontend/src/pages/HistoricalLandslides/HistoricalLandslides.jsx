import React, { useState, useEffect } from 'react';
import { getHistoricalLandslides, getDistrictSummary } from '../../services/gisApi';
import { Card } from '../../components/common/Card';
import { Table, TableRow, TableCell } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorState } from '../../components/feedback/ErrorState';
import { Database, Filter, Search, RotateCcw } from 'lucide-react';

export function HistoricalLandslides() {
  const [landslides, setLandslides] = useState([]);
  const [districtSummary, setDistrictSummary] = useState(null);
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [movementType, setMovementType] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLandslides = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getHistoricalLandslides({
        district: selectedDistrict || undefined,
        movementType: movementType || undefined,
        limit: 100,
      });
      setLandslides(data || []);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getDistrictSummary().then((sum) => setDistrictSummary(sum || {}));
    fetchLandslides();
  }, [selectedDistrict]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchLandslides();
  };

  const handleReset = () => {
    setSelectedDistrict('');
    setMovementType('');
    fetchLandslides();
  };

  return (
    <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto', padding: '1.5rem 1.75rem', width: '100%' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.5rem', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Landslide History
            </h1>
            <Badge variant="default">GSI NLSM Inventory — 5,523 records</Badge>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Authentic Geological Survey of India (GSI) National Landslide Susceptibility Mapping (NLSM) records mapped across Uttarakhand.
          </p>
        </div>
      </div>

      {/* District Summary Pills */}
      {districtSummary && (
        <Card title="District Landslide Density Breakdown" style={{ marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.25rem' }}>
            {Object.entries(districtSummary)
              .filter(([_, count]) => count > 10)
              .map(([dist, count]) => {
                const isSelected = selectedDistrict.toLowerCase() === dist.toLowerCase();
                return (
                  <button
                    key={dist}
                    type="button"
                    onClick={() => setSelectedDistrict(isSelected ? '' : dist)}
                    style={{
                      background: isSelected ? '#0f766e' : '#f1f5f9',
                      border: `1px solid ${isSelected ? '#0d655e' : '#cbd5e1'}`,
                      borderRadius: 'var(--radius-full)',
                      padding: '0.25rem 0.65rem',
                      fontSize: '0.75rem',
                      color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      fontWeight: 600,
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {dist}: <span style={{ opacity: 0.9 }}>{count}</span>
                  </button>
                );
              })}
          </div>
        </Card>
      )}

      {/* Filter Bar */}
      <Card style={{ marginBottom: '1.25rem' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'flex-end' }}>
          <div style={{ flex: '1 1 200px' }}>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem', fontWeight: 600 }}>
              District Filter
            </label>
            <input
              type="text"
              placeholder="e.g. Chamoli, Rudraprayag, Nainital"
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ flex: '1 1 200px' }}>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem', fontWeight: 600 }}>
              Movement Type
            </label>
            <input
              type="text"
              placeholder="e.g. Debris Slide, Rock Fall"
              value={movementType}
              onChange={(e) => setMovementType(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Button type="submit" variant="primary" size="md" icon={<Search size={14} />}>
              Filter Records
            </Button>
            <Button type="button" variant="secondary" size="md" onClick={handleReset} icon={<RotateCcw size={14} />}>
              Reset
            </Button>
          </div>
        </form>
      </Card>

      {/* Results Table */}
      <Card title={`Inventory Records (Showing ${landslides.length} entries)`}>
        {loading && <LoadingSpinner label="Loading recorded landslides..." />}

        {error && (
          <ErrorState
            title="Failed to Load Historical Records"
            message={error.message || 'Unable to retrieve inventory records from backend.'}
            onRetry={fetchLandslides}
          />
        )}

        {!loading && !error && landslides.length === 0 && (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            No historical landslides found matching the selected filters.
          </div>
        )}

        {!loading && !error && landslides.length > 0 && (
          <Table headers={['Slide No', 'District', 'Movement Type', 'Material Involved', 'Coordinates', 'Occurrence History']}>
            {landslides.map((row) => (
              <TableRow key={row.id}>
                <TableCell>
                  <span className="font-mono" style={{ fontWeight: 700, color: '#0f766e', fontSize: '0.78rem' }}>
                    {row.slideNo || `GSI-${row.id}`}
                  </span>
                </TableCell>
                <TableCell style={{ fontWeight: 600 }}>{row.district || '—'}</TableCell>
                <TableCell>
                  <Badge variant="default">{row.movementType || 'Unclassified'}</Badge>
                </TableCell>
                <TableCell style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  {row.materialInvolved || '—'}
                </TableCell>
                <TableCell>
                  <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {row.latitude?.toFixed(4)}, {row.longitude?.toFixed(4)}
                  </span>
                </TableCell>
                <TableCell style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {row.history || 'Historical Record'}
                </TableCell>
              </TableRow>
            ))}
          </Table>
        )}
      </Card>
    </div>
  );
}
