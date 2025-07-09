import { test as base, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';

type AuthFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  authenticatedPage: void;
};

export const test = base.extend<AuthFixtures>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },

  dashboardPage: async ({ page }, use) => {
    const dashboardPage = new DashboardPage(page);
    await use(dashboardPage);
  },

  authenticatedPage: async ({ page, context }, use) => {
    // Login via API to speed up tests
    const response = await page.request.post('http://localhost:8000/api/v1/auth/login', {
      form: {
        username: 'test@example.com',
        password: 'TestPassword123!',
      },
    });

    expect(response.ok()).toBeTruthy();
    const { access_token } = await response.json();

    // Save auth state
    await context.addCookies([
      {
        name: 'access_token',
        value: access_token,
        domain: 'localhost',
        path: '/',
      },
    ]);

    // Store token in localStorage as well (if your app uses it)
    await page.addInitScript((token) => {
      localStorage.setItem('access_token', token);
    }, access_token);

    await use();
  },
});

export { expect };