import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { StructuredData } from '@/app/structured-data';

// Mock next/script
vi.mock('next/script', () => ({
  default: ({ id, dangerouslySetInnerHTML }: { id: string, dangerouslySetInnerHTML: { __html: string } }) => (
    <script id={id} dangerouslySetInnerHTML={dangerouslySetInnerHTML} />
  ),
}));

describe('StructuredData', () => {
  it('renders all required schema types', () => {
    const { container } = render(<StructuredData />);
    
    // Check for script tags
    expect(container.querySelector('#schema-faq')).toBeDefined();
    expect(container.querySelector('#schema-medical')).toBeDefined();
    expect(container.querySelector('#schema-org')).toBeDefined();
    expect(container.querySelector('#schema-howto')).toBeDefined();
  });

  it('generates valid JSON-LD for FAQPage', () => {
    const { container } = render(<StructuredData />);
    const script = container.querySelector('#schema-faq');
    const content = JSON.parse(script?.innerHTML || '{}');
    
    expect(content['@type']).toBe('FAQPage');
    expect(content.mainEntity).toBeDefined();
    expect(content.mainEntity.length).toBeGreaterThan(0);
    expect(content.mainEntity[0]['@type']).toBe('Question');
  });

  it('generates valid JSON-LD for MedicalWebPage', () => {
    const { container } = render(<StructuredData />);
    const script = container.querySelector('#schema-medical');
    const content = JSON.parse(script?.innerHTML || '{}');
    
    expect(content['@type']).toBe('MedicalWebPage');
    expect(content.specialty.name).toBe('Emergency Medicine');
  });

  it('generates valid JSON-LD for Organization', () => {
    const { container } = render(<StructuredData />);
    const script = container.querySelector('#schema-org');
    const content = JSON.parse(script?.innerHTML || '{}');
    
    expect(content['@type']).toBe('Organization');
    expect(content.name).toBe('WaitTime Canada');
  });
});
