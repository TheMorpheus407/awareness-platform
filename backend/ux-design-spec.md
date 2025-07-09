# UX & Design Spezifikation - Cybersecurity Awareness Platform
**Version 1.0 | Comprehensive Design System & User Experience Guidelines**

## 1. Design Principles

### 1.1 Core Principles
```yaml
Security First:
  - Clear visual hierarchy for security states
  - Immediate feedback on risky actions
  - Progressive disclosure of sensitive information

Accessibility:
  - WCAG 2.1 AA compliance
  - Keyboard navigation support
  - Screen reader optimization
  - High contrast modes

Simplicity:
  - Minimal cognitive load
  - Clear call-to-actions
  - Consistent patterns
  - Self-explanatory interfaces

Engagement:
  - Gamification elements
  - Progress visualization
  - Positive reinforcement
  - Micro-interactions
```

### 1.2 Design Philosophy
- **Trustworthy**: Professional appearance that instills confidence
- **Approachable**: Not intimidating for non-technical users
- **Motivating**: Encourages continuous learning
- **Responsive**: Seamless experience across devices

## 2. Visual Design System

### 2.1 Color Palette

```scss
// Primary Colors
$primary-50: #E3F2FD;   // Lightest
$primary-100: #BBDEFB;
$primary-200: #90CAF9;
$primary-300: #64B5F6;
$primary-400: #42A5F5;
$primary-500: #2196F3;  // Main
$primary-600: #1E88E5;
$primary-700: #1976D2;
$primary-800: #1565C0;
$primary-900: #0D47A1;  // Darkest

// Semantic Colors
$success-500: #4CAF50;  // Green
$warning-500: #FF9800;  // Orange
$danger-500: #F44336;   // Red
$info-500: #00BCD4;     // Cyan

// Neutral Colors
$gray-50: #FAFAFA;
$gray-100: #F5F5F5;
$gray-200: #EEEEEE;
$gray-300: #E0E0E0;
$gray-400: #BDBDBD;
$gray-500: #9E9E9E;
$gray-600: #757575;
$gray-700: #616161;
$gray-800: #424242;
$gray-900: #212121;

// Risk Score Colors (Gradient)
$risk-low: #4CAF50;     // 0-30
$risk-medium: #FFC107;  // 31-70
$risk-high: #F44336;    // 71-100

// Special Purpose
$phishing-alert: #FF5722;
$compliance-badge: #673AB7;
$achievement-gold: #FFD700;
```

### 2.2 Typography

```scss
// Font Stack
$font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
$font-mono: 'JetBrains Mono', 'Courier New', monospace;

// Font Sizes
$text-xs: 0.75rem;    // 12px
$text-sm: 0.875rem;   // 14px
$text-base: 1rem;     // 16px
$text-lg: 1.125rem;   // 18px
$text-xl: 1.25rem;    // 20px
$text-2xl: 1.5rem;    // 24px
$text-3xl: 1.875rem;  // 30px
$text-4xl: 2.25rem;   // 36px
$text-5xl: 3rem;      // 48px

// Font Weights
$font-normal: 400;
$font-medium: 500;
$font-semibold: 600;
$font-bold: 700;

// Line Heights
$leading-none: 1;
$leading-tight: 1.25;
$leading-normal: 1.5;
$leading-relaxed: 1.625;
$leading-loose: 2;

// Typography Scale
.heading-1 {
  font-size: $text-4xl;
  font-weight: $font-bold;
  line-height: $leading-tight;
  letter-spacing: -0.02em;
}

.heading-2 {
  font-size: $text-3xl;
  font-weight: $font-semibold;
  line-height: $leading-tight;
  letter-spacing: -0.01em;
}

.heading-3 {
  font-size: $text-2xl;
  font-weight: $font-semibold;
  line-height: $leading-normal;
}

.body-large {
  font-size: $text-lg;
  line-height: $leading-relaxed;
}

.body-base {
  font-size: $text-base;
  line-height: $leading-normal;
}

.body-small {
  font-size: $text-sm;
  line-height: $leading-normal;
}

.caption {
  font-size: $text-xs;
  line-height: $leading-normal;
  letter-spacing: 0.03em;
}
```

### 2.3 Spacing System

