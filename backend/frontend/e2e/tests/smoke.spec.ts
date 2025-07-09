import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('frontend is accessible', async ({ page }) => {
    await page.goto('/');
    
    // Should redirect to login or show app
    await expect(page).toHaveURL(/(login|dashboard)/);
    
    // Page should load without errors
    const title = await page.title();
    expect(title).toContain('Cybersecurity Awareness Platform');
  });

  test('API health check', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('can reach login page', async ({ page }) => {
    await page.goto('/login');
    
    // Check essential elements
    await expect(page.getByRole('heading', { name: /sign in|anmelden/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in|anmelden/i })).toBeVisible();
  });

  test('static assets load correctly', async ({ page }) => {
    await page.goto('/login');
    
    // Check if CSS loaded (by checking if an element has expected styles)
    const button = page.getByRole('button', { name: /sign in|anmelden/i });
    const backgroundColor = await button.evaluate(el => 
      window.getComputedStyle(el).backgroundColor
    );
    expect(backgroundColor).not.toBe('rgba(0, 0, 0, 0)'); // Not transparent
    
    // Check if logo/images load
    const images = page.locator('img');
    const imageCount = await images.count();
    
    for (let i = 0; i < imageCount; i++) {
      const image = images.nth(i);
      const isVisible = await image.isVisible();
      if (isVisible) {
        const naturalWidth = await image.evaluate((img: HTMLImageElement) => img.naturalWidth);
        expect(naturalWidth).toBeGreaterThan(0);
      }
    }
  });

  test('handles 404 pages gracefully', async ({ page }) => {
    await page.goto('/non-existent-page-12345');
    
    // Should show 404 or redirect to login
    await expect(page).toHaveURL(/(404|login)/);
    
    // Should not show error boundary
    await expect(page.getByText(/something went wrong|error boundary/i)).not.toBeVisible();
  });
});