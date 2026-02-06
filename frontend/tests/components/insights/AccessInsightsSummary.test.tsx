import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AccessInsightsSummary } from '@/components/insights/AccessInsightsSummary';
import type { Hospital } from '@/app/api/hospitals/route';

const mockHospitals: Hospital[] = [
  {
    id: 'ca-on-ottawa-civic',
    name: 'Ottawa Civic Hospital',
    province: 'ON',
    city: 'Ottawa',
    latitude: 45.3977,
    longitude: -75.7540,
    current_wait_time: 120,
    last_updated: '2024-01-01T12:00:00Z',
    is_verified: true,
    is_visible: true,
    source_id: 'ontario-hqo',
  },
  {
    id: 'ca-on-ottawa-general',
    name: 'Ottawa General Hospital',
    province: 'ON',
    city: 'Ottawa',
    latitude: 45.4111,
    longitude: -75.6802,
    current_wait_time: 90,
    last_updated: '2024-01-01T12:00:00Z',
    is_verified: true,
    is_visible: true,
    source_id: 'ontario-hqo',
  },
];

describe('AccessInsightsSummary', () => {
  it('renders location prompt when userLocation is null', () => {
    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={null}
        province="ON"
      />
    );

    expect(screen.getByText(/enable location access/i)).toBeInTheDocument();
  });

  it('displays statistics when userLocation is provided', () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 }; // Downtown Ottawa

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="ON"
      />
    );

    // Should show stats
    expect(screen.getByText(/ERs Within 30km/i)).toBeInTheDocument();
    expect(screen.getByText(/Avg Access Cost/i)).toBeInTheDocument();
    expect(screen.getByText(/Nearest ER/i)).toBeInTheDocument();
  });

  it('displays disclaimer message', () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 };

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="ON"
      />
    );

    expect(screen.getByText(/Never delay care for cost/i)).toBeInTheDocument();
    expect(screen.getByText(/Call 911 for emergencies/i)).toBeInTheDocument();
  });

  it('calculates hospitals within 30km correctly', () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 };

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="ON"
      />
    );

    // Both mock hospitals are within 30km of downtown Ottawa
    expect(screen.getByText('2')).toBeInTheDocument(); // Count
    expect(screen.getByText(/of 2 total/i)).toBeInTheDocument();
  });

  it('shows cost estimates with gas prices', () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 };

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="ON"
      />
    );

    // Should show a dollar amount for average access cost
    const costElement = screen.getByText(/^\$\d+$/);
    expect(costElement).toBeInTheDocument();
  });

  it('identifies nearest hospital', () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 };

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="ON"
      />
    );

    // Should show distance to nearest hospital
    const distanceElement = screen.getByText(/^\d+\.\d+km$/);
    expect(distanceElement).toBeInTheDocument();
  });

  it('handles empty hospital list gracefully', () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 };

    render(
      <AccessInsightsSummary
        hospitals={[]}
        userLocation={userLocation}
        province="ON"
      />
    );

    // Should still render without crashing
    expect(screen.getByText(/ERs Within 30km/i)).toBeInTheDocument();
  });

  it('uses correct gas price for province', () => {
    const userLocation = { lat: 49.2827, lon: -123.1207 }; // Vancouver

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="BC"
      />
    );

    // BC should use $1.75/L (mentioned in the component)
    expect(screen.getByText(/\$1\.75\/L in BC/i)).toBeInTheDocument();
  });
});
