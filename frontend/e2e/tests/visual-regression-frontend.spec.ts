import { test, expect } from '@playwright/test';

test.describe('Visual Regression Tests - Frontend Only', () => {
  test('login page screenshot', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('login-page.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('register page screenshot', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('register-page.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('mobile view - login page', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('login-page-mobile.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('tablet view - login page', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('login-page-tablet.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('form focus states screenshot', async ({ page }) => {
    await page.goto('/login');
    
    // Focus on email input
    await page.getByPlaceholder(/you@example.com/i).focus();
    await expect(page).toHaveScreenshot('login-email-focused.png', {
      animations: 'disabled',
    });
    
    // Focus on password input
    await page.getByPlaceholder(/••••••••/).focus();
    await expect(page).toHaveScreenshot('login-password-focused.png', {
      animations: 'disabled',
    });
  });

  test('form filled states screenshot', async ({ page }) => {
    await page.goto('/login');
    
    // Fill the form
    await page.getByPlaceholder(/you@example.com/i).fill('test@example.com');
    await page.getByPlaceholder(/••••••••/).fill('password123');
    
    await expect(page).toHaveScreenshot('login-form-filled.png', {
      animations: 'disabled',
    });
  });

  test('hover states screenshot', async ({ page }) => {
    await page.goto('/login');
    
    // Hover over submit button
    await page.getByRole('button', { name: /sign in/i }).hover();
    await expect(page).toHaveScreenshot('login-button-hover.png', {
      animations: 'disabled',
    });
  });

  test('language switcher screenshot', async ({ page }) => {
    await page.goto('/login');
    
    const langSwitcher = page.getByRole('button', { name: /EN|DE/i });
    if (await langSwitcher.isVisible()) {
      // Click to switch language
      await langSwitcher.click();
      await page.waitForTimeout(500);
      
      await expect(page).toHaveScreenshot('login-page-german.png', {
        fullPage: true,
        animations: 'disabled',
      });
    }
  });

  test('error states screenshot', async ({ page }) => {
    await page.goto('/login');
    
    // Submit empty form to trigger validation
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForTimeout(500);
    
    await expect(page).toHaveScreenshot('login-validation-errors.png', {
      animations: 'disabled',
    });
  });
});