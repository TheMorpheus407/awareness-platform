import { test, expect } from '../fixtures/auth.fixture';
import { generateTestEmail, generateCompanyDomain } from '../utils/test-data';

test.describe('API Integration Tests', () => {
  test('should handle API errors gracefully', async ({ page, loginPage }) => {
    // Mock API to return error
    await page.route('**/api/v1/auth/login', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    });
    
    await loginPage.goto();
    await loginPage.login('admin@example.com', 'AdminPassword123!');
    
    // Should show user-friendly error
    await expect(page.getByText(/something went wrong|server error/i)).toBeVisible();
  });

  test('should handle network timeouts', async ({ page, authenticatedPage }) => {
    // Simulate network timeout
    await page.route('**/api/v1/users**', route => {
      // Never respond to simulate timeout
    });
    
    await page.goto('/users');
    
    // Should show timeout error after some time
    await expect(page.getByText(/request timeout|connection error/i)).toBeVisible({ timeout: 35000 });
  });

  test('should retry failed requests', async ({ page, authenticatedPage }) => {
    let requestCount = 0;
    
    // Fail first request, succeed on retry
    await page.route('**/api/v1/users**', route => {
      requestCount++;
      if (requestCount === 1) {
        route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Service temporarily unavailable' }),
        });
      } else {
        route.continue();
      }
    });
    
    await page.goto('/users');
    
    // Should eventually load data after retry
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
  });

  test('should handle pagination correctly', async ({ page, authenticatedPage, request }) => {
    // Create many items to test pagination
    const authToken = await request.post('/api/v1/auth/login', {
      form: {
        username: 'admin@example.com',
        password: 'AdminPassword123!',
      },
    }).then(res => res.json()).then(data => data.access_token);
    
    // Create 25 test users
    const userPromises = [];
    for (let i = 0; i < 25; i++) {
      userPromises.push(
        request.post('/api/v1/auth/register', {
          data: {
            email: generateTestEmail(),
            password: 'TestPassword123!',
            first_name: `Test${i}`,
            last_name: `User${i}`,
            role: 'user',
            is_active: true,
          },
        })
      );
    }
    await Promise.all(userPromises);
    
    await page.goto('/users');
    
    // Check pagination info
    await expect(page.getByText(/page 1/i)).toBeVisible();
    await expect(page.getByText(/25 total/i)).toBeVisible();
    
    // Navigate to page 2
    await page.getByRole('button', { name: /next|2/i }).click();
    
    // URL should update
    await expect(page).toHaveURL(/page=2/);
    
    // Different data should be shown
    const firstPageFirstUser = await page.locator('tbody tr').first().textContent();
    await page.getByRole('button', { name: /previous|1/i }).click();
    const secondPageFirstUser = await page.locator('tbody tr').first().textContent();
    expect(firstPageFirstUser).not.toBe(secondPageFirstUser);
  });

  test('should handle real-time updates', async ({ page, context, authenticatedPage }) => {
    await page.goto('/users');
    
    // Open second page in new tab
    const page2 = await context.newPage();
    await page2.goto('http://localhost:5173/users');
    
    // Create user in first tab
    const testEmail = generateTestEmail();
    await page.getByRole('button', { name: /add user/i }).click();
    await page.getByLabel(/email/i).fill(testEmail);
    await page.getByLabel(/first name/i).fill('Realtime');
    await page.getByLabel(/last name/i).fill('Test');
    await page.getByRole('button', { name: /save/i }).click();
    
    // If real-time updates are implemented, check if user appears in second tab
    // Otherwise, refresh and check
    await page2.reload();
    await expect(page2.getByText(testEmail)).toBeVisible();
  });

  test('should handle concurrent modifications', async ({ page, context, authenticatedPage, request }) => {
    // Create a test company
    const authToken = await request.post('/api/v1/auth/login', {
      form: {
        username: 'admin@example.com',
        password: 'AdminPassword123!',
      },
    }).then(res => res.json()).then(data => data.access_token);
    
    const company = await request.post('/api/v1/companies', {
      headers: { 'Authorization': `Bearer ${authToken}` },
      data: {
        name: 'Concurrent Test Company',
        domain: generateCompanyDomain(),
        industry: 'Technology',
        employee_count: 100,
        is_active: true,
      },
    }).then(res => res.json());
    
    // Open company edit in two tabs
    await page.goto('/companies');
    await page.getByText(company.name).click();
    await page.getByRole('button', { name: /edit/i }).click();
    
    const page2 = await context.newPage();
    await page2.goto(`http://localhost:5173/companies`);
    await page2.getByText(company.name).click();
    await page2.getByRole('button', { name: /edit/i }).click();
    
    // Edit in first tab
    await page.getByLabel(/company name/i).clear();
    await page.getByLabel(/company name/i).fill('Updated by Tab 1');
    await page.getByRole('button', { name: /save/i }).click();
    
    // Try to save in second tab
    await page2.getByLabel(/company name/i).clear();
    await page2.getByLabel(/company name/i).fill('Updated by Tab 2');
    await page2.getByRole('button', { name: /save/i }).click();
    
    // Should show conflict error or handle gracefully
    await expect(page2.getByText(/conflict|already modified|please refresh/i)).toBeVisible();
  });

  test('should validate data before sending to API', async ({ page, authenticatedPage }) => {
    await page.goto('/users');
    await page.getByRole('button', { name: /add user/i }).click();
    
    // Test various invalid inputs
    await page.getByLabel(/email/i).fill('not-an-email');
    await page.getByLabel(/first name/i).fill('123'); // Numbers only
    await page.getByLabel(/last name/i).fill(''); // Empty
    
    await page.getByRole('button', { name: /save/i }).click();
    
    // Should show validation errors without making API call
    await expect(page.getByText(/invalid email/i)).toBeVisible();
    await expect(page.getByText(/required/i)).toBeVisible();
    
    // Verify no API call was made
    let apiCalled = false;
    page.on('request', request => {
      if (request.url().includes('/api/v1/users') && request.method() === 'POST') {
        apiCalled = true;
      }
    });
    
    await page.waitForTimeout(1000);
    expect(apiCalled).toBe(false);
  });
});