```scss
// 8px Grid System
$space-1: 0.25rem;   // 4px
$space-2: 0.5rem;    // 8px
$space-3: 0.75rem;   // 12px
$space-4: 1rem;      // 16px
$space-5: 1.25rem;   // 20px
$space-6: 1.5rem;    // 24px
$space-8: 2rem;      // 32px
$space-10: 2.5rem;   // 40px
$space-12: 3rem;     // 48px
$space-16: 4rem;     // 64px
$space-20: 5rem;     // 80px
$space-24: 6rem;     // 96px

// Component Spacing
$padding-xs: $space-2;
$padding-sm: $space-3;
$padding-base: $space-4;
$padding-lg: $space-6;
$padding-xl: $space-8;

// Layout Spacing
$container-padding: $space-6;
$section-gap: $space-12;
$card-padding: $space-6;
```

### 2.4 Elevation & Shadows

```scss
// Shadow System
$shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
$shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
$shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
$shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
$shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
$shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

// Elevation Levels
.elevation-0 { box-shadow: none; }
.elevation-1 { box-shadow: $shadow-sm; }  // Cards
.elevation-2 { box-shadow: $shadow-md; }  // Dropdowns
.elevation-3 { box-shadow: $shadow-lg; }  // Modals
.elevation-4 { box-shadow: $shadow-xl; }  // Popovers
```

## 3. Component Design Specifications

### 3.1 Navigation Components

#### Primary Navigation
```tsx
// Navigation Structure
interface NavigationItem {
  label: string;
  icon: IconType;
  path: string;
  badge?: {
    value: number;
    variant: 'danger' | 'warning' | 'info';
  };
}

// Visual Specs
const navigationSpecs = {
  height: '64px',
  background: 'white',
  borderBottom: '1px solid $gray-200',
  itemPadding: '$space-4 $space-6',
  activeIndicator: {
    height: '3px',
    color: '$primary-500',
    position: 'bottom'
  },
  hover: {
    background: '$gray-50',
    transition: 'background 200ms ease'
  }
};
```

#### Sidebar Navigation (Desktop)
```scss
.sidebar {
  width: 260px;
  background: $gray-50;
  border-right: 1px solid $gray-200;
  
  &-item {
    display: flex;
    align-items: center;
    padding: $space-3 $space-4;
    margin: $space-1 $space-2;
    border-radius: 8px;
    transition: all 200ms ease;
    
    &:hover {
      background: $gray-100;
    }
    
    &.active {
      background: $primary-50;
      color: $primary-700;
      font-weight: $font-semibold;
    }
  }
  
  &-icon {
    width: 20px;
    height: 20px;
    margin-right: $space-3;
  }
}
```

### 3.2 Card Components

```tsx
// Card Variants
interface CardProps {
  variant: 'default' | 'interactive' | 'stat' | 'course';
  elevation?: 0 | 1 | 2 | 3;
  padding?: 'sm' | 'md' | 'lg';
  hover?: boolean;
}

// Card Styles
const cardStyles = {
  default: {
    background: 'white',
    borderRadius: '12px',
    padding: '$card-padding',
    border: '1px solid $gray-200',
    transition: 'all 200ms ease'
  },
  interactive: {
    cursor: 'pointer',
    '&:hover': {
      transform: 'translateY(-2px)',
      boxShadow: '$shadow-md'
    }
  },
  stat: {
    display: 'flex',
    flexDirection: 'column',
    gap: '$space-2',
    '.stat-value': {
      fontSize: '$text-3xl',
      fontWeight: '$font-bold',
      lineHeight: 1
    },
    '.stat-label': {
      fontSize: '$text-sm',
      color: '$gray-600'
    },
    '.stat-change': {
      fontSize: '$text-sm',
      display: 'flex',
      alignItems: 'center',
      gap: '$space-1'
    }
  }
};
```

### 3.3 Form Components

#### Input Fields
```scss
.input {
  width: 100%;
  padding: $space-3 $space-4;
  font-size: $text-base;
  line-height: $leading-normal;
  border: 1px solid $gray-300;
  border-radius: 8px;
  background: white;
  transition: all 200ms ease;
  
  &::placeholder {
    color: $gray-500;
  }
  
  &:hover:not(:disabled) {
    border-color: $gray-400;
  }
  
  &:focus {
    outline: none;
    border-color: $primary-500;
    box-shadow: 0 0 0 3px rgba($primary-500, 0.1);
  }
  
  &.error {
    border-color: $danger-500;
    
    &:focus {
      box-shadow: 0 0 0 3px rgba($danger-500, 0.1);
    }
  }
  
  &:disabled {
    background: $gray-100;
    cursor: not-allowed;
    opacity: 0.6;
  }
}

// Input with Icon
.input-group {
  position: relative;
  
  .input-icon {
    position: absolute;
    left: $space-4;
    top: 50%;
    transform: translateY(-50%);
    color: $gray-500;
    pointer-events: none;
  }
  
  .input {
    padding-left: $space-10;
  }
}
```

