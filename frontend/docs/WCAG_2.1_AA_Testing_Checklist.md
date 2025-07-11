# WCAG 2.1 AA Compliance Testing Checklist

## Overview
This checklist covers the key areas for testing WCAG 2.1 Level AA compliance in the AwarenessSchulungen application.

## 1. Perceivable

### 1.1 Text Alternatives
- [ ] All images have appropriate alt text
- [ ] Decorative images use `alt=""` or are marked as `aria-hidden="true"`
- [ ] Icons that convey meaning have `aria-label` attributes
- [ ] Complex images have longer descriptions available

### 1.2 Time-based Media
- [ ] Videos have captions
- [ ] Audio content has transcripts
- [ ] Pre-recorded videos have audio descriptions

### 1.3 Adaptable
- [ ] Content can be presented without losing information when:
  - [ ] CSS is disabled
  - [ ] Page is zoomed to 200%
  - [ ] Viewed in portrait or landscape orientation
- [ ] Proper heading hierarchy (h1, h2, h3, etc.)
- [ ] Lists use proper list markup (`<ul>`, `<ol>`, `<li>`)
- [ ] Tables have proper headers and captions

### 1.4 Distinguishable
- [ ] Color contrast ratio of at least 4.5:1 for normal text
- [ ] Color contrast ratio of at least 3:1 for large text
- [ ] Information is not conveyed by color alone
- [ ] Text can be resized up to 200% without assistive technology
- [ ] No text in images (except logos)

## 2. Operable

### 2.1 Keyboard Accessible
- [ ] All interactive elements are keyboard accessible
- [ ] No keyboard traps
- [ ] Focus order is logical
- [ ] Skip links are provided for repetitive content
- [ ] Keyboard shortcuts don't conflict with assistive technology

### 2.2 Enough Time
- [ ] Users can extend time limits
- [ ] Auto-updating content can be paused, stopped, or hidden
- [ ] No content flashes more than 3 times per second

### 2.3 Seizures and Physical Reactions
- [ ] No content that flashes more than 3 times per second
- [ ] Animation can be paused or disabled

### 2.4 Navigable
- [ ] Page has a descriptive title
- [ ] Links have descriptive text (not "click here")
- [ ] Multiple ways to navigate (menu, search, sitemap)
- [ ] Current location is indicated in navigation
- [ ] Focus is visible for all interactive elements
- [ ] Headings and labels are descriptive

### 2.5 Input Modalities
- [ ] Touch targets are at least 44x44 CSS pixels
- [ ] Functionality is available through single pointer actions
- [ ] Motion-based actions have alternatives

## 3. Understandable

### 3.1 Readable
- [ ] Page language is identified (`lang` attribute)
- [ ] Language changes within content are identified
- [ ] Unusual words are explained
- [ ] Abbreviations are expanded on first use

### 3.2 Predictable
- [ ] Navigation is consistent across pages
- [ ] Components behave consistently
- [ ] Changes of context don't happen automatically
- [ ] Error identification is clear

### 3.3 Input Assistance
- [ ] Form labels are descriptive and associated with inputs
- [ ] Required fields are clearly marked
- [ ] Error messages are specific and helpful
- [ ] Error prevention for legal/financial actions
- [ ] Form instructions are clear

## 4. Robust

### 4.1 Compatible
- [ ] Valid HTML markup
- [ ] ARIA attributes are used correctly
- [ ] Status messages use appropriate ARIA live regions
- [ ] Works with common assistive technologies

## Testing Tools

### Automated Testing
1. **axe DevTools** - Browser extension for accessibility testing
2. **WAVE** - Web Accessibility Evaluation Tool
3. **Lighthouse** - Built into Chrome DevTools
4. **Pa11y** - Command line accessibility testing

### Manual Testing
1. **Keyboard Navigation**
   - Tab through all interactive elements
   - Use Enter/Space to activate buttons
   - Use arrow keys in menus and lists
   - Test Escape key to close modals

2. **Screen Reader Testing**
   - NVDA (Windows)
   - JAWS (Windows)
   - VoiceOver (macOS/iOS)
   - TalkBack (Android)

3. **Visual Testing**
   - Zoom to 200% and check layout
   - Test with Windows High Contrast mode
   - Use color contrast analyzers
   - Test with CSS disabled

## ARIA Implementation Guidelines

### Buttons
- Use `aria-label` for icon-only buttons
- Use `aria-pressed` for toggle buttons
- Use `aria-expanded` for buttons that control collapsible content
- Add `aria-busy="true"` during loading states

### Forms
- Use `aria-required="true"` for required fields
- Use `aria-invalid="true"` for fields with errors
- Use `aria-describedby` to associate error messages with inputs
- Use `aria-live="polite"` for error messages

### Navigation
- Use `role="navigation"` with `aria-label` for nav sections
- Use `aria-current="page"` for current page in navigation
- Use `aria-expanded` for expandable menu items

### Modals/Dialogs
- Use `role="dialog"` with `aria-modal="true"`
- Use `aria-labelledby` to reference the dialog title
- Trap focus within the modal
- Return focus to trigger element when closed

### Tables
- Use `scope="col"` for column headers
- Use `scope="row"` for row headers
- Use `caption` element for table descriptions
- Use `aria-label` for tables without visible captions

### Live Regions
- Use `aria-live="polite"` for non-critical updates
- Use `aria-live="assertive"` for important announcements
- Use `role="alert"` for error messages
- Use `aria-atomic="true"` to read entire region

## Component-Specific Testing

### LoginForm Component
- [x] Email input has proper label and error handling
- [x] Password input has proper label and error handling
- [x] Form has aria-label
- [x] Error messages have role="alert" and aria-live
- [x] Submit button has aria-busy during loading
- [x] Icons are marked with aria-hidden

### Button Component
- [x] Supports aria-label for icon buttons
- [x] Supports aria-pressed for toggle states
- [x] Supports aria-expanded for expandable content
- [x] Loading state includes aria-busy
- [x] Loading spinner has sr-only text

### Navbar Component
- [x] Has role="navigation" with aria-label
- [x] Menu toggle button has aria-label and aria-expanded
- [x] Notification button has aria-label
- [x] Icons are marked with aria-hidden
- [x] Separator has role="separator"

### Table Component
- [x] Table headers have scope="col"
- [x] Container has role="region" with aria-label

### Modal/Dialog Components
- [x] Dialog has role="dialog" and aria-modal
- [x] Close button has aria-label
- [x] Title is referenced by aria-labelledby

### LoadingSpinner Component
- [x] Has role="status" with aria-live
- [x] Includes sr-only "Loading..." text
- [x] Spinner graphic has aria-hidden

### ErrorMessage Component
- [x] Has role="alert" with aria-live="assertive"
- [x] Uses aria-atomic="true" for complete announcement
- [x] Icon is marked with aria-hidden

## Checklist for New Components

When creating new components, ensure:

1. **Interactive Elements**
   - [ ] Keyboard accessible
   - [ ] Visible focus indicators
   - [ ] Appropriate ARIA labels

2. **Forms**
   - [ ] Labels associated with inputs
   - [ ] Error messages linked with aria-describedby
   - [ ] Required fields marked appropriately

3. **Dynamic Content**
   - [ ] Live regions for updates
   - [ ] Loading states announced
   - [ ] Error states announced

4. **Visual Design**
   - [ ] Sufficient color contrast
   - [ ] Not relying on color alone
   - [ ] Responsive to zoom and text sizing

5. **Semantic HTML**
   - [ ] Proper heading hierarchy
   - [ ] Meaningful link text
   - [ ] Appropriate landmark roles

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Resources](https://webaim.org/resources/)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)