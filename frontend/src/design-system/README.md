# Premium Design System

A comprehensive design system with advanced animations, micro-interactions, and accessibility-first components for the Awareness Training Platform.

## 🎨 Design Principles

### 1. **Motion with Purpose**
- Every animation serves a functional purpose
- Smooth, natural transitions that guide user attention
- Consistent timing and easing functions across components

### 2. **Accessibility First**
- WCAG 2.1 AA compliant components
- Full keyboard navigation support
- Screen reader friendly
- Focus indicators and ARIA labels

### 3. **Dark Mode Support**
- Seamless theme switching
- Optimized color contrasts for both modes
- Persistent user preference

### 4. **Performance Optimized**
- Hardware-accelerated animations
- Efficient re-renders with Framer Motion
- Lazy loading and code splitting ready

## 🚀 Getting Started

### Installation

```typescript
// In your main App.tsx or index.tsx
import { initializeThemeSystem } from './design-system';

// Initialize the design system
initializeThemeSystem();
```

### Import Global Styles

```css
/* In your main CSS file */
@import './design-system/styles/global.css';
```

## 📦 Components

### Button

Premium button component with ripple effects, multiple variants, and loading states.

```tsx
import { Button } from './design-system';

// Basic usage
<Button variant="primary" size="md">
  Click me
</Button>

// With icon and ripple effect
<Button 
  variant="secondary" 
  icon={<IconPlus />}
  ripple
  glow
>
  Add Item
</Button>

// Loading state
<Button loading>
  Processing...
</Button>
```

#### Props
- `variant`: 'primary' | 'secondary' | 'tertiary' | 'ghost' | 'danger' | 'success'
- `size`: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
- `loading`: boolean
- `disabled`: boolean
- `fullWidth`: boolean
- `icon`: ReactNode
- `iconPosition`: 'left' | 'right'
- `ripple`: boolean (default: true)
- `glow`: boolean
- `pulse`: boolean

### Card

Elegant card component with hover effects and multiple variants.

```tsx
import { Card, CardHeader, CardBody, CardFooter, CardMedia } from './design-system';

<Card variant="elevated" hover glow>
  <CardMedia src="/image.jpg" height={200} />
  <CardHeader 
    title="Card Title" 
    subtitle="Card subtitle"
    action={<Button size="sm" variant="ghost">Action</Button>}
  />
  <CardBody>
    <p>Card content goes here...</p>
  </CardBody>
  <CardFooter>
    <Button variant="primary">Learn More</Button>
  </CardFooter>
</Card>
```

#### Props
- `variant`: 'default' | 'elevated' | 'outlined' | 'filled' | 'interactive'
- `padding`: 'none' | 'sm' | 'md' | 'lg'
- `hover`: boolean
- `glow`: boolean
- `loading`: boolean

### Input

Advanced input component with floating labels and validation states.

```tsx
import { Input } from './design-system';

// Floating label input
<Input
  label="Email"
  type="email"
  placeholder="Enter your email"
  floatingLabel
  icon={<IconMail />}
/>

// With validation
<Input
  label="Password"
  type="password"
  error="Password must be at least 8 characters"
  clearable
/>

// Different variants
<Input
  variant="filled"
  label="Name"
  helper="Enter your full name"
/>
```

#### Props
- `variant`: 'outlined' | 'filled' | 'flushed'
- `size`: 'sm' | 'md' | 'lg'
- `label`: string
- `error`: string
- `success`: string
- `helper`: string
- `icon`: ReactNode
- `iconPosition`: 'left' | 'right'
- `loading`: boolean
- `clearable`: boolean
- `floatingLabel`: boolean (default: true)
- `animate`: boolean (default: true)

### Toast

Notification system with swipe-to-dismiss and auto-dismiss functionality.

```tsx
import { useToast, ToastContainer } from './design-system';

function App() {
  const { toasts, toast } = useToast();

  const showToast = () => {
    toast.success('Operation completed!', {
      description: 'Your changes have been saved.',
      duration: 5000,
      action: {
        label: 'Undo',
        onClick: () => console.log('Undo clicked')
      }
    });
  };

  return (
    <>
      <Button onClick={showToast}>Show Toast</Button>
      <ToastContainer toasts={toasts} position="bottom-right" />
    </>
  );
}
```

#### Toast Types
- `toast.info(title, options)`
- `toast.success(title, options)`
- `toast.warning(title, options)`
- `toast.error(title, options)`

### Modal

Smooth modal with focus trap and multiple sizes.

```tsx
import { Modal, ConfirmModal } from './design-system';

// Basic modal
<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Modal Title"
  description="Modal description"
  size="md"
  footer={
    <>
      <Button variant="ghost" onClick={() => setIsOpen(false)}>
        Cancel
      </Button>
      <Button variant="primary">
        Save Changes
      </Button>
    </>
  }
>
  <p>Modal content...</p>
</Modal>

// Confirm modal
<ConfirmModal
  isOpen={showConfirm}
  onClose={() => setShowConfirm(false)}
  title="Delete Item"
  message="Are you sure you want to delete this item?"
  confirmLabel="Delete"
  confirmVariant="danger"
  onConfirm={handleDelete}
/>
```

