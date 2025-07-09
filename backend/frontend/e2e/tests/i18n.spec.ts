import { test, expect } from '../fixtures/auth.fixture';

test.describe('Internationalization (i18n)', () => {
  test('should switch language on login page', async ({ page, loginPage }) => {
    await loginPage.goto();
    
    // Default should be English
    await expect(loginPage.submitButton).toContainText('Sign In');
    await expect(page.getByText('Welcome back')).toBeVisible();
    
    // Switch to German
    await loginPage.switchLanguage('de');
    await expect(loginPage.submitButton).toContainText('Anmelden');
    await expect(page.getByText('Willkommen zurück')).toBeVisible();
    
    // Switch back to English
    await loginPage.switchLanguage('en');
    await expect(loginPage.submitButton).toContainText('Sign In');
  });

  test('should persist language preference after login', async ({ page, loginPage, dashboardPage }) => {
    await loginPage.goto();
    
    // Switch to German before login
    await loginPage.switchLanguage('de');
    
    // Login
    await loginPage.login('admin@example.com', 'AdminPassword123!');
    
    // Check dashboard is in German
    await expect(page).toHaveURL('/dashboard');
    await expect(dashboardPage.navigationLinks.users).toContainText('Benutzer');
    await expect(dashboardPage.navigationLinks.companies).toContainText('Unternehmen');
  });

  test('should switch language in authenticated pages', async ({ page, authenticatedPage, dashboardPage }) => {
    await dashboardPage.goto();
    
    // Find and click language switcher
    const langSwitcher = page.getByRole('button', { name: /EN|DE/i });
    const currentLang = await langSwitcher.textContent();
    
    if (currentLang === 'EN') {
      await langSwitcher.click();
      await expect(dashboardPage.navigationLinks.users).toContainText('Benutzer');
    } else {
      await langSwitcher.click();
      await expect(dashboardPage.navigationLinks.users).toContainText('Users');
    }
  });

  test('should display validation messages in selected language', async ({ loginPage }) => {
    await loginPage.goto();
    
    // Switch to German
    await loginPage.switchLanguage('de');
    
    // Submit empty form
    await loginPage.submitButton.click();
    
    // Check German validation messages
    await expect(loginPage.page.getByText(/e-mail.*erforderlich/i)).toBeVisible();
    await expect(loginPage.page.getByText(/passwort.*erforderlich/i)).toBeVisible();
  });

  test('should handle language in error messages', async ({ loginPage }) => {
    await loginPage.goto();
    
    // Switch to German
    await loginPage.switchLanguage('de');
    
    // Try invalid login
    await loginPage.login('invalid@example.com', 'wrongpassword');
    
    // Error should be in German
    await expect(loginPage.errorMessage).toContainText(/ungültige e-mail oder passwort/i);
  });
});