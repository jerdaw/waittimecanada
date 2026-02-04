import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HospitalList } from '@/components/HospitalList';
import type { Hospital } from '@/app/api/hospitals/route';

// Mock react-window to just render children
vi.mock('react-window', () => ({
  FixedSizeList: ({ children, itemCount }: { children: any, itemCount: number }) => (
    <div>
      {Array.from({ length: itemCount }).map((_, index) => (
        children({ index, style: {} })
      ))}
    </div>
  ),
}));

// Mock AutoSizer to just render children
vi.mock('react-virtualized-auto-sizer', () => ({
  default: ({ children }: { children: any }) => children({ height: 500, width: 500 }),
}));

const mockHospitals: Hospital[] = [
  {
    id: "h1",
    name: "General Hospital",
    city: "Toronto",
    province: "ON",
    current_wait_time: 120,
    last_updated: new Date().toISOString(),
    is_verified: true,
  } as Hospital,
];

describe('HospitalList', () => {
  it('renders search input with provided query', () => {
    render(
      <HospitalList 
        hospitals={mockHospitals} 
        selectedId={null} 
        onSelect={() => {}}
        searchQuery="test query"
      />
    );
    
    const input = screen.getByPlaceholderText('Search by name or city...');
    expect(input).toHaveValue('test query');
  });

  it('calls onSearchChange when input changes', () => {
    const onSearchChange = vi.fn();
    render(
      <HospitalList 
        hospitals={mockHospitals} 
        selectedId={null} 
        onSelect={() => {}}
        searchQuery=""
        onSearchChange={onSearchChange}
      />
    );
    
    const input = screen.getByPlaceholderText('Search by name or city...');
    fireEvent.change(input, { target: { value: 'new' } });
    
    expect(onSearchChange).toHaveBeenCalledWith('new');
  });

  it('renders empty state message when no hospitals found', () => {
    render(
      <HospitalList 
        hospitals={[]} 
        selectedId={null} 
        onSelect={() => {}}
        searchQuery="invalid"
      />
    );
    
    expect(screen.getByText('No hospitals found matching "invalid"')).toBeDefined();
    expect(screen.getByText('Clear search')).toBeDefined();
  });

  it('calls onSearchChange with empty string when clear search clicked', () => {
    const onSearchChange = vi.fn();
    render(
      <HospitalList 
        hospitals={[]} 
        selectedId={null} 
        onSelect={() => {}}
        searchQuery="invalid"
        onSearchChange={onSearchChange}
      />
    );
    
    fireEvent.click(screen.getByText('Clear search'));
    expect(onSearchChange).toHaveBeenCalledWith('');
  });

  it('renders distance when userLocation is provided', () => {
    const userLocation = { lat: 43.65, lon: -79.38 }; // Toronto
    // Hospital is also Toronto (distance ~0)
    
    render(
      <HospitalList 
        hospitals={mockHospitals} 
        selectedId={null} 
        onSelect={() => {}}
        userLocation={userLocation}
      />
    );
    
    // Should show distance badge
    expect(screen.getByText(/📍/)).toBeDefined();
  });

  it('renders sort buttons and calls onSortChange', () => {
    const onSortChange = vi.fn();
    render(
      <HospitalList 
        hospitals={mockHospitals} 
        selectedId={null} 
        onSelect={() => {}}
        onSortChange={onSortChange}
        sortByDistance={false}
      />
    );
    
    const nearMeBtn = screen.getByText('Near Me');
    fireEvent.click(nearMeBtn);
    expect(onSortChange).toHaveBeenCalledWith(true);
  });

  it('renders LIVE badge for recently updated hospitals', () => {
    // Recent hospital (just updated)
    const recentHospital = {
      ...mockHospitals[0],
      id: "recent",
      last_updated: new Date().toISOString()
    };
    
    // Old hospital (1 hour ago)
    const oldDate = new Date();
    oldDate.setHours(oldDate.getHours() - 1);
    const oldHospital = {
      ...mockHospitals[0],
      id: "old",
      last_updated: oldDate.toISOString()
    };

    render(
      <HospitalList 
        hospitals={[recentHospital, oldHospital]} 
        selectedId={null} 
        onSelect={() => {}}
      />
    );
    
    // Check for LIVE badge
    const liveBadges = screen.getAllByText('LIVE');
    expect(liveBadges.length).toBe(1); // Only Recent should have it
  });
});