#### Button Components
```scss
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: $space-3 $space-6;
  font-size: $text-base;
  font-weight: $font-medium;
  line-height: $leading-normal;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 200ms ease;
  gap: $space-2;
  
  &:focus-visible {
    outline: 2px solid $primary-500;
    outline-offset: 2px;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  // Variants
  &.primary {
    background: $primary-500;
    color: white;
    
    &:hover:not(:disabled) {
      background: $primary-600;
    }
    
    &:active {
      background: $primary-700;
    }
  }
  
  &.secondary {
    background: white;
    color: $gray-700;
    border: 1px solid $gray-300;
    
    &:hover:not(:disabled) {
      background: $gray-50;
      border-color: $gray-400;
    }
  }
  
  &.danger {
    background: $danger-500;
    color: white;
    
    &:hover:not(:disabled) {
      background: darken($danger-500, 10%);
    }
  }
  
  // Sizes
  &.sm {
    padding: $space-2 $space-4;
    font-size: $text-sm;
  }
  
  &.lg {
    padding: $space-4 $space-8;
    font-size: $text-lg;
  }
  
  // Loading State
  &.loading {
    color: transparent;
    position: relative;
    
    &::after {
      content: '';
      position: absolute;
      width: 16px;
      height: 16px;
      border: 2px solid white;
      border-right-color: transparent;
      border-radius: 50%;
      animation: spin 0.75s linear infinite;
    }
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

### 3.4 Data Display Components

#### Tables
```scss
.table {
  width: 100%;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: $shadow-sm;
  
  thead {
    background: $gray-50;
    border-bottom: 1px solid $gray-200;
    
    th {
      padding: $space-3 $space-4;
      text-align: left;
      font-size: $text-sm;
      font-weight: $font-semibold;
      color: $gray-700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
  }
  
  tbody {
    tr {
      border-bottom: 1px solid $gray-100;
      transition: background 200ms ease;
      
      &:hover {
        background: $gray-50;
      }
      
      &:last-child {
        border-bottom: none;
      }
    }
    
    td {
      padding: $space-4;
      font-size: $text-base;
      color: $gray-900;
    }
  }
  
  // Responsive
  @media (max-width: 768px) {
    &.responsive {
      thead {
        display: none;
      }
      
      tbody {
        tr {
          display: block;
          margin-bottom: $space-4;
          border: 1px solid $gray-200;
          border-radius: 8px;
          padding: $space-4;
        }
        
        td {
          display: flex;
          justify-content: space-between;
          padding: $space-2 0;
          
          &::before {
            content: attr(data-label);
            font-weight: $font-semibold;
            color: $gray-600;
          }
        }
      }
    }
  }
}
```

### 3.5 Feedback Components

#### Alert Messages
```scss
.alert {
  display: flex;
  align-items: flex-start;
  padding: $space-4;
  border-radius: 8px;
  gap: $space-3;
  
  &-icon {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
  }
  
  &-content {
    flex: 1;
    
    .alert-title {
      font-weight: $font-semibold;
      margin-bottom: $space-1;
    }
    
    .alert-description {
      font-size: $text-sm;
      line-height: $leading-relaxed;
    }
  }
  
  // Variants
  &.info {
    background: rgba($info-500, 0.1);
    color: darken($info-500, 25%);
    
    .alert-icon {
      color: $info-500;
    }
  }
  
  &.success {
    background: rgba($success-500, 0.1);
    color: darken($success-500, 25%);
    
    .alert-icon {
      color: $success-500;
    }
  }
  
  &.warning {
    background: rgba($warning-500, 0.1);
    color: darken($warning-500, 25%);
    
    .alert-icon {
      color: $warning-500;
    }
  }
  
  &.danger {
    background: rgba($danger-500, 0.1);
    color: darken($danger-500, 25%);
    
    .alert-icon {
      color: $danger-500;
    }
  }
}
```

#### Progress Indicators
```scss
.progress {
  &-bar {
    width: 100%;
    height: 8px;
    background: $gray-200;
    border-radius: 999px;
    overflow: hidden;
    
    &-fill {
      height: 100%;
      background: $primary-500;
      border-radius: 999px;
      transition: width 300ms ease;
    }
  }
  
  &-circle {
    position: relative;
    display: inline-flex;
    
    svg {
      transform: rotate(-90deg);
    }
    
    .progress-circle-bg {
      stroke: $gray-200;
    }
    
    .progress-circle-fill {
      stroke: $primary-500;
      stroke-linecap: round;
      transition: stroke-dashoffset 300ms ease;
    }
    
    .progress-circle-text {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: $text-2xl;
      font-weight: $font-bold;
    }
  }
  
  &-steps {
    display: flex;
    justify-content: space-between;
    
    .progress-step {
      flex: 1;
      text-align: center;
      position: relative;
      
      &::before {
        content: '';
        position: absolute;
        top: 20px;
        left: -50%;
        right: 50%;
        height: 2px;
        background: $gray-300;
      }
      
      &:first-child::before {
        display: none;
      }
      
      &.completed {
        .progress-step-circle {
          background: $success-500;
          color: white;
        }
        
        &::before {
          background: $success-500;
        }
      }
      
      &.active {
        .progress-step-circle {
          background: $primary-500;
          color: white;
          box-shadow: 0 0 0 4px rgba($primary-500, 0.2);
        }
      }
    }
    
    &-circle {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: white;
      border: 2px solid $gray-300;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-weight: $font-semibold;
      margin-bottom: $space-2;
    }
    
    &-label {
      font-size: $text-sm;
      color: $gray-600;
    }
  }
}
```

## 4. Page Layouts

### 4.1 Dashboard Layout

```tsx
// Dashboard Grid System
const dashboardLayout = {
  container: {
    display: 'grid',
    gridTemplateColumns: 'repeat(12, 1fr)',
    gap: '$space-6',
    padding: '$space-6'
  },
  
  // Component Placement
  statsRow: {
    gridColumn: 'span 12',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: '$space-4'
  },
  
  mainChart: {
    gridColumn: 'span 8',
    minHeight: '400px'
  },
  
  sidePanel: {
    gridColumn: 'span 4',
    display: 'flex',
    flexDirection: 'column',
    gap: '$space-4'
  },
  
  // Responsive
  '@media (max-width: 1024px)': {
    mainChart: {
      gridColumn: 'span 12'
    },
    sidePanel: {
      gridColumn: 'span 12'
    }
  }
};
```

### 4.2 Course Layout

```scss
.course-layout {
  display: flex;
  height: calc(100vh - 64px); // Minus header height
  
  // Video/Content Area
  .course-main {
    flex: 1;
    background: black;
    position: relative;
    
    .video-container {
      position: relative;
      padding-bottom: 56.25%; // 16:9 aspect ratio
      height: 0;
      
      iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
      }
    }
    
    .course-controls {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(transparent, rgba(0,0,0,0.8));
      padding: $space-6;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
  
  // Sidebar
  .course-sidebar {
    width: 400px;
    background: white;
    border-left: 1px solid $gray-200;
    display: flex;
    flex-direction: column;
    
    .course-tabs {
      display: flex;
      border-bottom: 1px solid $gray-200;
      
      .tab {
        flex: 1;
        padding: $space-4;
        text-align: center;
        cursor: pointer;
        border-bottom: 2px solid transparent;
        transition: all 200ms ease;
        
        &:hover {
          background: $gray-50;
        }
        
        &.active {
          border-bottom-color: $primary-500;
          color: $primary-500;
          font-weight: $font-semibold;
        }
      }
    }
    
    .course-content {
      flex: 1;
      overflow-y: auto;
      padding: $space-6;
    }
  }
  
  // Mobile Layout
  @media (max-width: 768px) {
    flex-direction: column;
    
    .course-main {
      height: 40vh;
    }
    
    .course-sidebar {
      width: 100%;
      height: 60vh;
    }
  }
}
```

## 5. Interaction Design

### 5.1 Micro-interactions

```scss
// Hover Effects
.hover-lift {
  transition: transform 200ms ease;
  
  &:hover {
    transform: translateY(-2px);
  }
}

.hover-scale {
  transition: transform 200ms ease;
  
  &:hover {
    transform: scale(1.02);
  }
}

// Click Feedback
.clickable {
  position: relative;
  overflow: hidden;
  
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.1);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
  }
  
  &:active::after {
    width: 300px;
    height: 300px;
  }
}

