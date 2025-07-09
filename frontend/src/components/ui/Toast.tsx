import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import clsx from 'clsx';
import { X, CheckCircle, AlertCircle, Info, XCircle } from 'lucide-react';

export interface ToastProps {
  id: string;
  title?: string;
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  onClose: (id: string) => void;
}

const icons = {
  success: <CheckCircle className="w-5 h-5" />,
  error: <XCircle className="w-5 h-5" />,
  warning: <AlertCircle className="w-5 h-5" />,
  info: <Info className="w-5 h-5" />,
};

const styles = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
};

const iconStyles = {
  success: 'text-green-500',
  error: 'text-red-500',
  warning: 'text-yellow-500',
  info: 'text-blue-500',
};

export const Toast: React.FC<ToastProps> = ({
  id,
  title,
  message,
  type = 'info',
  duration = 5000,
  action,
  onClose,
}) => {
  const [isExiting, setIsExiting] = useState(false);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    if (duration > 0) {
      const interval = setInterval(() => {
        setProgress((prev) => {
          const next = prev - (100 / (duration / 100));
          if (next <= 0) {
            handleClose();
            return 0;
          }
          return next;
        });
      }, 100);

      return () => clearInterval(interval);
    }
  }, [duration]);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => onClose(id), 300);
  };

  return (
    <div
      className={clsx(
        'relative max-w-sm w-full pointer-events-auto',
        'transform transition-all duration-300 ease-out',
        isExiting
          ? 'translate-x-full opacity-0'
          : 'translate-x-0 opacity-100'
      )}
    >
      <div className={clsx(
        'relative rounded-lg border shadow-lg overflow-hidden',
        styles[type]
      )}>
        {/* Progress bar */}
        {duration > 0 && (
          <div className="absolute top-0 left-0 h-1 bg-black/10 w-full">
            <div
              className="h-full bg-current opacity-30 transition-all duration-100"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        <div className="p-4">
          <div className="flex items-start">
            <div className={clsx('flex-shrink-0', iconStyles[type])}>
              {icons[type]}
            </div>
            
            <div className="ml-3 flex-1">
              {title && (
                <h3 className="text-sm font-semibold mb-1">{title}</h3>
              )}
              <p className="text-sm">{message}</p>
              
              {action && (
                <button
                  onClick={action.onClick}
                  className="mt-2 text-sm font-medium underline hover:no-underline"
                >
                  {action.label}
                </button>
              )}
            </div>
            
            <button
              onClick={handleClose}
              className="ml-4 flex-shrink-0 text-current opacity-50 hover:opacity-100 transition-opacity"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Toast container component
export const ToastContainer: React.FC<{
  toasts: ToastProps[];
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
}> = ({ toasts, position = 'top-right' }) => {
  const positionStyles = {
    'top-right': 'top-0 right-0',
    'top-left': 'top-0 left-0',
    'bottom-right': 'bottom-0 right-0',
    'bottom-left': 'bottom-0 left-0',
    'top-center': 'top-0 left-1/2 -translate-x-1/2',
    'bottom-center': 'bottom-0 left-1/2 -translate-x-1/2',
  };

  return createPortal(
    <div
      className={clsx(
        'fixed z-50 p-4 pointer-events-none',
        positionStyles[position]
      )}
    >
      <div className="space-y-4">
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} />
        ))}
      </div>
    </div>,
    document.body
  );
};

// Toast hook
export const useToast = () => {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

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
    success: (message: string, options?: Partial<ToastProps>) => 
      addToast({ ...options, message, type: 'success' }),
    error: (message: string, options?: Partial<ToastProps>) => 
      addToast({ ...options, message, type: 'error' }),
    warning: (message: string, options?: Partial<ToastProps>) => 
      addToast({ ...options, message, type: 'warning' }),
    info: (message: string, options?: Partial<ToastProps>) => 
      addToast({ ...options, message, type: 'info' }),
  };

  return { toasts, toast };
};