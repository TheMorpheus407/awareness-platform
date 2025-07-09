import React from 'react';
import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

export interface LoadingStateProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  fullScreen?: boolean;
  overlay?: boolean;
  variant?: 'spinner' | 'dots' | 'pulse' | 'bar';
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  size = 'md',
  text,
  fullScreen = false,
  overlay = false,
  variant = 'spinner',
  className,
}) => {
  const sizeStyles = {
    sm: { spinner: 'w-6 h-6', text: 'text-sm' },
    md: { spinner: 'w-10 h-10', text: 'text-base' },
    lg: { spinner: 'w-16 h-16', text: 'text-lg' },
    xl: { spinner: 'w-24 h-24', text: 'text-xl' },
  };

  const content = (
    <div className={clsx(
      'flex flex-col items-center justify-center',
      fullScreen && 'min-h-screen',
      !fullScreen && !overlay && 'p-8',
      className
    )}>
      {/* Spinner variant */}
      {variant === 'spinner' && (
        <Loader2 
          className={clsx(
            sizeStyles[size].spinner,
            'text-blue-600 animate-spin'
          )} 
        />
      )}

      {/* Dots variant */}
      {variant === 'dots' && (
        <div className="flex space-x-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={clsx(
                'rounded-full bg-blue-600',
                size === 'sm' && 'w-2 h-2',
                size === 'md' && 'w-3 h-3',
                size === 'lg' && 'w-4 h-4',
                size === 'xl' && 'w-5 h-5',
                'animate-bounce'
              )}
              style={{
                animationDelay: `${i * 0.1}s`,
              }}
            />
          ))}
        </div>
      )}

      {/* Pulse variant */}
      {variant === 'pulse' && (
        <div className="relative">
          <div className={clsx(
            'rounded-full bg-blue-600',
            size === 'sm' && 'w-8 h-8',
            size === 'md' && 'w-12 h-12',
            size === 'lg' && 'w-16 h-16',
            size === 'xl' && 'w-24 h-24'
          )}>
            <div className="absolute inset-0 rounded-full bg-blue-600 animate-ping opacity-75" />
          </div>
        </div>
      )}

      {/* Bar variant */}
      {variant === 'bar' && (
        <div className={clsx(
          'relative overflow-hidden bg-gray-200 rounded-full',
          size === 'sm' && 'w-32 h-1',
          size === 'md' && 'w-48 h-2',
          size === 'lg' && 'w-64 h-3',
          size === 'xl' && 'w-80 h-4'
        )}>
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 animate-shimmer" />
        </div>
      )}

      {/* Loading text */}
      {text && (
        <p className={clsx(
          'mt-4 text-gray-600 animate-pulse',
          sizeStyles[size].text
        )}>
          {text}
        </p>
      )}
    </div>
  );

  if (overlay) {
    return (
      <div className="fixed inset-0 z-50 bg-white/80 backdrop-blur-sm flex items-center justify-center">
        {content}
      </div>
    );
  }

  return content;
};

// Inline loading component
export const InlineLoading: React.FC<{
  size?: 'xs' | 'sm' | 'md';
  className?: string;
}> = ({ size = 'sm', className }) => {
  const sizeStyles = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
  };

  return (
    <Loader2 
      className={clsx(
        sizeStyles[size],
        'animate-spin text-blue-600',
        className
      )} 
    />
  );
};

// Loading button state
export const LoadingButton: React.FC<{
  loading?: boolean;
  children: React.ReactNode;
  loadingText?: string;
  className?: string;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
}> = ({ 
  loading = false, 
  children, 
  loadingText = 'Loading...', 
  className,
  onClick,
  variant = 'primary'
}) => {
  const variantStyles = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
  };

  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={clsx(
        variantStyles[variant],
        'relative',
        loading && 'cursor-not-allowed',
        className
      )}
    >
      <span className={clsx('flex items-center justify-center', loading && 'invisible')}>
        {children}
      </span>
      
      {loading && (
        <span className="absolute inset-0 flex items-center justify-center">
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          {loadingText}
        </span>
      )}
    </button>
  );
};

// Page transition loading
export const PageLoading: React.FC<{
  isLoading: boolean;
}> = ({ isLoading }) => {
  if (!isLoading) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      <div className="h-1 bg-blue-600/20">
        <div className="h-full bg-gradient-to-r from-blue-600 to-purple-600 animate-progress" />
      </div>
    </div>
  );
};