import React, { forwardRef, useRef, useState } from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';
import { clsx } from 'clsx';
import { Ripple } from '../Ripple/Ripple';
import './Button.css';

export interface ButtonProps extends Omit<HTMLMotionProps<"button">, 'size'> {
  variant?: 'primary' | 'secondary' | 'tertiary' | 'ghost' | 'danger' | 'success';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  fullWidth?: boolean;
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  ripple?: boolean;
  glow?: boolean;
  pulse?: boolean;
  children: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      disabled = false,
      icon,
      iconPosition = 'left',
      ripple = true,
      glow = false,
      pulse = false,
      children,
      className,
      onClick,
      ...props
    },
    ref
  ) => {
    const buttonRef = useRef<HTMLButtonElement>(null);
    const [isPressed, setIsPressed] = useState(false);

    // Merge refs
    React.useImperativeHandle(ref, () => buttonRef.current as HTMLButtonElement);

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (!disabled && !loading && onClick) {
        onClick(e);
      }
    };

    const buttonClasses = clsx(
      'ds-button',
      `ds-button--${variant}`,
      `ds-button--${size}`,
      {
        'ds-button--full-width': fullWidth,
        'ds-button--loading': loading,
        'ds-button--disabled': disabled,
        'ds-button--with-icon': !!icon,
        'ds-button--icon-right': iconPosition === 'right',
        'ds-button--glow': glow,
        'ds-button--pulse': pulse,
      },
      className
    );

    const buttonVariants = {
      idle: { scale: 1 },
      hover: { scale: 1.02 },
      tap: { scale: 0.98 },
    };

    const iconVariants = {
      idle: { rotate: 0 },
      hover: { rotate: iconPosition === 'right' ? 5 : -5 },
    };

    const loadingVariants = {
      animate: {
        rotate: 360,
        transition: {
          duration: 1,
          repeat: Infinity,
          ease: "linear" as const
        }
      }
    };

    return (
      <motion.button
        ref={buttonRef}
        className={buttonClasses}
        disabled={disabled || loading}
        onClick={handleClick}
        onMouseDown={() => setIsPressed(true)}
        onMouseUp={() => setIsPressed(false)}
        onMouseLeave={() => setIsPressed(false)}
        variants={buttonVariants}
        initial="idle"
        whileHover="hover"
        whileTap="tap"
        transition={{
          type: "spring",
          stiffness: 500,
          damping: 30,
        }}
        {...props}
      >
        {/* Ripple Effect */}
        {ripple && !disabled && <Ripple />}

        {/* Loading Spinner */}
        {loading && (
          <motion.span
            className="ds-button__spinner"
            variants={loadingVariants}
            animate="animate"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M8 1.5C4.41 1.5 1.5 4.41 1.5 8C1.5 11.59 4.41 14.5 8 14.5"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </motion.span>
        )}

        {/* Icon */}
        {icon && iconPosition === 'left' && !loading && (
          <motion.span
            className="ds-button__icon ds-button__icon--left"
            variants={iconVariants}
            transition={{ duration: 0.2 }}
          >
            {icon}
          </motion.span>
        )}

        {/* Button Text */}
        <span className="ds-button__text">{children}</span>

        {/* Icon Right */}
        {icon && iconPosition === 'right' && !loading && (
          <motion.span
            className="ds-button__icon ds-button__icon--right"
            variants={iconVariants}
            transition={{ duration: 0.2 }}
          >
            {icon}
          </motion.span>
        )}

        {/* Glow Effect */}
        {glow && !disabled && (
          <span className="ds-button__glow" />
        )}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';