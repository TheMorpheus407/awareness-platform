import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    // Check for login form elements
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show error on invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    await page.fill('input[type="email"]', 'invalid@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Check for error message
    await expect(page.locator('text=/Invalid credentials|Login failed/i')).toBeVisible({ timeout: 10000 });
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    // Listen for console messages
    page.on('console', msg => console.log('Browser log:', msg.text()));
    page.on('pageerror', err => console.log('Page error:', err.message));
    
    // Listen for network requests
    page.on('response', response => {
      if (response.url().includes('/auth/login')) {
        console.log('Login response:', response.status(), response.statusText());
      }
    });
    
    // Fill in valid test credentials
    await page.fill('input[type="email"]', 'user@example.com');
    await page.fill('input[type="password"]', 'UserPassword123!');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 10000 });
  });
});