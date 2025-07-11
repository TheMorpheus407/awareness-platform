import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('Homepage loads successfully', async ({ page }) => {
    await page.goto('/');
    
    // Check critical elements
    await expect(page).toHaveTitle(/Awareness Schulungen/);
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('h1')).toContainText(/Cyber Security Awareness/);
    
    // Check performance
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
      };
    });
    
    expect(performanceMetrics.domContentLoaded).toBeLessThan(3000);
    expect(performanceMetrics.loadComplete).toBeLessThan(5000);
  });

  test('API health check', async ({ request }) => {
    const response = await request.get('/api/v1/health');
    expect(response.ok()).toBeTruthy();
    
    const health = await response.json();
    expect(health.status).toBe('healthy');
    expect(health.database).toBe('healthy');
    expect(health.redis).toBe('healthy');
  });

  test('Login flow works', async ({ page }) => {
    await page.goto('/login');
    
    // Fill login form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');
    
    // Check redirect to dashboard
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('Registration flow accessible', async ({ page }) => {
    await page.goto('/register');
    
    // Check form elements
    await expect(page.locator('input[name="firstName"]')).toBeVisible();
    await expect(page.locator('input[name="lastName"]')).toBeVisible();
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeEnabled();
  });

  test('Course catalog loads', async ({ page }) => {
    await page.goto('/courses');
    
    // Wait for courses to load
    await page.waitForSelector('[data-testid="course-card"]', { timeout: 10000 });
    
    // Check at least one course is displayed
    const courseCards = page.locator('[data-testid="course-card"]');
    await expect(courseCards).toHaveCount(await courseCards.count());
    expect(await courseCards.count()).toBeGreaterThan(0);
  });

  test('Critical user journey - Browse to Enrollment', async ({ page }) => {
    // Start from homepage
    await page.goto('/');
    
    // Navigate to courses
    await page.click('text=Courses');
    await expect(page).toHaveURL(/courses/);
    
    // Select first course
    await page.click('[data-testid="course-card"]:first-child');
    
    // Check course details page
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('text=Enroll Now')).toBeVisible();
    
    // Click enroll (should redirect to login if not authenticated)
    await page.click('text=Enroll Now');
    
    // Verify navigation worked
    const url = page.url();
    expect(url).toMatch(/login|dashboard/);
  });

  test('Responsive design check', async ({ page }) => {
    // Desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await expect(page.locator('.desktop-nav')).toBeVisible();
    
    // Mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('.mobile-menu-button')).toBeVisible();
    
    // Tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    const navigation = await page.locator('nav').boundingBox();
    expect(navigation).toBeTruthy();
  });

  test('Error handling - 404 page', async ({ page }) => {
    await page.goto('/non-existent-page');
    
    await expect(page.locator('text=404')).toBeVisible();
    await expect(page.locator('text=Page not found')).toBeVisible();
    await expect(page.locator('text=Go to Homepage')).toBeVisible();
  });

  test('Security headers present', async ({ page }) => {
    const response = await page.goto('/');
    const headers = response?.headers() || {};
    
    expect(headers['x-content-type-options']).toBe('nosniff');
    expect(headers['x-frame-options']).toBe('DENY');
    expect(headers['x-xss-protection']).toBe('1; mode=block');
    expect(headers['strict-transport-security']).toContain('max-age=');
  });

  test('Accessibility - ARIA landmarks', async ({ page }) => {
    await page.goto('/');
    
    // Check for main ARIA landmarks
    await expect(page.locator('nav[role="navigation"]')).toBeVisible();
    await expect(page.locator('main[role="main"]')).toBeVisible();
    await expect(page.locator('footer[role="contentinfo"]')).toBeVisible();
    
    // Check for skip link
    await page.keyboard.press('Tab');
    const skipLink = page.locator('text=Skip to content');
    await expect(skipLink).toBeFocused();
  });
});