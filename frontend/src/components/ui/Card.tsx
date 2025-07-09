import React from 'react';
import { clsx } from 'clsx';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <div
      className={clsx(
        'bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <div
      className={clsx('px-6 py-4 border-b border-gray-200 dark:border-gray-700', className)}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardTitle: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <h3
      className={clsx('text-lg font-semibold text-gray-900 dark:text-gray-100', className)}
      {...props}
    >
      {children}
    </h3>
  );
};

export const CardContent: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <div className={clsx('px-6 py-4', className)} {...props}>
      {children}
    </div>
  );
};

export const CardFooter: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <div
      className={clsx(
        'px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};