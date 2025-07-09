import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './Ripple.css';

interface RippleData {
  x: number;
  y: number;
  size: number;
  id: number;
}

export const Ripple: React.FC = () => {
  const [ripples, setRipples] = useState<RippleData[]>([]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const button = (e.currentTarget as HTMLElement).getBoundingClientRect();
      const size = Math.max(button.width, button.height) * 2;
      const x = e.clientX - button.left - size / 2;
      const y = e.clientY - button.top - size / 2;

      const newRipple: RippleData = {
        x,
        y,
        size,
        id: Date.now(),
      };

      setRipples((prev) => [...prev, newRipple]);
    };

    const parent = document.currentScript?.parentElement;
    if (parent) {
      parent.addEventListener('click', handleClick);
      return () => parent.removeEventListener('click', handleClick);
    }
  }, []);

  const removeRipple = (id: number) => {
    setRipples((prev) => prev.filter((ripple) => ripple.id !== id));
  };

  return (
    <span className="ds-ripple-container" aria-hidden="true">
      <AnimatePresence>
        {ripples.map((ripple) => (
          <motion.span
            key={ripple.id}
            className="ds-ripple"
            initial={{ scale: 0, opacity: 0.5 }}
            animate={{ scale: 1, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{
              duration: 0.6,
              ease: [0.4, 0, 0.2, 1],
            }}
            onAnimationComplete={() => removeRipple(ripple.id)}
            style={{
              left: ripple.x,
              top: ripple.y,
              width: ripple.size,
              height: ripple.size,
            }}
          />
        ))}
      </AnimatePresence>
    </span>
  );
};

// Hook version for more control
export const useRipple = () => {
  const [ripples, setRipples] = useState<RippleData[]>([]);

  const createRipple = (event: React.MouseEvent<HTMLElement>) => {
    const button = event.currentTarget.getBoundingClientRect();
    const size = Math.max(button.width, button.height) * 2;
    const x = event.clientX - button.left - size / 2;
    const y = event.clientY - button.top - size / 2;

    const newRipple: RippleData = {
      x,
      y,
      size,
      id: Date.now(),
    };

    setRipples((prev) => [...prev, newRipple]);

    // Auto-remove after animation
    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== newRipple.id));
    }, 600);
  };

  const rippleComponent = (
    <span className="ds-ripple-container" aria-hidden="true">
      <AnimatePresence>
        {ripples.map((ripple) => (
          <motion.span
            key={ripple.id}
            className="ds-ripple"
            initial={{ scale: 0, opacity: 0.5 }}
            animate={{ scale: 1, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{
              duration: 0.6,
              ease: [0.4, 0, 0.2, 1],
            }}
            style={{
              left: ripple.x,
              top: ripple.y,
              width: ripple.size,
              height: ripple.size,
            }}
          />
        ))}
      </AnimatePresence>
    </span>
  );

  return { createRipple, rippleComponent };
};