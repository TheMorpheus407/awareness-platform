import { test, expect } from '../fixtures/auth.fixture';
import { generateTestEmail } from '../utils/test-data';

test.describe('Authentication Flow', () => {
  test('should display login page with correct elements', async ({ page, loginPage }) => {
    await loginPage.goto();
    
    // Check all elements are visible
    await expect(page).toHaveTitle(/Cybersecurity Awareness Platform/);
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.submitButton).toBeVisible();
    await expect(loginPage.registerLink).toBeVisible();
    await expect(loginPage.languageSwitcher).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.submitButton.click();
    
    // Check for validation messages
    await expect(loginPage.page.getByText(/email.*required/i)).toBeVisible();
    await expect(loginPage.page.getByText(/password.*required/i)).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login('invalid@example.com', 'wrongpassword');
    
    await expect(loginPage.errorMessage).toBeVisible();
    await expect(loginPage.errorMessage).toContainText(/incorrect email or password/i);
  });

  test('should successfully login with valid credentials', async ({ page, loginPage, dashboardPage }) => {
    await loginPage.goto();
    await loginPage.login('admin@example.com', 'AdminPassword123!');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(dashboardPage.welcomeMessage).toBeVisible();
  });

  test('should logout successfully', async ({ page, authenticatedPage, dashboardPage }) => {
    await dashboardPage.goto();
    await dashboardPage.logout();
    
    // Should redirect to login
    await expect(page).toHaveURL('/login');
  });

  test('should register new user', async ({ page, loginPage }) => {
    await page.goto('/register');
    
    const testEmail = generateTestEmail();
    
    // Fill registration form
    await page.getByLabel(/email/i).fill(testEmail);
    await page.getByLabel(/^password$/i).fill('TestPassword123!');
    await page.getByLabel(/confirm password/i).fill('TestPassword123!');
    await page.getByLabel(/first name/i).fill('Test');
    await page.getByLabel(/last name/i).fill('User');
    await page.getByLabel(/phone/i).fill('+1234567890');
    
    await page.getByRole('button', { name: /register|registrieren/i }).click();
    
    // Should show success message or redirect
    await expect(page.getByText(/registration successful|check your email/i)).toBeVisible();
  });

  test('should protect routes from unauthenticated access', async ({ page }) => {
    // Try to access protected routes
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login');
    
    await page.goto('/users');
    await expect(page).toHaveURL('/login');
    
    await page.goto('/companies');
    await expect(page).toHaveURL('/login');
  });

  test('should handle token expiration gracefully', async ({ page, context }) => {
    // Set an expired token
    await context.addCookies([
      {
        name: 'access_token',
        value: 'expired_token',
        domain: 'localhost',
        path: '/',
      },
    ]);
    
    await page.goto('/dashboard');
    
    // Should redirect to login
    await expect(page).toHaveURL('/login');
  });
});