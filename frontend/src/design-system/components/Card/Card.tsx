import React, { forwardRef } from 'react';
import { motion, type HTMLMotionProps, type Variants } from 'framer-motion';
import { clsx } from 'clsx';
import './Card.css';

export interface CardProps extends HTMLMotionProps<"div"> {
  variant?: 'default' | 'elevated' | 'outlined' | 'filled' | 'interactive';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
  glow?: boolean;
  loading?: boolean;
  children: React.ReactNode;
}

const cardVariants: Variants = {
  initial: {
    scale: 1,
    y: 0,
  },
  hover: {
    scale: 1.02,
    y: -4,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 20,
    },
  },
  tap: {
    scale: 0.98,
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 25,
    },
  },
};

const glowVariants: Variants = {
  initial: {
    opacity: 0,
  },
  hover: {
    opacity: 1,
    transition: {
      duration: 0.3,
    },
  },
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      padding = 'md',
      hover = false,
      glow = false,
      loading = false,
      children,
      className,
      ...props
    },
    ref
  ) => {
    const cardClasses = clsx(
      'ds-card',
      `ds-card--${variant}`,
      `ds-card--padding-${padding}`,
      {
        'ds-card--hover': hover,
        'ds-card--glow': glow,
        'ds-card--loading': loading,
      },
      className
    );

    return (
      <motion.div
        ref={ref}
        className={cardClasses}
        variants={hover ? cardVariants : undefined}
        initial="initial"
        whileHover={hover ? "hover" : undefined}
        whileTap={hover ? "tap" : undefined}
        {...props}
      >
        {/* Content */}
        <div className="ds-card__content">
          {children}
        </div>

        {/* Glow Effect */}
        {glow && (
          <motion.div
            className="ds-card__glow"
            variants={glowVariants}
            initial="initial"
            animate={hover ? "hover" : "initial"}
          />
        )}

        {/* Loading Overlay */}
        {loading && (
          <div className="ds-card__loading">
            <div className="ds-card__loading-shimmer" />
          </div>
        )}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';

// Card Header Component
export interface CardHeaderProps extends HTMLMotionProps<"div"> {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  children?: React.ReactNode;
}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ title, subtitle, action, children, className, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={clsx('ds-card__header', className)}
        {...props}
      >
        {children || (
          <>
            <div className="ds-card__header-content">
              {title && <h3 className="ds-card__title">{title}</h3>}
              {subtitle && <p className="ds-card__subtitle">{subtitle}</p>}
            </div>
            {action && <div className="ds-card__header-action">{action}</div>}
          </>
        )}
      </motion.div>
    );
  }
);

CardHeader.displayName = 'CardHeader';

// Card Body Component
export interface CardBodyProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
}

export const CardBody = forwardRef<HTMLDivElement, CardBodyProps>(
  ({ children, className, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={clsx('ds-card__body', className)}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

CardBody.displayName = 'CardBody';

// Card Footer Component
export interface CardFooterProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  divider?: boolean;
}

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ children, divider = true, className, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={clsx('ds-card__footer', {
          'ds-card__footer--divider': divider,
        }, className)}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

CardFooter.displayName = 'CardFooter';

// Card Media Component
export interface CardMediaProps extends HTMLMotionProps<"div"> {
  src?: string;
  alt?: string;
  height?: number | string;
  children?: React.ReactNode;
}

export const CardMedia = forwardRef<HTMLDivElement, CardMediaProps>(
  ({ src, alt, height = 200, children, className, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={clsx('ds-card__media', className)}
        style={{ height }}
        {...props}
      >
        {src ? (
          <img
            src={src}
            alt={alt || ''}
            className="ds-card__media-image"
          />
        ) : children}
      </motion.div>
    );
  }
);

CardMedia.displayName = 'CardMedia';