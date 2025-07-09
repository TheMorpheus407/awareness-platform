// Design System - Border Tokens
// Border radius, width, and style system

export const borders = {
  // Border radius
  radius: {
    none: '0',
    sm: '0.125rem',     // 2px
    base: '0.25rem',    // 4px
    md: '0.375rem',     // 6px
    lg: '0.5rem',       // 8px
    xl: '0.75rem',      // 12px
    '2xl': '1rem',      // 16px
    '3xl': '1.5rem',    // 24px
    full: '9999px',     // Pill shape
    circle: '50%',      // Perfect circle
  },

  // Border width
  width: {
    0: '0',
    1: '1px',
    2: '2px',
    4: '4px',
    8: '8px',
  },

  // Border styles
  style: {
    solid: 'solid',
    dashed: 'dashed',
    dotted: 'dotted',
    double: 'double',
    none: 'none',
  },

  // Component-specific borders
  components: {
    // Button borders
    button: {
      radius: {
        sm: 'var(--radius-md)',
        md: 'var(--radius-lg)',
        lg: 'var(--radius-xl)',
        pill: 'var(--radius-full)',
      },
      width: {
        default: 'var(--border-width-1)',
        thick: 'var(--border-width-2)',
      },
    },

    // Card borders
    card: {
      radius: {
        sm: 'var(--radius-lg)',
        md: 'var(--radius-xl)',
        lg: 'var(--radius-2xl)',
      },
      width: 'var(--border-width-1)',
    },

    // Input borders
    input: {
      radius: {
        sm: 'var(--radius-md)',
        md: 'var(--radius-lg)',
        lg: 'var(--radius-xl)',
      },
      width: {
        default: 'var(--border-width-1)',
        focus: 'var(--border-width-2)',
      },
    },

    // Modal borders
    modal: {
      radius: 'var(--radius-xl)',
      width: 'var(--border-width-1)',
    },

    // Avatar borders
    avatar: {
      radius: {
        square: 'var(--radius-lg)',
        rounded: 'var(--radius-3xl)',
        circle: 'var(--radius-circle)',
      },
      width: 'var(--border-width-2)',
    },

    // Badge borders
    badge: {
      radius: {
        default: 'var(--radius-md)',
        pill: 'var(--radius-full)',
      },
      width: 'var(--border-width-1)',
    },

    // Table borders
    table: {
      radius: 'var(--radius-lg)',
      width: 'var(--border-width-1)',
    },
  },

  // Special border effects
  effects: {
    // Gradient borders
    gradient: {
      primary: 'linear-gradient(135deg, #0ea5e9 0%, #a855f7 100%)',
      secondary: 'linear-gradient(135deg, #a855f7 0%, #f59e0b 100%)',
      accent: 'linear-gradient(135deg, #f59e0b 0%, #dc2626 100%)',
      rainbow: 'linear-gradient(135deg, #dc2626 0%, #f59e0b 25%, #10b981 50%, #0ea5e9 75%, #a855f7 100%)',
    },

    // Animated borders
    animated: {
      pulse: {
        animation: 'border-pulse 2s ease-in-out infinite',
      },
      spin: {
        animation: 'border-spin 3s linear infinite',
      },
      glow: {
        animation: 'border-glow 2s ease-in-out infinite',
      },
    },
  },

  // Border colors (references color tokens)
  colors: {
    default: 'var(--color-neutral-200)',
    light: 'var(--color-neutral-100)',
    medium: 'var(--color-neutral-300)',
    dark: 'var(--color-neutral-400)',
    transparent: 'transparent',
    current: 'currentColor',

    // Interactive states
    hover: 'var(--color-neutral-300)',
    focus: 'var(--color-brand-primary-500)',
    active: 'var(--color-brand-primary-600)',
    disabled: 'var(--color-neutral-200)',

    // Validation states
    error: 'var(--color-semantic-error-DEFAULT)',
    warning: 'var(--color-semantic-warning-DEFAULT)',
    success: 'var(--color-semantic-success-DEFAULT)',
    info: 'var(--color-semantic-info-DEFAULT)',
  },
};

// CSS Custom Properties Generator
export const generateBorderTokens = () => {
  const tokens: Record<string, string> = {};

  // Generate radius tokens
  Object.entries(borders.radius).forEach(([key, value]) => {
    tokens[`--radius-${key}`] = value;
  });

  // Generate width tokens
  Object.entries(borders.width).forEach(([key, value]) => {
    tokens[`--border-width-${key}`] = value;
  });

  // Generate style tokens
  Object.entries(borders.style).forEach(([key, value]) => {
    tokens[`--border-style-${key}`] = value;
  });

  // Generate color tokens
  Object.entries(borders.colors).forEach(([key, value]) => {
    tokens[`--border-color-${key}`] = value;
  });

  return tokens;
};