#### Props
- `size`: 'sm' | 'md' | 'lg' | 'xl' | 'full'
- `closeOnOverlayClick`: boolean (default: true)
- `closeOnEsc`: boolean (default: true)
- `showCloseButton`: boolean (default: true)

## 🎨 Design Tokens

### Colors
```typescript
import { colors } from './design-system/tokens';

// Access color tokens
colors.brand.primary[500]  // Main brand color
colors.semantic.success.DEFAULT  // Success color
colors.neutral[900]  // Text color
```

### Typography
```typescript
import { typography } from './design-system/tokens';

// Font families
typography.fontFamily.sans
typography.fontFamily.display

// Font sizes (fluid)
typography.fontSize.base  // 16-18px
typography.fontSize['2xl']  // 24-30px

// Text styles
typography.textStyles.h1
typography.textStyles['body-large']
```

### Spacing
```typescript
import { spacing } from './design-system/tokens';

// Spacing scale
spacing.scale[4]  // 16px
spacing.scale[8]  // 32px

// Component spacing
spacing.components.button.md
spacing.layout.container.padding
```

### Animation
```typescript
import { animation } from './design-system/tokens';

// Durations
animation.duration.fast  // 150ms
animation.duration.normal  // 250ms

// Easings
animation.easing.smooth  // cubic-bezier(0.4, 0, 0.2, 1)
animation.easing.spring  // cubic-bezier(0.175, 0.885, 0.32, 1.275)

// Transitions
animation.transition.button
animation.transition.modal
```

## 🌗 Theme System

### Toggle Theme
```typescript
import { applyTheme, getCurrentTheme } from './design-system';

// Get current theme
const currentTheme = getCurrentTheme(); // 'light' | 'dark'

// Apply theme
applyTheme('dark');
```

### CSS Variables
All design tokens are available as CSS custom properties:

```css
.my-component {
  color: var(--color-text-primary);
  background: var(--color-surface-primary);
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
  transition: var(--transition-all);
}
```

## 🎭 Animation Utilities

### CSS Animation Classes
```css
/* Entrance animations */
.ds-animate-fadeIn
.ds-animate-fadeInUp
.ds-animate-fadeInDown
.ds-animate-scaleIn

/* Continuous animations */
.ds-animate-spin
.ds-animate-pulse
.ds-animate-bounce

/* Stagger delays */
.ds-stagger-1  /* 50ms delay */
.ds-stagger-2  /* 100ms delay */
.ds-stagger-3  /* 150ms delay */
```

### Skeleton Loading
```css
.ds-skeleton {
  /* Applies shimmer animation */
  height: 20px;
  width: 100%;
}
```

## ♿ Accessibility

### Keyboard Navigation
- All interactive components support keyboard navigation
- Focus indicators follow WCAG guidelines
- Tab order is logical and predictable

### Screen Readers
- Proper ARIA labels and descriptions
- Live regions for dynamic content
- Semantic HTML structure

### Reduced Motion
- Respects `prefers-reduced-motion` setting
- Graceful degradation of animations
- Essential motion preserved

## 📱 Responsive Design

All components are fully responsive with:
- Mobile-first approach
- Fluid typography
- Adaptive layouts
- Touch-friendly interactions

## 🎯 Best Practices

1. **Use semantic variants**: Choose button/card variants based on their purpose
2. **Consistent spacing**: Use spacing tokens instead of arbitrary values
3. **Meaningful animations**: Every animation should have a purpose
4. **Test accessibility**: Always test with keyboard and screen readers
5. **Performance first**: Use `will-change` and hardware acceleration wisely

## 🚀 Performance Tips

1. **Lazy load components**: Use React.lazy() for code splitting
2. **Memoize expensive operations**: Use React.memo() and useMemo()
3. **Batch animations**: Group related animations together
4. **Use CSS transforms**: Prefer transform over position changes
5. **Optimize bundle size**: Tree-shake unused components

## 🔧 Customization

### Extending Components
```tsx
import { Button } from './design-system';
import styled from 'styled-components';

const CustomButton = styled(Button)`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
  }
`;
```

### Custom Tokens
```typescript
// Add custom tokens
const customTokens = {
  '--custom-color': '#ff6b6b',
  '--custom-spacing': '24px',
};

// Apply to root
Object.entries(customTokens).forEach(([key, value]) => {
  document.documentElement.style.setProperty(key, value);
});
```

## 📚 Resources

- [Framer Motion Documentation](https://www.framer.com/motion/)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Material Design Motion](https://material.io/design/motion/)
- [Tailwind CSS](https://tailwindcss.com/)

---

Built with ❤️ for premium user experiences.