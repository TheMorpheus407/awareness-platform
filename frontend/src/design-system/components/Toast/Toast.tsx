import React, { useEffect } from 'react';
import { motion, AnimatePresence, type Variants } from 'framer-motion';
import { clsx } from 'clsx';
import './Toast.css';

export interface ToastProps {
  id: string;
  title: string;
  description?: string;
  type?: 'info' | 'success' | 'warning' | 'error';
  duration?: number;
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
  onClose: (id: string) => void;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const toastVariants: Variants = {
  initial: (position: string) => ({
    opacity: 0,
    x: position.includes('right') ? 100 : position.includes('left') ? -100 : 0,
    y: position.includes('top') ? -100 : position.includes('bottom') ? 100 : 0,
    scale: 0.85,
  }),
  animate: {
    opacity: 1,
    x: 0,
    y: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 25,
    },
  },
  exit: (position: string) => ({
    opacity: 0,
    x: position.includes('right') ? 100 : position.includes('left') ? -100 : 0,
    scale: 0.85,
    transition: {
      duration: 0.2,
    },
  }),
};

const progressVariants: Variants = {
  initial: { scaleX: 1 },
  animate: (duration: number) => ({
    scaleX: 0,
    transition: {
      duration: duration / 1000,
      ease: "linear",
    },
  }),
};

export const Toast: React.FC<ToastProps> = ({
  id,
  title,
  description,
  type = 'info',
  duration = 5000,
  position = 'bottom-right',
  onClose,
  action,
}) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose(id);
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);

  const toastClasses = clsx(
    'ds-toast',
    `ds-toast--${type}`,
  );

  const getIcon = () => {
    switch (type) {
      case 'success':
        return (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM8 15L3 10L4.41 8.59L8 12.17L15.59 4.58L17 6L8 15Z"
              fill="currentColor"
            />
          </svg>
        );
      case 'error':
        return (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM11 15H9V13H11V15ZM11 11H9V5H11V11Z"
              fill="currentColor"
            />
          </svg>
        );
      case 'warning':
        return (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M1 19H19L10 2L1 19ZM11 16H9V14H11V16ZM11 12H9V8H11V12Z"
              fill="currentColor"
            />
          </svg>
        );
      default:
        return (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM11 15H9V9H11V15ZM11 7H9V5H11V7Z"
              fill="currentColor"
            />
          </svg>
        );
    }
  };

  return (
    <motion.div
      className={toastClasses}
      custom={position}
      variants={toastVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      layout
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.2}
      onDragEnd={(_, info) => {
        if (Math.abs(info.offset.x) > 100) {
          onClose(id);
        }
      }}
    >
      {/* Icon */}
      <div className="ds-toast__icon">
        {getIcon()}
      </div>

      {/* Content */}
      <div className="ds-toast__content">
        <h4 className="ds-toast__title">{title}</h4>
        {description && (
          <p className="ds-toast__description">{description}</p>
        )}
        {action && (
          <button
            className="ds-toast__action"
            onClick={action.onClick}
          >
            {action.label}
          </button>
        )}
      </div>

      {/* Close Button */}
      <motion.button
        className="ds-toast__close"
        onClick={() => onClose(id)}
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

      {/* Progress Bar */}
      {duration > 0 && (
        <motion.div
          className="ds-toast__progress"
          custom={duration}
          variants={progressVariants}
          initial="initial"
          animate="animate"
        />
      )}
    </motion.div>
  );
};

// Toast Container Component
export interface ToastContainerProps {
  toasts: ToastProps[];
  position?: ToastProps['position'];
}

export const ToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  position = 'bottom-right',
}) => {
  const containerClasses = clsx(
    'ds-toast-container',
    `ds-toast-container--${position}`,
  );

  return (
    <div className={containerClasses}>
      <AnimatePresence>
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} position={position} />
        ))}
      </AnimatePresence>
    </div>
  );
};

// Toast Hook
export const useToast = () => {
  const [toasts, setToasts] = React.useState<ToastProps[]>([]);

  const addToast = (toast: Omit<ToastProps, 'id' | 'onClose'>) => {
    const id = Date.now().toString();
    const newToast: ToastProps = {
      ...toast,
      id,
      onClose: removeToast,
    };
    setToasts((prev) => [...prev, newToast]);
    return id;
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const toast = {
    info: (title: string, options?: Partial<ToastProps>) =>
      addToast({ ...options, title, type: 'info' }),
    success: (title: string, options?: Partial<ToastProps>) =>
      addToast({ ...options, title, type: 'success' }),
    warning: (title: string, options?: Partial<ToastProps>) =>
      addToast({ ...options, title, type: 'warning' }),
    error: (title: string, options?: Partial<ToastProps>) =>
      addToast({ ...options, title, type: 'error' }),
  };

  return { toasts, toast };
};