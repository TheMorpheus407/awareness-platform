// Design System - Animation Tokens
// Motion design principles and timing functions

export const animation = {
  // Duration scales
  duration: {
    instant: '0ms',
    fast: '150ms',
    normal: '250ms',
    slow: '350ms',
    slower: '500ms',
    slowest: '1000ms',
    // Specific use cases
    enter: '250ms',
    exit: '200ms',
    complex: '350ms',
    // Micro-interactions
    micro: '100ms',
    ripple: '600ms',
    skeleton: '1500ms',
    pulse: '2000ms',
  },

  // Easing functions
  easing: {
    // Basic easings
    linear: 'linear',
    ease: 'ease',
    easeIn: 'ease-in',
    easeOut: 'ease-out',
    easeInOut: 'ease-in-out',

    // Custom cubic-bezier easings
    smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',         // Material Design standard
    smoothIn: 'cubic-bezier(0.4, 0, 1, 1)',         // Accelerate
    smoothOut: 'cubic-bezier(0, 0, 0.2, 1)',        // Decelerate
    smoothInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',    // Standard

    // Expressive easings
    spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',     // Overshoot
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',      // Elastic
    elastic: 'cubic-bezier(0.645, 0.045, 0.355, 1)',       // Subtle spring
    anticipate: 'cubic-bezier(0.4, 0, 0.2, 1.4)',          // Build anticipation

    // UI-specific easings
    menu: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
    modal: 'cubic-bezier(0.4, 0, 0.2, 1)',
    drawer: 'cubic-bezier(0.4, 0, 0.6, 1)',
    fab: 'cubic-bezier(0.4, 0, 0.2, 1.4)',
  },

  // Predefined animations
  keyframes: {
    // Fade animations
    fadeIn: {
      from: { opacity: '0' },
      to: { opacity: '1' },
    },
    fadeOut: {
      from: { opacity: '1' },
      to: { opacity: '0' },
    },
    fadeInUp: {
      from: { 
        opacity: '0',
        transform: 'translateY(20px)',
      },
      to: { 
        opacity: '1',
        transform: 'translateY(0)',
      },
    },
    fadeInDown: {
      from: { 
        opacity: '0',
        transform: 'translateY(-20px)',
      },
      to: { 
        opacity: '1',
        transform: 'translateY(0)',
      },
    },

    // Scale animations
    scaleIn: {
      from: { 
        opacity: '0',
        transform: 'scale(0.9)',
      },
      to: { 
        opacity: '1',
        transform: 'scale(1)',
      },
    },
    scaleOut: {
      from: { 
        opacity: '1',
        transform: 'scale(1)',
      },
      to: { 
        opacity: '0',
        transform: 'scale(0.9)',
      },
    },
    scalePulse: {
      '0%': { transform: 'scale(1)' },
      '50%': { transform: 'scale(1.05)' },
      '100%': { transform: 'scale(1)' },
    },

    // Slide animations
    slideInRight: {
      from: { 
        transform: 'translateX(100%)',
        opacity: '0',
      },
      to: { 
        transform: 'translateX(0)',
        opacity: '1',
      },
    },
    slideInLeft: {
      from: { 
        transform: 'translateX(-100%)',
        opacity: '0',
      },
      to: { 
        transform: 'translateX(0)',
        opacity: '1',
      },
    },
    slideInUp: {
      from: { 
        transform: 'translateY(100%)',
        opacity: '0',
      },
      to: { 
        transform: 'translateY(0)',
        opacity: '1',
      },
    },

    // Rotation animations
    spin: {
      from: { transform: 'rotate(0deg)' },
      to: { transform: 'rotate(360deg)' },
    },
    spinReverse: {
      from: { transform: 'rotate(360deg)' },
      to: { transform: 'rotate(0deg)' },
    },

    // Special effects
    shimmer: {
      '0%': {
        backgroundPosition: '-200% 0',
      },
      '100%': {
        backgroundPosition: '200% 0',
      },
    },
    ripple: {
      '0%': {
        transform: 'scale(0)',
        opacity: '1',
      },
      '100%': {
        transform: 'scale(4)',
        opacity: '0',
      },
    },
    bounce: {
      '0%, 100%': {
        transform: 'translateY(0)',
      },
      '50%': {
        transform: 'translateY(-20px)',
      },
    },
    shake: {
      '0%, 100%': { transform: 'translateX(0)' },
      '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-2px)' },
      '20%, 40%, 60%, 80%': { transform: 'translateX(2px)' },
    },
    pulse: {
      '0%': {
        opacity: '1',
        transform: 'scale(1)',
      },
      '50%': {
        opacity: '0.8',
        transform: 'scale(0.98)',
      },
      '100%': {
        opacity: '1',
        transform: 'scale(1)',
      },
    },
    glow: {
      '0%, 100%': {
        boxShadow: '0 0 20px rgba(14, 165, 233, 0.5)',
      },
      '50%': {
        boxShadow: '0 0 30px rgba(14, 165, 233, 0.8)',
      },
    },
  },

  // Transition properties
  transition: {
    // Common transitions
    all: 'all var(--duration-normal) var(--easing-smooth)',
    opacity: 'opacity var(--duration-fast) var(--easing-smooth)',
    transform: 'transform var(--duration-normal) var(--easing-smooth)',
    colors: 'background-color var(--duration-normal) var(--easing-smooth), border-color var(--duration-normal) var(--easing-smooth), color var(--duration-normal) var(--easing-smooth)',
    shadow: 'box-shadow var(--duration-normal) var(--easing-smooth)',
    
    // Component-specific
    button: 'all var(--duration-fast) var(--easing-smooth)',
    input: 'border-color var(--duration-fast) var(--easing-smooth), box-shadow var(--duration-fast) var(--easing-smooth)',
    card: 'transform var(--duration-normal) var(--easing-smooth), box-shadow var(--duration-normal) var(--easing-smooth)',
    modal: 'opacity var(--duration-normal) var(--easing-smooth), transform var(--duration-normal) var(--easing-modal)',
    drawer: 'transform var(--duration-slow) var(--easing-drawer)',
    dropdown: 'opacity var(--duration-fast) var(--easing-smoothOut), transform var(--duration-fast) var(--easing-smoothOut)',
  },

  // Animation compositions
  compositions: {
    // Entrance animations
    enterBottom: {
      animation: 'fadeInUp var(--duration-enter) var(--easing-smoothOut) both',
    },
    enterTop: {
      animation: 'fadeInDown var(--duration-enter) var(--easing-smoothOut) both',
    },
    enterScale: {
      animation: 'scaleIn var(--duration-enter) var(--easing-smoothOut) both',
    },
    
    // Exit animations
    exitScale: {
      animation: 'scaleOut var(--duration-exit) var(--easing-smoothIn) both',
    },
    exitFade: {
      animation: 'fadeOut var(--duration-exit) var(--easing-smoothIn) both',
    },

    // Loading animations
    loading: {
      animation: 'spin var(--duration-slowest) linear infinite',
    },
    skeleton: {
      animation: 'shimmer var(--duration-skeleton) var(--easing-linear) infinite',
      background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.1) 50%, transparent 100%)',
      backgroundSize: '200% 100%',
    },
    pulse: {
      animation: 'pulse var(--duration-pulse) var(--easing-smoothInOut) infinite',
    },

    // Micro-interactions
    hover: {
      transform: 'translateY(-2px)',
      transition: 'var(--transition-transform)',
    },
    press: {
      transform: 'scale(0.98)',
      transition: 'transform var(--duration-micro) var(--easing-smoothOut)',
    },
    focus: {
      boxShadow: '0 0 0 3px rgba(14, 165, 233, 0.2)',
      transition: 'var(--transition-shadow)',
    },
  },
};

// CSS Custom Properties Generator
export const generateAnimationTokens = () => {
  const tokens: Record<string, string> = {};

  // Generate duration tokens
  Object.entries(animation.duration).forEach(([key, value]) => {
    tokens[`--duration-${key}`] = value;
  });

  // Generate easing tokens
  Object.entries(animation.easing).forEach(([key, value]) => {
    tokens[`--easing-${key}`] = value;
  });

  // Generate transition tokens
  Object.entries(animation.transition).forEach(([key, value]) => {
    tokens[`--transition-${key}`] = value;
  });

  return tokens;
};