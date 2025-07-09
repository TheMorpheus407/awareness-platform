import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatsCard } from './StatsCard';
import { Users } from 'lucide-react';

describe('StatsCard', () => {
  const defaultProps = {
    title: 'Total Users',
    value: '1,234',
    icon: Users,
    change: 20,
    changeType: 'increase' as const,
  };

  it('renders title and value', () => {
    render(<StatsCard {...defaultProps} />);
    
    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('1,234')).toBeInTheDocument();
  });

  it('renders change when provided', () => {
    render(<StatsCard {...defaultProps} />);
    
    expect(screen.getByText('+20% from last month')).toBeTruthy();
  });

  it('renders without change', () => {
    const { container } = render(
      <StatsCard title="Test" value="100" icon={Users} />
    );
    
    expect(container.textContent).not.toContain('from last month');
  });

  it('applies correct styling for increase', () => {
    render(<StatsCard {...defaultProps} changeType="increase" />);
    
    const change = screen.getByText('+20% from last month');
    expect(change.className).toContain('text-green-600');
  });

  it('applies correct styling for decrease', () => {
    render(<StatsCard {...defaultProps} change={-20} changeType="decrease" />);
    
    const change = screen.getByText('-20% from last month');
    expect(change.className).toContain('text-red-600');
  });

  it('applies correct color classes', () => {
    const { container } = render(<StatsCard {...defaultProps} color="success" />);
    
    const iconContainer = container.querySelector('.bg-green-100');
    expect(iconContainer).toBeTruthy();
  });

  it('renders with icon', () => {
    const { container } = render(<StatsCard {...defaultProps} />);
    
    const icon = container.querySelector('svg');
    expect(icon).toBeTruthy();
  });

  it('renders with card styling', () => {
    const { container } = render(<StatsCard {...defaultProps} />);
    
    const card = container.querySelector('.card');
    expect(card).toBeTruthy();
  });
});