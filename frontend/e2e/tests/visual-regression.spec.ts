import { test, expect } from '../fixtures/auth.fixture';

test.describe('Visual Regression Tests', () => {
  test('login page screenshot', async ({ page, loginPage }) => {
    await loginPage.goto();
    await expect(page).toHaveScreenshot('login-page.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('login page - German language screenshot', async ({ page, loginPage }) => {
    await loginPage.goto();
    await loginPage.switchLanguage('de');
    await expect(page).toHaveScreenshot('login-page-german.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('dashboard screenshot', async ({ page, authenticatedPage, dashboardPage }) => {
    await dashboardPage.goto();
    // Wait for data to load
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('dashboard.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('users page screenshot', async ({ page, authenticatedPage }) => {
    await page.goto('/users');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('users-page.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('companies page screenshot', async ({ page, authenticatedPage }) => {
    await page.goto('/companies');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('companies-page.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('mobile view - login page', async ({ page, loginPage }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await loginPage.goto();
    await expect(page).toHaveScreenshot('login-page-mobile.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('mobile view - dashboard', async ({ page, authenticatedPage, dashboardPage }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await dashboardPage.goto();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('dashboard-mobile.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('dark mode screenshots', async ({ page, authenticatedPage }) => {
    // If dark mode is implemented, toggle it
    await page.goto('/dashboard');
    
    // Try to find and click dark mode toggle
    const darkModeToggle = page.getByRole('button', { name: /dark mode|theme/i });
    if (await darkModeToggle.isVisible()) {
      await darkModeToggle.click();
      await page.waitForTimeout(500); // Wait for theme transition
      
      await expect(page).toHaveScreenshot('dashboard-dark-mode.png', {
        fullPage: true,
        animations: 'disabled',
      });
    }
  });

  test('form validation states screenshot', async ({ page, loginPage }) => {
    await loginPage.goto();
    
    // Trigger validation errors
    await loginPage.submitButton.click();
    
    await expect(page).toHaveScreenshot('login-validation-errors.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('loading states screenshot', async ({ page, authenticatedPage }) => {
    // Intercept API calls to simulate loading
    await page.route('**/api/v1/users**', async route => {
      await page.waitForTimeout(2000); // Simulate slow response
      await route.continue();
    });
    
    await page.goto('/users');
    
    // Capture loading state
    await expect(page).toHaveScreenshot('users-loading-state.png', {
      animations: 'disabled',
    });
  });
});