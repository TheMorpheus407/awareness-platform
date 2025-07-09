// Design System - Token Index
// Central export for all design tokens

export * from './colors';
export * from './typography';
export * from './spacing';
export * from './animation';
export * from './shadows';
export * from './borders';

import { generateColorTokens } from './colors';
import { generateTypographyTokens } from './typography';
import { generateSpacingTokens } from './spacing';
import { generateAnimationTokens } from './animation';
import { generateShadowTokens } from './shadows';
import { generateBorderTokens } from './borders';

// Generate all CSS custom properties
export const generateAllTokens = () => {
  return {
    ...generateColorTokens(),
    ...generateTypographyTokens(),
    ...generateSpacingTokens(),
    ...generateAnimationTokens(),
    ...generateShadowTokens(),
    ...generateBorderTokens(),
  };
};

// Apply tokens to document root
export const applyTokensToRoot = () => {
  const tokens = generateAllTokens();
  const root = document.documentElement;

  Object.entries(tokens).forEach(([property, value]) => {
    root.style.setProperty(property, value);
  });
};

// Theme configuration
export const themes = {
  light: {
    name: 'light',
    class: '',
  },
  dark: {
    name: 'dark',
    class: 'dark',
  },
};

// Apply theme
export const applyTheme = (theme: keyof typeof themes) => {
  const root = document.documentElement;
  
  // Remove all theme classes
  Object.values(themes).forEach((t) => {
    if (t.class) root.classList.remove(t.class);
  });

  // Add new theme class
  if (themes[theme].class) {
    root.classList.add(themes[theme].class);
  }

  // Store preference
  localStorage.setItem('theme-preference', theme);
};

// Get current theme
export const getCurrentTheme = (): keyof typeof themes => {
  const stored = localStorage.getItem('theme-preference') as keyof typeof themes;
  if (stored && themes[stored]) return stored;

  // Check system preference
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }

  return 'light';
};

// Initialize theme system
export const initializeThemeSystem = () => {
  // Apply tokens
  applyTokensToRoot();

  // Apply saved or system theme
  const currentTheme = getCurrentTheme();
  applyTheme(currentTheme);

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const stored = localStorage.getItem('theme-preference');
    if (!stored) {
      applyTheme(e.matches ? 'dark' : 'light');
    }
  });
};