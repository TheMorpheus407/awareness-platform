// Design System - Color Tokens
// Semantic color system with support for light/dark modes

export const colors = {
  // Brand Colors
  brand: {
    primary: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      200: '#bae6fd',
      300: '#7dd3fc',
      400: '#38bdf8',
      500: '#0ea5e9', // Main brand color
      600: '#0284c7',
      700: '#0369a1',
      800: '#075985',
      900: '#0c4a6e',
      950: '#082f49',
    },
    secondary: {
      50: '#faf5ff',
      100: '#f3e8ff',
      200: '#e9d5ff',
      300: '#d8b4fe',
      400: '#c084fc',
      500: '#a855f7',
      600: '#9333ea',
      700: '#7c3aed',
      800: '#6b21a8',
      900: '#581c87',
      950: '#3b0764',
    },
    accent: {
      50: '#fef3c7',
      100: '#fde68a',
      200: '#fcd34d',
      300: '#fbbf24',
      400: '#f59e0b',
      500: '#d97706',
      600: '#b45309',
      700: '#92400e',
      800: '#78350f',
      900: '#451a03',
    },
  },

  // Semantic Colors
  semantic: {
    success: {
      light: '#10b981',
      DEFAULT: '#059669',
      dark: '#047857',
      bg: '#d1fae5',
      border: '#6ee7b7',
    },
    warning: {
      light: '#f59e0b',
      DEFAULT: '#d97706',
      dark: '#b45309',
      bg: '#fef3c7',
      border: '#fcd34d',
    },
    error: {
      light: '#f87171',
      DEFAULT: '#dc2626',
      dark: '#b91c1c',
      bg: '#fee2e2',
      border: '#fca5a5',
    },
    info: {
      light: '#60a5fa',
      DEFAULT: '#3b82f6',
      dark: '#2563eb',
      bg: '#dbeafe',
      border: '#93c5fd',
    },
  },

  // Neutral Colors
  neutral: {
    0: '#ffffff',
    50: '#fafafa',
    100: '#f4f4f5',
    200: '#e4e4e7',
    300: '#d4d4d8',
    400: '#a1a1aa',
    500: '#71717a',
    600: '#52525b',
    700: '#3f3f46',
    800: '#27272a',
    900: '#18181b',
    950: '#09090b',
    1000: '#000000',
  },

  // Special Purpose
  surface: {
    primary: 'var(--color-neutral-0)',
    secondary: 'var(--color-neutral-50)',
    tertiary: 'var(--color-neutral-100)',
    inverse: 'var(--color-neutral-900)',
  },

  text: {
    primary: 'var(--color-neutral-900)',
    secondary: 'var(--color-neutral-600)',
    tertiary: 'var(--color-neutral-500)',
    disabled: 'var(--color-neutral-400)',
    inverse: 'var(--color-neutral-0)',
  },

  // Dark mode overrides
  dark: {
    surface: {
      primary: 'var(--color-neutral-900)',
      secondary: 'var(--color-neutral-800)',
      tertiary: 'var(--color-neutral-700)',
      inverse: 'var(--color-neutral-0)',
    },
    text: {
      primary: 'var(--color-neutral-0)',
      secondary: 'var(--color-neutral-300)',
      tertiary: 'var(--color-neutral-400)',
      disabled: 'var(--color-neutral-600)',
      inverse: 'var(--color-neutral-900)',
    },
  },
};

// CSS Custom Properties Generator
export const generateColorTokens = () => {
  const tokens: Record<string, string> = {};

  // Flatten color object
  const flattenColors = (obj: any, prefix = '') => {
    Object.keys(obj).forEach((key) => {
      const value = obj[key];
      const tokenName = prefix ? `${prefix}-${key}` : key;

      if (typeof value === 'string') {
        tokens[`--color-${tokenName}`] = value;
      } else {
        flattenColors(value, tokenName);
      }
    });
  };

  flattenColors(colors);
  return tokens;
};