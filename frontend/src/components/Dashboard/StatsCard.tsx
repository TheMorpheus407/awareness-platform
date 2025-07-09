import React from 'react';
import type { LucideIcon } from 'lucide-react';
import clsx from 'clsx';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { useCountAnimation } from '../../hooks/useAnimation';
import { Card } from '../ui';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  change?: number;
  changeType?: 'increase' | 'decrease';
  color?: 'primary' | 'success' | 'warning' | 'danger';
  animated?: boolean;
  sparkline?: number[];
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon: Icon,
  change,
  changeType,
  color = 'primary',
  animated = true,
  sparkline,
}) => {
  const numericValue = typeof value === 'string' ? parseInt(value) : value;
  const { count, animate } = useCountAnimation(isNaN(numericValue) ? 0 : numericValue, 2000);
  
  React.useEffect(() => {
    if (animated && !isNaN(numericValue)) {
      animate();
    }
  }, [numericValue]);

  const colorClasses = {
    primary: 'bg-gradient-to-br from-blue-500 to-blue-600',
    success: 'bg-gradient-to-br from-green-500 to-green-600',
    warning: 'bg-gradient-to-br from-amber-500 to-amber-600',
    danger: 'bg-gradient-to-br from-red-500 to-red-600',
  };

  const iconBgClasses = {
    primary: 'bg-blue-100 text-blue-600',
    success: 'bg-green-100 text-green-600',
    warning: 'bg-amber-100 text-amber-600',
    danger: 'bg-red-100 text-red-600',
  };

  const displayValue = animated && !isNaN(numericValue) ? count : value;

  return (
    <Card
      variant="elevated"
      interactive
      glow
      className="group hover:shadow-2xl transition-all duration-500"
    >
      <div className="relative overflow-hidden">
        {/* Background decoration */}
        <div className={clsx(
          'absolute -right-8 -top-8 w-32 h-32 rounded-full opacity-10',
          colorClasses[color]
        )} />
        
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-4">
            <div className={clsx(
              'p-3 rounded-xl transition-all duration-300 group-hover:scale-110',
              iconBgClasses[color]
            )}>
              <Icon className="w-6 h-6" />
            </div>
            
            {sparkline && (
              <div className="flex items-end space-x-1 h-8">
                {sparkline.map((value, index) => (
                  <div
                    key={index}
                    className={clsx(
                      'w-1 bg-gray-300 rounded-full transition-all duration-500',
                      'group-hover:bg-blue-400'
                    )}
                    style={{ height: `${value}%` }}
                  />
                ))}
              </div>
            )}
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
            <p className="text-3xl font-bold text-gray-900">
              {typeof displayValue === 'string' && displayValue.includes('%') 
                ? displayValue 
                : displayValue.toLocaleString()}
            </p>
            
            {change !== undefined && (
              <div className="flex items-center mt-3 space-x-1">
                {changeType === 'increase' ? (
                  <TrendingUp className="w-4 h-4 text-green-600" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-600" />
                )}
                <p className={clsx(
                  'text-sm font-medium',
                  changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                )}>
                  {Math.abs(change)}%
                </p>
                <p className="text-sm text-gray-500">vs last month</p>
              </div>
            )}
          </div>
        </div>
        
        {/* Hover effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
      </div>
    </Card>
  );
};