import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { EmptyState } from '../components/feedback/EmptyState';
import { UnsupportedLocation } from '../components/feedback/UnsupportedLocation';
import { DemoDataNotice } from '../components/feedback/DemoDataNotice';
import { RiskBadge } from '../components/common/RiskBadge';

describe('Data Quality UX & Feedback Components (Phase 10)', () => {
  it('renders LoadingState with custom message', () => {
    render(<LoadingState message="Fetching sensor telemetry..." />);
    expect(screen.getByText('Fetching sensor telemetry...')).toBeInTheDocument();
  });

  it('renders ErrorState with title, message, and retry button', () => {
    const handleRetry = () => {};
    render(<ErrorState title="Gateway Timeout" message="Failed to connect" onRetry={handleRetry} />);
    expect(screen.getByText('Gateway Timeout')).toBeInTheDocument();
    expect(screen.getByText('Failed to connect')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('renders EmptyState with title', () => {
    render(<EmptyState title="No Landslides Found" />);
    expect(screen.getByText('No Landslides Found')).toBeInTheDocument();
  });

  it('renders UnsupportedLocation with coordinates and blocked evaluation notice', () => {
    render(<UnsupportedLocation latitude={29.580286} longitude={82.808874} />);
    expect(screen.getByText('Unsupported Geographic Coordinate')).toBeInTheDocument();
    expect(screen.getByText(/29.580286, 82.808874/)).toBeInTheDocument();
    expect(screen.getByText(/Evaluation Blocked/i)).toBeInTheDocument();
  });

  it('renders DemoDataNotice clearly stating synthetic development data', () => {
    render(<DemoDataNotice entity="Emergency Facilities" />);
    expect(screen.getByRole('note')).toBeInTheDocument();
    expect(screen.getByText(/contains synthetic development records/i)).toBeInTheDocument();
    expect(screen.getByText(/does not represent real emergency facilities/i)).toBeInTheDocument();
  });

  it('renders accessible RiskBadge for all risk levels without relying on color alone', () => {
    const { rerender } = render(<RiskBadge levelOrScore="LOW" />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', expect.stringContaining('Low Risk'));
    expect(screen.getByText('LOW RISK')).toBeInTheDocument();

    rerender(<RiskBadge levelOrScore="CRITICAL" />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', expect.stringContaining('Critical Risk'));
    expect(screen.getByText('CRITICAL RISK')).toBeInTheDocument();
  });
});
