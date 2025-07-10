import React, { forwardRef, useState, useRef, useEffect } from 'react';
import { motion, type HTMLMotionProps, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';
import './Input.css';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  error?: string;
  success?: string;
  helper?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'outlined' | 'filled' | 'flushed';
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
  clearable?: boolean;
  onClear?: () => void;
  floatingLabel?: boolean;
  animate?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      success,
      helper,
      size = 'md',
      variant = 'outlined',
      icon,
      iconPosition = 'left',
      loading = false,
      clearable = false,
      onClear,
      floatingLabel = true,
      animate = true,
      className,
      value,
      onChange,
      onFocus,
      onBlur,
      ...props
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const [hasValue, setHasValue] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    // Merge refs
    React.useImperativeHandle(ref, () => inputRef.current as HTMLInputElement);

    useEffect(() => {
      setHasValue(!!value || !!inputRef.current?.value);
    }, [value]);

    const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(true);
      onFocus?.(e);
    };

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(false);
      onBlur?.(e);
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setHasValue(!!e.target.value);
      onChange?.(e);
    };

    const handleClear = () => {
      if (inputRef.current) {
        const event = new Event('input', { bubbles: true });
        inputRef.current.value = '';
        inputRef.current.dispatchEvent(event);
      }
      setHasValue(false);
      onClear?.();
    };

    const containerClasses = clsx(
      'ds-input',
      `ds-input--${variant}`,
      `ds-input--${size}`,
      {
        'ds-input--focused': isFocused,
        'ds-input--error': !!error,
        'ds-input--success': !!success,
        'ds-input--has-value': hasValue,
        'ds-input--has-icon': !!icon,
        'ds-input--icon-left': icon && iconPosition === 'left',
        'ds-input--icon-right': icon && iconPosition === 'right',
        'ds-input--loading': loading,
        'ds-input--floating-label': floatingLabel && label,
      },
      className
    );

    const containerVariants = animate ? {
      initial: { opacity: 0, y: 10 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -10 },
    } : undefined;

    const labelVariants = {
      rest: {
        y: 0,
        scale: 1,
        color: 'var(--color-text-secondary)',
      },
      float: {
        y: variant === 'outlined' ? -24 : -20,
        scale: 0.75,
        color: isFocused 
          ? error ? 'var(--color-semantic-error-DEFAULT)'
          : success ? 'var(--color-semantic-success-DEFAULT)'
          : 'var(--color-brand-primary-500)'
          : 'var(--color-text-secondary)',
      },
    };

    const borderVariants = {
      rest: { scaleX: 0 },
      focus: { scaleX: 1 },
    };

    return (
      <motion.div
        className={containerClasses}
        variants={containerVariants}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        <div className="ds-input__wrapper">
          {/* Floating Label */}
          {label && floatingLabel && (
            <motion.label
              className="ds-input__label ds-input__label--floating"
              htmlFor={props.id}
              variants={labelVariants}
              initial={false}
              animate={isFocused || hasValue ? "float" : "rest"}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
              }}
            >
              {label}
            </motion.label>
          )}

          {/* Static Label */}
          {label && !floatingLabel && (
            <label className="ds-input__label ds-input__label--static" htmlFor={props.id}>
              {label}
            </label>
          )}

          <div className="ds-input__field-wrapper">
            {/* Left Icon */}
            {icon && iconPosition === 'left' && (
              <span className="ds-input__icon ds-input__icon--left">
                {icon}
              </span>
            )}

            {/* Input Field */}
            <input
              ref={inputRef}
              className="ds-input__field"
              value={value}
              onChange={handleChange}
              onFocus={handleFocus}
              onBlur={handleBlur}
              {...props}
            />

            {/* Right Icon / Clear Button / Loading */}
            <div className="ds-input__actions">
              {clearable && hasValue && !loading && (
                <motion.button
                  type="button"
                  className="ds-input__clear"
                  onClick={handleClear}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M12 4L4 12M4 4L12 12"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                </motion.button>
              )}

              {icon && iconPosition === 'right' && !clearable && !loading && (
                <span className="ds-input__icon ds-input__icon--right">
                  {icon}
                </span>
              )}

              {loading && (
                <motion.span
                  className="ds-input__loading"
                  animate={{ rotate: 360 }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M8 1.5C4.41 1.5 1.5 4.41 1.5 8C1.5 11.59 4.41 14.5 8 14.5"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                </motion.span>
              )}
            </div>

            {/* Focus Border Animation */}
            {variant === 'flushed' && (
              <motion.span
                className="ds-input__border"
                variants={borderVariants}
                initial="rest"
                animate={isFocused ? "focus" : "rest"}
                transition={{
                  type: "spring",
                  stiffness: 500,
                  damping: 30,
                }}
              />
            )}
          </div>
        </div>

        {/* Helper/Error/Success Text */}
        <AnimatePresence mode="wait">
          {(error || success || helper) && (
            <motion.div
              className="ds-input__message"
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.15 }}
            >
              {error && (
                <span className="ds-input__error">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M8 8V5M8 11H8.01M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  </svg>
                  {error}
                </span>
              )}
              {success && !error && (
                <span className="ds-input__success">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M6 8L7.5 9.5L10 6.5M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  {success}
                </span>
              )}
              {helper && !error && !success && (
                <span className="ds-input__helper">{helper}</span>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  }
);

Input.displayName = 'Input';