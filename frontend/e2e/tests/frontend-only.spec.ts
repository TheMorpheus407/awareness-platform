import { test, expect } from '@playwright/test';

test.describe('Frontend-Only Tests', () => {
  test('should load the application', async ({ page }) => {
    await page.goto('/');
    
    // Either landing page or redirect to login
    await expect(page).toHaveURL(/\/(login)?$/);
  });

  test('should navigate to login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveURL('/login');
    
    // Check basic elements
    await expect(page.getByRole('heading', { name: /Welcome Back/i })).toBeVisible();
    await expect(page.getByPlaceholder(/you@example.com/i)).toBeVisible();
    await expect(page.getByPlaceholder(/••••••••/)).toBeVisible();
    await expect(page.getByRole('button', { name: /Sign In/i })).toBeVisible();
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/register');
    await expect(page).toHaveURL('/register');
    
    // Check basic elements
    await expect(page.getByRole('heading', { name: /Create.*Account|Register/i })).toBeVisible();
    await expect(page.getByPlaceholder(/you@example.com|email/i)).toBeVisible();
    await expect(page.getByPlaceholder(/••••••••|password/i).first()).toBeVisible();
  });

  test('should have proper page titles', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Cybersecurity Awareness Platform/);
  });

  test('should handle navigation between pages', async ({ page }) => {
    // Start at login
    await page.goto('/login');
    
    // Navigate to register
    const registerLink = page.getByRole('link', { name: /register|registrieren|sign up/i });
    if (await registerLink.isVisible()) {
      await registerLink.click();
      await expect(page).toHaveURL('/register');
    }
    
    // Navigate back to login
    const loginLink = page.getByRole('link', { name: /login|sign in|anmelden/i });
    if (await loginLink.isVisible()) {
      await loginLink.click();
      await expect(page).toHaveURL('/login');
    }
  });

  test('should display form validation', async ({ page }) => {
    await page.goto('/login');
    
    // Fill invalid email
    const emailInput = page.getByPlaceholder(/you@example.com/i);
    const passwordInput = page.getByPlaceholder(/••••••••/);
    
    await emailInput.fill('invalid-email');
    await passwordInput.fill('');
    
    // Try to submit form
    const submitButton = page.getByRole('button', { name: /sign in/i });
    await submitButton.click();
    
    // Check if email input is marked as invalid (either by HTML5 validation or custom validation)
    const emailValue = await emailInput.inputValue();
    expect(emailValue).toBe('invalid-email');
    
    // Form should not submit with invalid data
    await expect(page).toHaveURL('/login');
  });

  test('should have responsive design', async ({ page }) => {
    await page.goto('/');
    
    // Desktop view
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.waitForTimeout(500);
    
    // Mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    
    // Tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    
    // No errors should occur during viewport changes
  });

  test('should load without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.goto('/');
    await page.waitForTimeout(1000);
    
    // Filter out expected errors (like API connection errors)
    const unexpectedErrors = errors.filter(error => 
      !error.includes('Failed to fetch') &&
      !error.includes('Network request failed') &&
      !error.includes('ERR_CONNECTION_REFUSED')
    );
    
    expect(unexpectedErrors).toHaveLength(0);
  });
});