import React, { useState, useEffect } from 'react';
import { getNearbyInfrastructure } from '../../services/infrastructureApi';
import { Card } from '../../components/common/Card';
import { Table, TableRow, TableCell } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { DemoDataNotice } from '../../components/feedback/DemoDataNotice';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Shield, Hospital, Home, Search } from 'lucide-react';

export function Resources() {
  const [latitude, setLatitude] = useState('30.529505');
  const [longitude, setLongitude] = useState('79.085957');
  const [distance, setDistance] = useState('10000'); // 10km
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasQueried, setHasQueried] = useState(false);

  const fetchResources = async () => {
    try {
      setLoading(true);
      const res = await getNearbyInfrastructure({
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        distance: parseFloat(distance),
      });
      setItems(res || []);
      setHasQueried(true);
    } catch (e) {
      console.error('Failed to fetch infrastructure:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
  }, []);

  return (
    <div style={{ maxWidth: 'var(--max-content-width)', margin: '0 auto', padding: '1.5rem 1.75rem', width: '100%' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.25rem', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Emergency & Evacuation
            </h1>
            <Badge variant="warning">Development / Demo Infrastructure Data</Badge>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            PostGIS ST_DWithin spatial query engine identifying medical and shelter infrastructure within emergency proximity.
          </p>
        </div>
      </div>

      <div style={{ marginBottom: '1.25rem' }}>
        <DemoDataNotice entity="Emergency facilities and civil protection infrastructure" />
      </div>

      {/* Query Filter */}
      <Card style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'flex-end' }}>
          <div style={{ flex: '1 1 180px' }}>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem', fontWeight: 600 }}>
              Latitude (°N)
            </label>
            <input
              type="number"
              step="any"
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ flex: '1 1 180px' }}>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem', fontWeight: 600 }}>
              Longitude (°E)
            </label>
            <input
              type="number"
              step="any"
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ flex: '1 1 180px' }}>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem', fontWeight: 600 }}>
              Radius (Meters)
            </label>
            <input
              type="number"
              step="1000"
              value={distance}
              onChange={(e) => setDistance(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>

          <Button variant="primary" size="md" onClick={fetchResources} loading={loading} icon={<Search size={14} />}>
            Search Facilities
          </Button>
        </div>
      </Card>

      {/* Facilities List */}
      <Card title={`Nearby Infrastructure Records (${items.length} Found)`}>
        {loading && <LoadingSpinner label="Querying PostGIS spatial proximity..." />}

        {!loading && items.length === 0 && hasQueried && (
          <div style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
            No infrastructure records found within {Number(distance) / 1000} km of the specified coordinate.
          </div>
        )}

        {!loading && items.length > 0 && (
          <Table headers={['Facility Name', 'Type', 'Coordinates', 'Capacity', 'Operational Status']}>
            {items.map((row) => (
              <TableRow key={row.id}>
                <TableCell style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {row.name}
                </TableCell>
                <TableCell>
                  <Badge variant={row.type === 'HOSPITAL' ? 'success' : 'info'}>
                    {row.type}
                  </Badge>
                </TableCell>
                <TableCell>
                  <span className="font-mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {row.latitude?.toFixed(4)}, {row.longitude?.toFixed(4)}
                  </span>
                </TableCell>
                <TableCell style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                  {row.capacity ? `${row.capacity} Beds` : 'Standard'}
                </TableCell>
                <TableCell>
                  <Badge variant="warning">DEMO RECORD</Badge>
                </TableCell>
              </TableRow>
            ))}
          </Table>
        )}
      </Card>
    </div>
  );
}
