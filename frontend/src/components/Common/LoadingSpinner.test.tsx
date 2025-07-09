import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingSpinner } from './LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default size', () => {
    const { container } = render(<LoadingSpinner />);
    
    const spinner = container.querySelector('div > div');
    expect(spinner).toBeTruthy();
    expect(spinner?.className).toContain('w-8');
    expect(spinner?.className).toContain('h-8');
  });

  it('renders with small size', () => {
    const { container } = render(<LoadingSpinner size="small" />);
    
    const spinner = container.querySelector('div > div');
    expect(spinner?.className).toContain('w-4');
    expect(spinner?.className).toContain('h-4');
  });

  it('renders with medium size', () => {
    const { container } = render(<LoadingSpinner size="medium" />);
    
    const spinner = container.querySelector('div > div');
    expect(spinner?.className).toContain('w-8');
    expect(spinner?.className).toContain('h-8');
  });

  it('renders with large size', () => {
    const { container } = render(<LoadingSpinner size="large" />);
    
    const spinner = container.querySelector('div > div');
    expect(spinner?.className).toContain('w-12');
    expect(spinner?.className).toContain('h-12');
  });

  it('has animate-spin class', () => {
    const { container } = render(<LoadingSpinner />);
    
    const spinner = container.querySelector('div > div');
    expect(spinner?.className).toContain('animate-spin');
  });

  it('renders with custom className', () => {
    const { container } = render(<LoadingSpinner className="custom-class" />);
    
    const wrapper = container.firstChild;
    expect(wrapper?.className).toContain('custom-class');
  });
});