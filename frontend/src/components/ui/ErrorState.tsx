import React from 'react';
import clsx from 'clsx';
import { AlertCircle, RefreshCw, Home, HelpCircle, XCircle } from 'lucide-react';
import { Button } from './button';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  variant?: 'error' | 'warning' | 'not-found' | 'permission';
  icon?: React.ReactNode;
  showRetry?: boolean;
  onRetry?: () => void;
  showHome?: boolean;
  onHome?: () => void;
  children?: React.ReactNode;
  className?: string;
}

const defaultContent = {
  error: {
    title: 'Oops! Something went wrong',
    message: 'We encountered an unexpected error. Please try again or contact support if the problem persists.',
    icon: <XCircle className="w-16 h-16" />,
  },
  warning: {
    title: 'Warning',
    message: 'This action requires your attention. Please review and proceed with caution.',
    icon: <AlertCircle className="w-16 h-16" />,
  },
  'not-found': {
    title: '404 - Page not found',
    message: 'The page you are looking for doesn\'t exist or has been moved.',
    icon: <HelpCircle className="w-16 h-16" />,
  },
  permission: {
    title: 'Access denied',
    message: 'You don\'t have permission to access this resource. Please contact your administrator.',
    icon: <AlertCircle className="w-16 h-16" />,
  },
};

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  variant = 'error',
  icon,
  showRetry = true,
  onRetry,
  showHome = false,
  onHome,
  children,
  className,
}) => {
  const content = defaultContent[variant];
  
  const iconColors = {
    error: 'text-red-500',
    warning: 'text-yellow-500',
    'not-found': 'text-blue-500',
    permission: 'text-orange-500',
  };

  return (
    <div className={clsx(
      'flex flex-col items-center justify-center min-h-[400px] p-8 text-center',
      className
    )}>
      {/* Icon */}
      <div className={clsx(
        'mb-6 animate-bounce',
        iconColors[variant]
      )}>
        {icon || content.icon}
      </div>

      {/* Title */}
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        {title || content.title}
      </h2>

      {/* Message */}
      <p className="text-gray-600 max-w-md mb-8">
        {message || content.message}
      </p>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-4">
        {showRetry && onRetry && (
          <Button
            onClick={onRetry}
            variant="primary"
            icon={<RefreshCw className="w-4 h-4" />}
            animated
          >
            Try again
          </Button>
        )}
        
        {showHome && onHome && (
          <Button
            onClick={onHome}
            variant="secondary"
            icon={<Home className="w-4 h-4" />}
          >
            Go home
          </Button>
        )}
      </div>

      {/* Additional content */}
      {children && (
        <div className="mt-8">
          {children}
        </div>
      )}
    </div>
  );
};

// Empty state component
export const EmptyState: React.FC<{
  title?: string;
  message?: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}> = ({
  title = 'No data found',
  message = 'There\'s nothing to display here yet.',
  icon,
  action,
  className,
}) => (
  <div className={clsx(
    'flex flex-col items-center justify-center min-h-[300px] p-8 text-center',
    className
  )}>
    {icon && (
      <div className="mb-4 text-gray-400">
        {icon}
      </div>
    )}
    
    <h3 className="text-lg font-semibold text-gray-900 mb-2">
      {title}
    </h3>
    
    <p className="text-gray-600 max-w-sm mb-6">
      {message}
    </p>
    
    {action && (
      <Button onClick={action.onClick} variant="primary" size="sm">
        {action.label}
      </Button>
    )}
  </div>
);

// Inline error component
export const InlineError: React.FC<{
  message: string;
  onDismiss?: () => void;
  className?: string;
}> = ({ message, onDismiss, className }) => (
  <div className={clsx(
    'flex items-center p-3 bg-red-50 border border-red-200 rounded-lg',
    className
  )}>
    <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0" />
    <p className="text-sm text-red-700 flex-1">{message}</p>
    {onDismiss && (
      <button
        onClick={onDismiss}
        className="ml-2 text-red-500 hover:text-red-700 transition-colors"
      >
        <XCircle className="w-4 h-4" />
      </button>
    )}
  </div>
);

// Network error component
export const NetworkError: React.FC<{
  onRetry?: () => void;
  className?: string;
}> = ({ onRetry, className }) => (
  <ErrorState
    variant="error"
    title="Connection lost"
    message="Please check your internet connection and try again."
    icon={
      <div className="relative">
        <AlertCircle className="w-16 h-16 text-red-500" />
        <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-white rounded-full flex items-center justify-center">
          <XCircle className="w-4 h-4 text-red-500" />
        </div>
      </div>
    }
    showRetry
    onRetry={onRetry}
    className={className}
  />
);