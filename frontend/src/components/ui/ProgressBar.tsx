import React from 'react';
import clsx from 'clsx';
import { Trophy, Star, Zap } from 'lucide-react';

export interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'gradient';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  animated?: boolean;
  showMilestones?: boolean;
  milestones?: number[];
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  showPercentage = true,
  variant = 'default',
  size = 'md',
  animated = true,
  showMilestones = false,
  milestones = [25, 50, 75],
  className,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const baseStyles = 'relative w-full overflow-hidden rounded-full bg-gray-200';

  const sizeStyles = {
    xs: 'h-1',
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
  };

  const fillStyles = {
    default: 'bg-blue-600',
    success: 'bg-green-600',
    warning: 'bg-yellow-600',
    danger: 'bg-red-600',
    gradient: 'bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600',
  };

  const getMilestoneIcon = (milestone: number) => {
    if (milestone <= 25) return <Star className="w-3 h-3" />;
    if (milestone <= 50) return <Trophy className="w-3 h-3" />;
    return <Zap className="w-3 h-3" />;
  };

  return (
    <div className={clsx('space-y-2', className)}>
      {/* Label and percentage */}
      {(label || showPercentage) && (
        <div className="flex justify-between items-center text-sm">
          {label && <span className="font-medium text-gray-700">{label}</span>}
          {showPercentage && (
            <span className="font-semibold text-gray-900">{Math.round(percentage)}%</span>
          )}
        </div>
      )}

      {/* Progress bar container */}
      <div className={clsx(baseStyles, sizeStyles[size])}>
        {/* Milestones */}
        {showMilestones && (
          <>
            {milestones.map((milestone) => (
              <div
                key={milestone}
                className={clsx(
                  'absolute top-1/2 -translate-y-1/2 z-10',
                  'w-6 h-6 rounded-full border-2 border-white',
                  'flex items-center justify-center',
                  'transition-all duration-500',
                  percentage >= milestone
                    ? 'bg-white text-gray-900 scale-110'
                    : 'bg-gray-400 text-gray-600 scale-90'
                )}
                style={{ left: `${milestone}%`, marginLeft: '-12px' }}
              >
                {getMilestoneIcon(milestone)}
              </div>
            ))}
          </>
        )}

        {/* Progress fill */}
        <div
          className={clsx(
            'h-full transition-all duration-1000 ease-out relative',
            fillStyles[variant],
            animated && 'animate-pulse'
          )}
          style={{ width: `${percentage}%` }}
        >
          {/* Shimmer effect */}
          {animated && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
          )}

          {/* Leading edge glow */}
          {animated && percentage > 0 && percentage < 100 && (
            <div className="absolute right-0 top-0 bottom-0 w-2 bg-white/50 blur-sm animate-pulse" />
          )}
        </div>

        {/* Completion celebration */}
        {percentage === 100 && animated && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-white font-bold animate-bounce">🎉</span>
          </div>
        )}
      </div>

      {/* Milestone labels */}
      {showMilestones && size !== 'xs' && (
        <div className="relative h-4">
          {milestones.map((milestone) => (
            <span
              key={milestone}
              className={clsx(
                'absolute text-xs font-medium transition-colors duration-500',
                percentage >= milestone ? 'text-blue-600' : 'text-gray-400'
              )}
              style={{ left: `${milestone}%`, transform: 'translateX(-50%)' }}
            >
              {milestone}%
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

// Circular progress variant
export const CircularProgress: React.FC<{
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  strokeWidth?: number;
  showValue?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'gradient';
  className?: string;
}> = ({
  value,
  max = 100,
  size = 'md',
  strokeWidth = 4,
  showValue = true,
  variant = 'default',
  className,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const sizes = {
    sm: { dimension: 48, fontSize: 'text-xs' },
    md: { dimension: 64, fontSize: 'text-sm' },
    lg: { dimension: 96, fontSize: 'text-base' },
    xl: { dimension: 128, fontSize: 'text-lg' },
  };

  const colors = {
    default: '#3b82f6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    gradient: 'url(#gradient)',
  };

  const { dimension, fontSize } = sizes[size];
  const radius = (dimension - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className={clsx('relative inline-flex items-center justify-center', className)}>
      <svg
        width={dimension}
        height={dimension}
        className="transform -rotate-90"
      >
        {variant === 'gradient' && (
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="50%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#ec4899" />
            </linearGradient>
          </defs>
        )}
        
        {/* Background circle */}
        <circle
          cx={dimension / 2}
          cy={dimension / 2}
          r={radius}
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
          fill="none"
        />
        
        {/* Progress circle */}
        <circle
          cx={dimension / 2}
          cy={dimension / 2}
          r={radius}
          stroke={colors[variant]}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      
      {/* Value display */}
      {showValue && (
        <div className={clsx('absolute inset-0 flex items-center justify-center', fontSize)}>
          <span className="font-bold text-gray-900">{Math.round(percentage)}%</span>
        </div>
      )}
    </div>
  );
};