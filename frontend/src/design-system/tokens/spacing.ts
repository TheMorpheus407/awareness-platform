// Design System - Spacing Tokens
// Consistent spacing system based on 4px grid

export const spacing = {
  // Base unit (4px)
  unit: 4,

  // Spacing scale
  scale: {
    0: '0',
    px: '1px',
    0.5: '0.125rem',  // 2px
    1: '0.25rem',     // 4px
    1.5: '0.375rem',  // 6px
    2: '0.5rem',      // 8px
    2.5: '0.625rem',  // 10px
    3: '0.75rem',     // 12px
    3.5: '0.875rem',  // 14px
    4: '1rem',        // 16px
    5: '1.25rem',     // 20px
    6: '1.5rem',      // 24px
    7: '1.75rem',     // 28px
    8: '2rem',        // 32px
    9: '2.25rem',     // 36px
    10: '2.5rem',     // 40px
    11: '2.75rem',    // 44px
    12: '3rem',       // 48px
    14: '3.5rem',     // 56px
    16: '4rem',       // 64px
    20: '5rem',       // 80px
    24: '6rem',       // 96px
    28: '7rem',       // 112px
    32: '8rem',       // 128px
    36: '9rem',       // 144px
    40: '10rem',      // 160px
    44: '11rem',      // 176px
    48: '12rem',      // 192px
    52: '13rem',      // 208px
    56: '14rem',      // 224px
    60: '15rem',      // 240px
    64: '16rem',      // 256px
    72: '18rem',      // 288px
    80: '20rem',      // 320px
    96: '24rem',      // 384px
  },

  // Component-specific spacing
  components: {
    // Button padding
    button: {
      xs: {
        x: 'var(--spacing-2)',
        y: 'var(--spacing-1)',
      },
      sm: {
        x: 'var(--spacing-3)',
        y: 'var(--spacing-1-5)',
      },
      md: {
        x: 'var(--spacing-4)',
        y: 'var(--spacing-2)',
      },
      lg: {
        x: 'var(--spacing-6)',
        y: 'var(--spacing-3)',
      },
      xl: {
        x: 'var(--spacing-8)',
        y: 'var(--spacing-4)',
      },
    },

    // Card padding
    card: {
      sm: 'var(--spacing-4)',
      md: 'var(--spacing-6)',
      lg: 'var(--spacing-8)',
    },

    // Input padding
    input: {
      sm: {
        x: 'var(--spacing-3)',
        y: 'var(--spacing-1-5)',
      },
      md: {
        x: 'var(--spacing-3)',
        y: 'var(--spacing-2)',
      },
      lg: {
        x: 'var(--spacing-4)',
        y: 'var(--spacing-3)',
      },
    },

    // Modal padding
    modal: {
      header: 'var(--spacing-6)',
      body: 'var(--spacing-6)',
      footer: 'var(--spacing-4)',
    },

    // Section spacing
    section: {
      xs: 'var(--spacing-8)',
      sm: 'var(--spacing-12)',
      md: 'var(--spacing-16)',
      lg: 'var(--spacing-24)',
      xl: 'var(--spacing-32)',
    },

    // Stack spacing (for vertical lists)
    stack: {
      xs: 'var(--spacing-1)',
      sm: 'var(--spacing-2)',
      md: 'var(--spacing-4)',
      lg: 'var(--spacing-6)',
      xl: 'var(--spacing-8)',
    },

    // Inline spacing (for horizontal lists)
    inline: {
      xs: 'var(--spacing-1)',
      sm: 'var(--spacing-2)',
      md: 'var(--spacing-3)',
      lg: 'var(--spacing-4)',
      xl: 'var(--spacing-6)',
    },
  },

  // Layout spacing
  layout: {
    gutter: {
      xs: 'var(--spacing-2)',
      sm: 'var(--spacing-4)',
      md: 'var(--spacing-6)',
      lg: 'var(--spacing-8)',
      xl: 'var(--spacing-12)',
    },
    container: {
      padding: {
        mobile: 'var(--spacing-4)',
        tablet: 'var(--spacing-6)',
        desktop: 'var(--spacing-8)',
      },
      maxWidth: {
        xs: '20rem',      // 320px
        sm: '24rem',      // 384px
        md: '28rem',      // 448px
        lg: '32rem',      // 512px
        xl: '36rem',      // 576px
        '2xl': '42rem',   // 672px
        '3xl': '48rem',   // 768px
        '4xl': '56rem',   // 896px
        '5xl': '64rem',   // 1024px
        '6xl': '72rem',   // 1152px
        '7xl': '80rem',   // 1280px
        full: '100%',
      },
    },
  },
};

// CSS Custom Properties Generator
export const generateSpacingTokens = () => {
  const tokens: Record<string, string> = {};

  // Generate spacing scale tokens
  Object.entries(spacing.scale).forEach(([key, value]) => {
    tokens[`--spacing-${key.replace('.', '-')}`] = value;
  });

  return tokens;
};