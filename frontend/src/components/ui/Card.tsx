import React from 'react';
import { clsx } from 'clsx';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

interface CardComponent extends React.FC<CardProps> {
  Header: React.FC<CardProps>;
  Title: React.FC<CardProps>;
  Content: React.FC<CardProps>;
  Footer: React.FC<CardProps>;
}

const CardBase: React.FC<CardProps> = ({ children, className, ...props }) => {
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

export const Card = CardBase as CardComponent;

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

// Attach sub-components to Card for dot notation access
Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Content = CardContent;
Card.Footer = CardFooter;

// Also export as named exports for compatibility
export { CardHeader, CardTitle, CardContent, CardFooter };