// Loading States
.skeleton {
  position: relative;
  overflow: hidden;
  background: $gray-200;
  
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.4),
      transparent
    );
    animation: skeleton-wave 1.5s infinite;
  }
}

@keyframes skeleton-wave {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
```

### 5.2 Transitions

```scss
// Page Transitions
.page-enter {
  opacity: 0;
  transform: translateY(20px);
}

.page-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: all 300ms ease;
}

.page-exit {
  opacity: 1;
}

.page-exit-active {
  opacity: 0;
  transition: opacity 200ms ease;
}

// Modal Transitions
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  transition: opacity 200ms ease;
  
  &.entering {
    opacity: 0;
  }
  
  &.entered {
    opacity: 1;
  }
}

.modal-content {
  transform: scale(0.95) translateY(20px);
  opacity: 0;
  transition: all 200ms ease;
  
  &.entered {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}
```

## 6. Responsive Design

### 6.1 Breakpoints

```scss
// Breakpoint Variables
$breakpoint-sm: 640px;   // Mobile landscape
$breakpoint-md: 768px;   // Tablet
$breakpoint-lg: 1024px;  // Desktop
$breakpoint-xl: 1280px;  // Large desktop
$breakpoint-2xl: 1536px; // Extra large

// Mixins
@mixin sm {
  @media (min-width: $breakpoint-sm) { @content; }
}

@mixin md {
  @media (min-width: $breakpoint-md) { @content; }
}

@mixin lg {
  @media (min-width: $breakpoint-lg) { @content; }
}

@mixin xl {
  @media (min-width: $breakpoint-xl) { @content; }
}

@mixin mobile-only {
  @media (max-width: $breakpoint-md - 1px) { @content; }
}

@mixin tablet-only {
  @media (min-width: $breakpoint-md) and (max-width: $breakpoint-lg - 1px) { @content; }
}
```

### 6.2 Mobile-First Components

```scss
// Container
.container {
  width: 100%;
  padding: 0 $space-4;
  margin: 0 auto;
  
  @include sm {
    max-width: $breakpoint-sm;
  }
  
  @include md {
    max-width: $breakpoint-md;
    padding: 0 $space-6;
  }
  
  @include lg {
    max-width: $breakpoint-lg;
  }
  
  @include xl {
    max-width: $breakpoint-xl;
  }
}

// Grid System
.grid {
  display: grid;
  gap: $space-4;
  
  // Mobile: 1 column
  grid-template-columns: 1fr;
  
  @include sm {
    &.sm\:cols-2 {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  @include md {
    &.md\:cols-3 {
      grid-template-columns: repeat(3, 1fr);
    }
    
    &.md\:cols-4 {
      grid-template-columns: repeat(4, 1fr);
    }
  }
  
  @include lg {
    gap: $space-6;
    
    &.lg\:cols-4 {
      grid-template-columns: repeat(4, 1fr);
    }
  }
}
```

## 7. Accessibility Design

### 7.1 Focus Indicators

```scss
// Focus Styles
:focus-visible {
  outline: 2px solid $primary-500;
  outline-offset: 2px;
}

// Skip Links
.skip-link {
  position: absolute;
  left: -999px;
  width: 1px;
  height: 1px;
  overflow: hidden;
  
  &:focus {
    position: fixed;
    top: $space-4;
    left: $space-4;
    width: auto;
    height: auto;
    padding: $space-3 $space-4;
    background: $primary-500;
    color: white;
    border-radius: 4px;
    z-index: 9999;
  }
}

// Screen Reader Only
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

### 7.2 High Contrast Mode

```scss
@media (prefers-contrast: high) {
  .button {
    border: 2px solid currentColor;
  }
  
  .card {
    border: 2px solid currentColor;
  }
  
  .input {
    border-width: 2px;
  }
}

// Dark Mode Support
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: #{$gray-900};
    --color-surface: #{$gray-800};
    --color-text: #{$gray-100};
    --color-border: #{$gray-700};
  }
  
  body {
    background: var(--color-background);
    color: var(--color-text);
  }
  
  .card {
    background: var(--color-surface);
    border-color: var(--color-border);
  }
}
```

## 8. Motion Design

### 8.1 Animation Principles

```scss
// Timing Functions
$ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
$ease-out: cubic-bezier(0, 0, 0.2, 1);
$ease-in: cubic-bezier(0.4, 0, 1, 1);
$spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);

// Duration Scale
$duration-75: 75ms;
$duration-100: 100ms;
$duration-150: 150ms;
$duration-200: 200ms;
$duration-300: 300ms;
$duration-500: 500ms;
$duration-700: 700ms;
$duration-1000: 1000ms;

// Reduce Motion
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### 8.2 Animation Library

```scss
// Fade Animations
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// Scale Animations
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

// Slide Animations
@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

// Success Animation
@keyframes successBounce {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

// Usage Classes
.animate-fadeIn {
  animation: fadeIn $duration-300 $ease-out;
}

.animate-fadeInUp {
  animation: fadeInUp $duration-500 $ease-out;
}

.animate-scaleIn {
  animation: scaleIn $duration-300 $spring;
}
```

## 9. Gamification Elements

### 9.1 Achievement Badges

```scss
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, $primary-400, $primary-600);
  box-shadow: $shadow-lg;
  position: relative;
  
  &.gold {
    background: linear-gradient(135deg, #FFD700, #FFA500);
  }
  
  &.silver {
    background: linear-gradient(135deg, #C0C0C0, #808080);
  }
  
  &.bronze {
    background: linear-gradient(135deg, #CD7F32, #8B4513);
  }
  
  .badge-icon {
    width: 32px;
    height: 32px;
    color: white;
  }
  
  &.locked {
    background: $gray-300;
    
    &::after {
      content: '🔒';
      position: absolute;
      bottom: -4px;
      right: -4px;
      background: white;
      border-radius: 50%;
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: $shadow-sm;
    }
  }
  
  &.new {
    animation: badgePulse 2s ease-in-out infinite;
  }
}

@keyframes badgePulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
```

### 9.2 Progress Visualization

```scss
.level-indicator {
  display: flex;
  flex-direction: column;
  gap: $space-2;
  
  .level-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .level-number {
      font-size: $text-2xl;
      font-weight: $font-bold;
      color: $primary-600;
    }
    
    .level-points {
      font-size: $text-sm;
      color: $gray-600;
    }
  }
  
  .level-progress {
    height: 12px;
    background: $gray-200;
    border-radius: 999px;
    overflow: hidden;
    position: relative;
    
    .level-progress-fill {
      height: 100%;
      background: linear-gradient(90deg, $primary-400, $primary-600);
      border-radius: 999px;
      transition: width 1s $ease-out;
      
      &::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        width: 100px;
        background: linear-gradient(
          90deg,
          transparent,
          rgba(255, 255, 255, 0.4),
          transparent
        );
        animation: shimmer 2s infinite;
      }
    }
  }
}

@keyframes shimmer {
  0% { transform: translateX(-100px); }
  100% { transform: translateX(100px); }
}
```

## 10. Dark Mode Design

### 10.1 Color Scheme

```scss
// Dark Mode Palette
$dark-bg: #0A0A0B;
$dark-surface: #1A1A1B;
$dark-surface-2: #2A2A2B;
$dark-border: #3A3A3B;
$dark-text: #FAFAFA;
$dark-text-secondary: #A0A0A0;

// Dark Mode Variables
[data-theme="dark"] {
  // Backgrounds
  --color-bg: #{$dark-bg};
  --color-surface: #{$dark-surface};
  --color-surface-2: #{$dark-surface-2};
  
  // Text
  --color-text-primary: #{$dark-text};
  --color-text-secondary: #{$dark-text-secondary};
  
  // Borders
  --color-border: #{$dark-border};
  
  // Primary (adjusted for dark)
  --color-primary: #{$primary-400};
  --color-primary-hover: #{$primary-300};
  
  // Shadows (reduced opacity)
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
}
```

### 10.2 Component Adaptations

```scss
[data-theme="dark"] {
  .card {
    background: var(--color-surface);
    border-color: var(--color-border);
  }
  
  .input {
    background: var(--color-surface-2);
    border-color: var(--color-border);
    color: var(--color-text-primary);
    
    &::placeholder {
      color: var(--color-text-secondary);
    }
    
    &:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba($primary-400, 0.2);
    }
  }
  
  .button.secondary {
    background: var(--color-surface-2);
    border-color: var(--color-border);
    color: var(--color-text-primary);
    
    &:hover {
      background: var(--color-border);
    }
  }
  
  // Code blocks
  pre, code {
    background: var(--color-surface-2);
    border-color: var(--color-border);
  }
  
  // Charts
  .chart {
    --chart-grid-color: #{$dark-border};
    --chart-text-color: #{$dark-text-secondary};
  }
}
```

Diese umfassende UX & Design Spezifikation stellt sicher, dass die Cybersecurity Awareness Platform eine konsistente, ansprechende und benutzerfreundliche Oberfläche bietet.