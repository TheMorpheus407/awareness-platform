import React, { forwardRef } from 'react';
import type { HTMLAttributes, FC } from 'react';
import clsx from 'clsx';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined' | 'gradient' | 'glass';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  interactive?: boolean;
  glow?: boolean;
  animated?: boolean;
}

interface CardComponent extends React.ForwardRefExoticComponent<CardProps & React.RefAttributes<HTMLDivElement>> {
  Header: FC<{ className?: string; children: React.ReactNode }>;
  Title: FC<{ className?: string; children: React.ReactNode }>;
  Content: FC<{ className?: string; children: React.ReactNode }>;
  Footer: FC<{ className?: string; children: React.ReactNode }>;
}

const CardBase = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      className,
      variant = 'default',
      padding = 'md',
      interactive = false,
      glow = false,
      animated = true,
      onMouseMove,
      ...props
    },
    ref
  ) => {
    const [mousePosition, setMousePosition] = React.useState({ x: 0, y: 0 });

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
      if (variant === 'gradient' || glow) {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        setMousePosition({ x, y });
      }
      onMouseMove?.(e);
    };

    const baseStyles = clsx(
      'relative rounded-2xl transition-all duration-500',
      animated && 'transform',
      interactive && 'cursor-pointer hover:scale-[1.02] hover:-translate-y-1'
    );

    const variantStyles = {
      default: clsx(
        'bg-white border border-gray-200',
        interactive && 'hover:shadow-xl hover:border-gray-300'
      ),
      elevated: clsx(
        'bg-white shadow-lg',
        interactive && 'hover:shadow-2xl'
      ),
      outlined: clsx(
        'bg-transparent border-2 border-gray-300',
        interactive && 'hover:border-blue-500 hover:bg-blue-50/50'
      ),
      gradient: clsx(
        'bg-gradient-to-br from-white to-gray-50 border border-gray-200',
        interactive && 'hover:shadow-2xl hover:from-blue-50 hover:to-purple-50'
      ),
      glass: clsx(
        'bg-white/70 backdrop-blur-md border border-white/20',
        interactive && 'hover:bg-white/80 hover:shadow-xl'
      ),
    };

    const paddingStyles = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
      xl: 'p-10',
    };

    const glowStyles = glow && 'shadow-xl hover:shadow-2xl hover:shadow-blue-500/20';

    return (
      <div
        ref={ref}
        className={clsx(
          baseStyles,
          variantStyles[variant],
          paddingStyles[padding],
          glowStyles,
          className
        )}
        onMouseMove={handleMouseMove}
        style={
          {
            '--mouse-x': `${mousePosition.x}px`,
            '--mouse-y': `${mousePosition.y}px`,
          } as React.CSSProperties
        }
        {...props}
      >
        {/* Gradient glow effect */}
        {(variant === 'gradient' || glow) && (
          <div
            className="absolute inset-0 rounded-2xl opacity-0 hover:opacity-100 transition-opacity duration-500 pointer-events-none"
            style={{
              background: `radial-gradient(600px circle at var(--mouse-x) var(--mouse-y), rgba(59, 130, 246, 0.1), transparent 40%)`,
            }}
          />
        )}

        {/* Glass reflection */}
        {variant === 'glass' && (
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-white/10 to-transparent pointer-events-none" />
        )}

        {/* Content */}
        <div className="relative z-10">{children}</div>

        {/* Interactive shine effect */}
        {interactive && animated && (
          <div className="absolute inset-0 rounded-2xl overflow-hidden pointer-events-none">
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full hover:translate-x-full transition-transform duration-1000" />
          </div>
        )}
      </div>
    );
  }
);

CardBase.displayName = 'Card';

// Card sub-components
export const CardHeader: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <div className={clsx('mb-4 pb-4 border-b border-gray-200', className)}>
    {children}
  </div>
);

export const CardTitle: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <h3 className={clsx('text-xl font-semibold text-gray-900', className)}>
    {children}
  </h3>
);

export const CardContent: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => <div className={clsx('text-gray-600', className)}>{children}</div>;

export const CardFooter: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <div className={clsx('mt-4 pt-4 border-t border-gray-200', className)}>
    {children}
  </div>
);

// Export Card with proper typing
export const Card = Object.assign(CardBase, {
  Header: CardHeader,
  Title: CardTitle,
  Content: CardContent,
  Footer: CardFooter,
}) as CardComponent;