import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Tests', () => {
  test('login page should have no accessibility violations', async ({ page }) => {
    await page.goto('/login');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('register page should have no accessibility violations', async ({ page }) => {
    await page.goto('/register');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('keyboard navigation should work on login page', async ({ page }) => {
    await page.goto('/login');
    
    // Tab through elements
    await page.keyboard.press('Tab'); // Should focus email
    const emailFocused = await page.getByPlaceholder(/you@example.com/i).evaluate(el => el === document.activeElement);
    expect(emailFocused).toBeTruthy();
    
    await page.keyboard.press('Tab'); // Should focus password
    const passwordFocused = await page.getByPlaceholder(/••••••••/).evaluate(el => el === document.activeElement);
    expect(passwordFocused).toBeTruthy();
    
    await page.keyboard.press('Tab'); // Should focus remember me checkbox
    await page.keyboard.press('Tab'); // Should focus forgot password link
    await page.keyboard.press('Tab'); // Should focus submit button
    
    const submitFocused = await page.getByRole('button', { name: /sign in/i }).evaluate(el => el === document.activeElement);
    expect(submitFocused).toBeTruthy();
  });

  test('form labels should be properly associated', async ({ page }) => {
    await page.goto('/login');
    
    // Check if inputs have proper labels or aria-labels
    const emailInput = page.getByPlaceholder(/you@example.com/i);
    const emailLabel = await emailInput.getAttribute('aria-label');
    const emailLabelledBy = await emailInput.getAttribute('aria-labelledby');
    expect(emailLabel || emailLabelledBy).toBeTruthy();
    
    const passwordInput = page.getByPlaceholder(/••••••••/);
    const passwordLabel = await passwordInput.getAttribute('aria-label');
    const passwordLabelledBy = await passwordInput.getAttribute('aria-labelledby');
    expect(passwordLabel || passwordLabelledBy).toBeTruthy();
  });

  test('images should have alt text', async ({ page }) => {
    await page.goto('/');
    
    const images = page.locator('img');
    const imageCount = await images.count();
    
    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
    }
  });

  test('headings should have proper hierarchy', async ({ page }) => {
    await page.goto('/login');
    
    // Check for h1
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThan(0);
    
    // Check heading order
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').allTextContents();
    expect(headings.length).toBeGreaterThan(0);
  });

  test('color contrast should meet WCAG standards', async ({ page }) => {
    await page.goto('/login');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .include(['color-contrast'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('focus indicators should be visible', async ({ page }) => {
    await page.goto('/login');
    
    // Focus on email input
    await page.getByPlaceholder(/you@example.com/i).focus();
    
    // Check if focus is visible (this is a basic check)
    const emailInput = page.getByPlaceholder(/you@example.com/i);
    const outlineStyle = await emailInput.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        outlineWidth: styles.outlineWidth,
        outlineStyle: styles.outlineStyle,
        boxShadow: styles.boxShadow
      };
    });
    
    // Should have some focus indicator
    const hasFocusIndicator = 
      (outlineStyle.outlineWidth !== '0px' && outlineStyle.outlineStyle !== 'none') ||
      outlineStyle.boxShadow !== 'none';
    
    expect(hasFocusIndicator).toBeTruthy();
  });
});