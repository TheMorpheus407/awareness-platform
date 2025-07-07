import { test, expect } from '../fixtures/auth.fixture';
import { UsersPage } from '../pages/users.page';
import { TestDataManager, generateTestEmail } from '../utils/test-data';

test.describe('User Management', () => {
  let usersPage: UsersPage;
  let testDataManager: TestDataManager;
  let authToken: string;

  test.beforeEach(async ({ page, authenticatedPage, request }) => {
    usersPage = new UsersPage(page);
    testDataManager = new TestDataManager(request);
    
    // Get auth token for API calls
    authToken = await testDataManager.loginAsAdmin();
    
    await usersPage.goto();
  });

  test.afterEach(async () => {
    // Cleanup test data
    await testDataManager.cleanup(authToken);
  });

  test('should display users list', async ({ page }) => {
    await expect(usersPage.userTable).toBeVisible();
    await expect(usersPage.addUserButton).toBeVisible();
    await expect(usersPage.searchInput).toBeVisible();
    
    // Should have at least one user (admin)
    const userCount = await usersPage.getUserCount();
    expect(userCount).toBeGreaterThan(0);
  });

  test('should add new user', async ({ page }) => {
    const initialCount = await usersPage.getUserCount();
    const testEmail = generateTestEmail();
    
    await usersPage.addUser({
      email: testEmail,
      firstName: 'New',
      lastName: 'User',
      role: 'user',
    });
    
    // Wait for success message
    await expect(page.getByText(/user created successfully/i)).toBeVisible();
    
    // Check user count increased
    const newCount = await usersPage.getUserCount();
    expect(newCount).toBe(initialCount + 1);
    
    // Search for the new user
    await usersPage.searchUsers(testEmail);
    await expect(page.getByText(testEmail)).toBeVisible();
  });

  test('should edit existing user', async ({ page }) => {
    // First create a user
    const testUser = await testDataManager.createTestUser({
      email: generateTestEmail(),
      password: 'TestPassword123!',
      firstName: 'Original',
      lastName: 'Name',
    });
    
    await page.reload();
    await usersPage.searchUsers(testUser.email);
    
    // Edit the user
    await usersPage.editUser(0, {
      firstName: 'Updated',
      lastName: 'Username',
    });
    
    // Wait for success message
    await expect(page.getByText(/user updated successfully/i)).toBeVisible();
    
    // Verify changes
    await page.reload();
    await usersPage.searchUsers(testUser.email);
    const userData = await usersPage.getUserData(0);
    expect(userData.name).toContain('Updated Username');
  });

  test('should delete user', async ({ page }) => {
    // First create a user
    const testUser = await testDataManager.createTestUser({
      email: generateTestEmail(),
      password: 'TestPassword123!',
      firstName: 'Delete',
      lastName: 'Me',
    });
    
    await page.reload();
    await usersPage.searchUsers(testUser.email);
    const initialCount = await usersPage.getUserCount();
    
    // Delete the user
    await usersPage.deleteUser(0);
    
    // Wait for success message
    await expect(page.getByText(/user deleted successfully/i)).toBeVisible();
    
    // Verify user is gone
    await page.reload();
    await usersPage.searchUsers(testUser.email);
    const newCount = await usersPage.getUserCount();
    expect(newCount).toBe(0);
  });

  test('should search users', async ({ page }) => {
    // Create multiple test users
    const users = await Promise.all([
      testDataManager.createTestUser({
        email: generateTestEmail(),
        password: 'TestPassword123!',
        firstName: 'Alice',
        lastName: 'Anderson',
      }),
      testDataManager.createTestUser({
        email: generateTestEmail(),
        password: 'TestPassword123!',
        firstName: 'Bob',
        lastName: 'Brown',
      }),
      testDataManager.createTestUser({
        email: generateTestEmail(),
        password: 'TestPassword123!',
        firstName: 'Charlie',
        lastName: 'Clark',
      }),
    ]);
    
    await page.reload();
    
    // Search by name
    await usersPage.searchUsers('Alice');
    let count = await usersPage.getUserCount();
    expect(count).toBe(1);
    await expect(page.getByText('Alice Anderson')).toBeVisible();
    
    // Search by email
    await usersPage.searchUsers(users[1].email);
    count = await usersPage.getUserCount();
    expect(count).toBe(1);
    await expect(page.getByText(users[1].email)).toBeVisible();
    
    // Clear search
    await usersPage.searchUsers('');
    await page.waitForTimeout(500);
    count = await usersPage.getUserCount();
    expect(count).toBeGreaterThan(3); // Including existing users
  });

  test('should validate user form', async ({ page }) => {
    await usersPage.addUserButton.click();
    
    // Try to submit empty form
    await usersPage.submitButton.click();
    
    // Check validation messages
    await expect(page.getByText(/email.*required/i)).toBeVisible();
    await expect(page.getByText(/first name.*required/i)).toBeVisible();
    await expect(page.getByText(/last name.*required/i)).toBeVisible();
    
    // Test invalid email
    await usersPage.emailInput.fill('invalid-email');
    await usersPage.submitButton.click();
    await expect(page.getByText(/invalid email/i)).toBeVisible();
  });

  test('should handle duplicate email error', async ({ page }) => {
    const existingEmail = 'admin@example.com';
    
    await usersPage.addUser({
      email: existingEmail,
      firstName: 'Duplicate',
      lastName: 'User',
      role: 'user',
    });
    
    // Should show error
    await expect(page.getByText(/email already exists/i)).toBeVisible();
  });

  test('should paginate users list', async ({ page }) => {
    // Create many users to trigger pagination
    const userPromises = [];
    for (let i = 0; i < 15; i++) {
      userPromises.push(
        testDataManager.createTestUser({
          email: generateTestEmail(),
          password: 'TestPassword123!',
          firstName: `User${i}`,
          lastName: `Test${i}`,
        })
      );
    }
    await Promise.all(userPromises);
    
    await page.reload();
    
    // Check pagination controls exist
    await expect(page.getByRole('navigation', { name: /pagination/i })).toBeVisible();
    
    // Navigate to next page
    await page.getByRole('button', { name: /next/i }).click();
    
    // Verify different users are shown
    await expect(page.url()).toContain('page=2');
  });
});