// Design System - Typography Tokens
// Comprehensive typography system with fluid scales

export const typography = {
  // Font families
  fontFamily: {
    sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
    mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', 'monospace'],
    display: ['Poppins', 'Inter', 'sans-serif'],
  },

  // Font sizes with fluid scaling
  fontSize: {
    // Base sizes
    '2xs': 'clamp(0.625rem, 0.5rem + 0.5vw, 0.75rem)',    // 10-12px
    xs: 'clamp(0.75rem, 0.625rem + 0.5vw, 0.875rem)',     // 12-14px
    sm: 'clamp(0.875rem, 0.75rem + 0.5vw, 1rem)',         // 14-16px
    base: 'clamp(1rem, 0.875rem + 0.5vw, 1.125rem)',      // 16-18px
    lg: 'clamp(1.125rem, 1rem + 0.5vw, 1.25rem)',         // 18-20px
    xl: 'clamp(1.25rem, 1.125rem + 0.5vw, 1.5rem)',       // 20-24px
    '2xl': 'clamp(1.5rem, 1.25rem + 1vw, 1.875rem)',      // 24-30px
    '3xl': 'clamp(1.875rem, 1.5rem + 1.5vw, 2.25rem)',    // 30-36px
    '4xl': 'clamp(2.25rem, 1.875rem + 1.5vw, 3rem)',      // 36-48px
    '5xl': 'clamp(3rem, 2.25rem + 3vw, 4rem)',            // 48-64px
    '6xl': 'clamp(4rem, 3rem + 4vw, 6rem)',               // 64-96px
  },

  // Line heights
  lineHeight: {
    none: '1',
    tight: '1.25',
    snug: '1.375',
    normal: '1.5',
    relaxed: '1.625',
    loose: '1.75',
    body: '1.75',
    heading: '1.2',
  },

  // Font weights
  fontWeight: {
    thin: '100',
    extralight: '200',
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
    black: '900',
  },

  // Letter spacing
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
    heading: '-0.02em',
    body: '0',
    caps: '0.05em',
  },

  // Text styles (predefined combinations)
  textStyles: {
    // Display
    'display-large': {
      fontFamily: 'var(--font-family-display)',
      fontSize: 'var(--font-size-6xl)',
      fontWeight: 'var(--font-weight-bold)',
      lineHeight: 'var(--line-height-heading)',
      letterSpacing: 'var(--letter-spacing-heading)',
    },
    'display-medium': {
      fontFamily: 'var(--font-family-display)',
      fontSize: 'var(--font-size-5xl)',
      fontWeight: 'var(--font-weight-semibold)',
      lineHeight: 'var(--line-height-heading)',
      letterSpacing: 'var(--letter-spacing-heading)',
    },
    'display-small': {
      fontFamily: 'var(--font-family-display)',
      fontSize: 'var(--font-size-4xl)',
      fontWeight: 'var(--font-weight-semibold)',
      lineHeight: 'var(--line-height-heading)',
      letterSpacing: 'var(--letter-spacing-heading)',
    },

    // Headings
    h1: {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-3xl)',
      fontWeight: 'var(--font-weight-bold)',
      lineHeight: 'var(--line-height-heading)',
      letterSpacing: 'var(--letter-spacing-heading)',
    },
    h2: {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-2xl)',
      fontWeight: 'var(--font-weight-semibold)',
      lineHeight: 'var(--line-height-heading)',
      letterSpacing: 'var(--letter-spacing-heading)',
    },
    h3: {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-xl)',
      fontWeight: 'var(--font-weight-semibold)',
      lineHeight: 'var(--line-height-heading)',
      letterSpacing: 'var(--letter-spacing-normal)',
    },
    h4: {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-lg)',
      fontWeight: 'var(--font-weight-semibold)',
      lineHeight: 'var(--line-height-normal)',
      letterSpacing: 'var(--letter-spacing-normal)',
    },
    h5: {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-base)',
      fontWeight: 'var(--font-weight-semibold)',
      lineHeight: 'var(--line-height-normal)',
      letterSpacing: 'var(--letter-spacing-normal)',
    },
    h6: {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-sm)',
      fontWeight: 'var(--font-weight-semibold)',
      lineHeight: 'var(--line-height-normal)',
      letterSpacing: 'var(--letter-spacing-wide)',
      textTransform: 'uppercase',
    },

    // Body
    'body-large': {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-lg)',
      fontWeight: 'var(--font-weight-normal)',
      lineHeight: 'var(--line-height-body)',
      letterSpacing: 'var(--letter-spacing-body)',
    },
    'body-regular': {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-base)',
      fontWeight: 'var(--font-weight-normal)',
      lineHeight: 'var(--line-height-body)',
      letterSpacing: 'var(--letter-spacing-body)',
    },
    'body-small': {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-sm)',
      fontWeight: 'var(--font-weight-normal)',
      lineHeight: 'var(--line-height-normal)',
      letterSpacing: 'var(--letter-spacing-body)',
    },

    // Special
    label: {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-sm)',
      fontWeight: 'var(--font-weight-medium)',
      lineHeight: 'var(--line-height-normal)',
      letterSpacing: 'var(--letter-spacing-normal)',
    },
    caption: {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-xs)',
      fontWeight: 'var(--font-weight-normal)',
      lineHeight: 'var(--line-height-normal)',
      letterSpacing: 'var(--letter-spacing-normal)',
    },
    overline: {
      fontFamily: 'var(--font-family-sans)',
      fontSize: 'var(--font-size-xs)',
      fontWeight: 'var(--font-weight-semibold)',
      lineHeight: 'var(--line-height-normal)',
      letterSpacing: 'var(--letter-spacing-caps)',
      textTransform: 'uppercase',
    },
    code: {
      fontFamily: 'var(--font-family-mono)',
      fontSize: 'var(--font-size-sm)',
      fontWeight: 'var(--font-weight-normal)',
      lineHeight: 'var(--line-height-normal)',
      letterSpacing: 'var(--letter-spacing-normal)',
    },
  },
};

// CSS Custom Properties Generator
export const generateTypographyTokens = () => {
  const tokens: Record<string, string> = {};

  // Generate font family tokens
  Object.entries(typography.fontFamily).forEach(([key, value]) => {
    tokens[`--font-family-${key}`] = value.join(', ');
  });

  // Generate other typography tokens
  ['fontSize', 'lineHeight', 'fontWeight', 'letterSpacing'].forEach((category) => {
    Object.entries(typography[category as keyof typeof typography]).forEach(([key, value]) => {
      tokens[`--${category.replace(/([A-Z])/g, '-$1').toLowerCase()}-${key}`] = value as string;
    });
  });

  return tokens;
};