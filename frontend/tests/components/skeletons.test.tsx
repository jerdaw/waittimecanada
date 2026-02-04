import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { HospitalCardSkeleton } from '@/components/skeletons/HospitalCardSkeleton';
import { HeroSkeleton } from '@/components/skeletons/HeroSkeleton';

describe('Skeletons', () => {
  it('HospitalCardSkeleton renders with animate-pulse', () => {
    const { container } = render(<HospitalCardSkeleton />);
    const pulseElements = container.querySelectorAll('.animate-pulse');
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it('HeroSkeleton renders with animate-pulse', () => {
    const { container } = render(<HeroSkeleton />);
    const pulseElements = container.querySelectorAll('.animate-pulse');
    expect(pulseElements.length).toBeGreaterThan(0);
  });
});
