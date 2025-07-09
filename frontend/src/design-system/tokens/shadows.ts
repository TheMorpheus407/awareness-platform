// Design System - Shadow Tokens
// Elevation and depth system

export const shadows = {
  // Elevation levels (Material Design inspired)
  elevation: {
    0: 'none',
    1: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    2: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    3: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    4: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    5: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    6: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  },

  // Component-specific shadows
  components: {
    // Card shadows
    card: {
      default: 'var(--shadow-elevation-2)',
      hover: 'var(--shadow-elevation-4)',
      active: 'var(--shadow-elevation-1)',
    },

    // Button shadows
    button: {
      default: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      hover: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      active: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
      focus: '0 0 0 3px rgba(14, 165, 233, 0.2)',
    },

    // Input shadows
    input: {
      default: 'inset 0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      focus: '0 0 0 3px rgba(14, 165, 233, 0.1)',
      error: '0 0 0 3px rgba(220, 38, 38, 0.1)',
      success: '0 0 0 3px rgba(5, 150, 105, 0.1)',
    },

    // Modal/Dialog shadows
    modal: {
      backdrop: 'rgba(0, 0, 0, 0.5)',
      content: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    },

    // Dropdown shadows
    dropdown: {
      default: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    },

    // Tooltip shadows
    tooltip: {
      default: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },

  // Special effect shadows
  effects: {
    // Glow effects
    glow: {
      primary: '0 0 20px rgba(14, 165, 233, 0.3)',
      success: '0 0 20px rgba(5, 150, 105, 0.3)',
      warning: '0 0 20px rgba(217, 119, 6, 0.3)',
      error: '0 0 20px rgba(220, 38, 38, 0.3)',
    },

    // Inner shadows
    inner: {
      sm: 'inset 0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      md: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
      lg: 'inset 0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    },

    // Colored shadows (for branding)
    colored: {
      primary: '0 10px 25px -5px rgba(14, 165, 233, 0.25)',
      secondary: '0 10px 25px -5px rgba(168, 85, 247, 0.25)',
      accent: '0 10px 25px -5px rgba(245, 158, 11, 0.25)',
    },

    // Neumorphic shadows
    neumorphic: {
      flat: '5px 5px 10px rgba(0, 0, 0, 0.1), -5px -5px 10px rgba(255, 255, 255, 0.1)',
      concave: 'inset 5px 5px 10px rgba(0, 0, 0, 0.1), inset -5px -5px 10px rgba(255, 255, 255, 0.1)',
      convex: '5px 5px 10px rgba(0, 0, 0, 0.1), -5px -5px 10px rgba(255, 255, 255, 0.1)',
    },
  },

  // Dark mode shadows (with adjusted opacity)
  dark: {
    elevation: {
      0: 'none',
      1: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
      2: '0 1px 3px 0 rgba(0, 0, 0, 0.4), 0 1px 2px 0 rgba(0, 0, 0, 0.3)',
      3: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
      4: '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
      5: '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.3)',
      6: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
    },
  },
};

// CSS Custom Properties Generator
export const generateShadowTokens = () => {
  const tokens: Record<string, string> = {};

  // Generate elevation tokens
  Object.entries(shadows.elevation).forEach(([key, value]) => {
    tokens[`--shadow-elevation-${key}`] = value;
  });

  // Generate component shadow tokens
  Object.entries(shadows.components).forEach(([component, shadows]) => {
    Object.entries(shadows).forEach(([state, value]) => {
      tokens[`--shadow-${component}-${state}`] = value;
    });
  });

  // Generate effect shadow tokens
  Object.entries(shadows.effects).forEach(([effect, shadows]) => {
    Object.entries(shadows).forEach(([variant, value]) => {
      tokens[`--shadow-${effect}-${variant}`] = value;
    });
  });

  return tokens;
};