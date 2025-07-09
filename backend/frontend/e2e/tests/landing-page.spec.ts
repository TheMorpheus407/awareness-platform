import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display the landing page when not authenticated', async ({ page }) => {
    // Check if we're on the landing page or redirected to login
    await expect(page).toHaveURL(/\/(login)?$/);
    
    // If on landing page, check for hero section
    if (page.url() === 'http://localhost:5173/') {
      await expect(page.getByRole('heading', { level: 1 })).toContainText(/Cybersecurity Awareness/i);
      await expect(page.getByText(/Empower Your Team/i)).toBeVisible();
    }
  });

  test('should have navigation menu', async ({ page }) => {
    // Check navigation items
    await expect(page.getByRole('link', { name: /Features/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Pricing/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /About/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Contact/i })).toBeVisible();
  });

  test('should have login and register buttons', async ({ page }) => {
    await expect(page.getByRole('link', { name: /Login/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Get Started|Register/i })).toBeVisible();
  });

  test('should navigate to features section', async ({ page }) => {
    await page.getByRole('link', { name: /Features/i }).click();
    await expect(page).toHaveURL('/#features');
    
    // Check features section is visible
    await expect(page.getByText(/AI-Powered Training/i)).toBeVisible();
    await expect(page.getByText(/Phishing Simulation/i)).toBeVisible();
    await expect(page.getByText(/Real-time Monitoring/i)).toBeVisible();
  });

  test('should navigate to pricing section', async ({ page }) => {
    await page.getByRole('link', { name: /Pricing/i }).click();
    await expect(page).toHaveURL('/#pricing');
    
    // Check pricing cards
    await expect(page.getByText(/Basic/i)).toBeVisible();
    await expect(page.getByText(/Professional/i)).toBeVisible();
    await expect(page.getByText(/Enterprise/i)).toBeVisible();
  });

  test('should show testimonials', async ({ page }) => {
    // Scroll to testimonials
    await page.evaluate(() => {
      const element = document.querySelector('#testimonials');
      element?.scrollIntoView();
    });
    
    // Check testimonials section
    await expect(page.getByText(/What Our Customers Say/i)).toBeVisible();
    await expect(page.locator('.testimonial-card').first()).toBeVisible();
  });

  test('should have working CTA buttons', async ({ page }) => {
    // Hero CTA
    const heroCTA = page.getByRole('link', { name: /Get Started Free/i }).first();
    await expect(heroCTA).toBeVisible();
    await heroCTA.click();
    await expect(page).toHaveURL('/register');
    
    // Go back
    await page.goBack();
    
    // Pricing CTA
    await page.evaluate(() => {
      const element = document.querySelector('#pricing');
      element?.scrollIntoView();
    });
    const pricingCTA = page.getByRole('button', { name: /Choose Plan/i }).first();
    await expect(pricingCTA).toBeVisible();
  });

  test('should have footer with links', async ({ page }) => {
    // Scroll to footer
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    
    // Check footer sections
    await expect(page.getByText(/Product/i).first()).toBeVisible();
    await expect(page.getByText(/Company/i).first()).toBeVisible();
    await expect(page.getByText(/Resources/i).first()).toBeVisible();
    await expect(page.getByText(/Legal/i).first()).toBeVisible();
    
    // Check copyright
    await expect(page.getByText(/© 2024 Cybersecurity Awareness Platform/i)).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check mobile menu button
    const mobileMenuButton = page.getByRole('button', { name: /menu/i });
    await expect(mobileMenuButton).toBeVisible();
    
    // Click menu button
    await mobileMenuButton.click();
    
    // Check mobile menu items
    await expect(page.getByRole('link', { name: /Features/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Pricing/i })).toBeVisible();
  });

  test('should have proper SEO meta tags', async ({ page }) => {
    // Check title
    await expect(page).toHaveTitle(/Cybersecurity Awareness Platform/i);
    
    // Check meta description
    const metaDescription = await page.getAttribute('meta[name="description"]', 'content');
    expect(metaDescription).toBeTruthy();
    expect(metaDescription).toContain('cybersecurity');
  });

  test('should handle navigation from login page back to landing', async ({ page }) => {
    // Go to login
    await page.getByRole('link', { name: /Login/i }).click();
    await expect(page).toHaveURL('/login');
    
    // Click logo or home link to go back
    const logo = page.getByRole('link', { name: /Cybersecurity Awareness Platform|Home/i }).first();
    if (await logo.isVisible()) {
      await logo.click();
      await expect(page).toHaveURL('/');
    } else {
      // Use browser back
      await page.goBack();
      await expect(page).toHaveURL('/');
    }
  });
});