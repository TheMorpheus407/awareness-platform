import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorMessage } from './ErrorMessage';

describe('ErrorMessage', () => {
  it('renders error message', () => {
    const message = 'An error occurred';
    render(<ErrorMessage message={message} />);
    
    expect(screen.getByText(message)).toBeTruthy();
  });

  it('renders with error styling', () => {
    render(<ErrorMessage message="Error" />);
    
    const container = screen.getByText('Error').parentElement;
    expect(container?.className).toContain('bg-red-50');
    expect(container?.className).toContain('border-red-200');
    expect(container?.className).toContain('text-red-700');
  });

  it('renders with proper structure', () => {
    render(<ErrorMessage message="Test error" />);
    
    const container = screen.getByText('Test error').parentElement;
    expect(container?.className).toContain('rounded-md');
    expect(container?.className).toContain('p-3');
    expect(container?.className).toContain('border');
  });

  it('applies custom className', () => {
    render(<ErrorMessage message="Error" className="custom-class" />);
    
    const container = screen.getByText('Error').parentElement;
    expect(container?.className).toContain('custom-class');
  });
});