import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import clsx from 'clsx';

export interface TooltipProps {
  children: React.ReactElement;
  content: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  arrow?: boolean;
  className?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({
  children,
  content,
  position = 'top',
  delay = 200,
  arrow = true,
  className,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect();
        const scrollY = window.scrollY;
        const scrollX = window.scrollX;

        let x = 0;
        let y = 0;

        switch (position) {
          case 'top':
            x = rect.left + rect.width / 2 + scrollX;
            y = rect.top + scrollY;
            break;
          case 'bottom':
            x = rect.left + rect.width / 2 + scrollX;
            y = rect.bottom + scrollY;
            break;
          case 'left':
            x = rect.left + scrollX;
            y = rect.top + rect.height / 2 + scrollY;
            break;
          case 'right':
            x = rect.right + scrollX;
            y = rect.top + rect.height / 2 + scrollY;
            break;
        }

        setCoords({ x, y });
        setIsVisible(true);
      }
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  const getTooltipStyles = () => {
    if (!tooltipRef.current) return {};

    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    let transform = '';

    switch (position) {
      case 'top':
        transform = `translate(-50%, calc(-100% - 8px))`;
        break;
      case 'bottom':
        transform = `translate(-50%, 8px)`;
        break;
      case 'left':
        transform = `translate(calc(-100% - 8px), -50%)`;
        break;
      case 'right':
        transform = `translate(8px, -50%)`;
        break;
    }

    return {
      left: `${coords.x}px`,
      top: `${coords.y}px`,
      transform,
    };
  };

  const arrowStyles = {
    top: 'bottom-[-4px] left-1/2 -translate-x-1/2 border-t-gray-900 border-x-transparent border-b-transparent',
    bottom: 'top-[-4px] left-1/2 -translate-x-1/2 border-b-gray-900 border-x-transparent border-t-transparent',
    left: 'right-[-4px] top-1/2 -translate-y-1/2 border-l-gray-900 border-y-transparent border-r-transparent',
    right: 'left-[-4px] top-1/2 -translate-y-1/2 border-r-gray-900 border-y-transparent border-l-transparent',
  };

  return (
    <>
      {React.cloneElement(children, {
        ref: triggerRef,
        onMouseEnter: showTooltip,
        onMouseLeave: hideTooltip,
        onFocus: showTooltip,
        onBlur: hideTooltip,
      })}
      
      {isVisible && content && createPortal(
        <div
          ref={tooltipRef}
          className={clsx(
            'fixed z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg pointer-events-none',
            'transition-opacity duration-200',
            isVisible ? 'opacity-100' : 'opacity-0',
            className
          )}
          style={getTooltipStyles()}
        >
          {content}
          {arrow && (
            <div
              className={clsx(
                'absolute w-0 h-0 border-4',
                arrowStyles[position]
              )}
            />
          )}
        </div>,
        document.body
      )}
    </>
  );
};

// Simplified tooltip for quick use
export const SimpleTooltip: React.FC<{
  title: string;
  children: React.ReactElement;
  position?: 'top' | 'bottom' | 'left' | 'right';
}> = ({ title, children, position = 'top' }) => (
  <Tooltip content={title} position={position}>
    {children}
  </Tooltip>
);