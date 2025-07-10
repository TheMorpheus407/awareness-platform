import type { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly registerLink: Locator;
  readonly errorMessage: Locator;
  readonly languageSwitcher: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByPlaceholder(/you@example.com/i);
    this.passwordInput = page.getByPlaceholder(/••••••••/);
    this.submitButton = page.locator('button[type="submit"]');
    this.registerLink = page.getByRole('link', { name: /sign up/i });
    this.errorMessage = page.getByRole('alert');
    this.languageSwitcher = page.locator('button').filter({ hasText: /🇬🇧|🇩🇪/ });
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async switchLanguage(lang: 'en' | 'de') {
    const currentLang = await this.languageSwitcher.textContent();
    const isCurrentlyEnglish = currentLang?.includes('EN');
    const isCurrentlyGerman = currentLang?.includes('DE');
    
    if ((lang === 'en' && isCurrentlyGerman) || (lang === 'de' && isCurrentlyEnglish)) {
      await this.languageSwitcher.click();
      // Wait for dropdown to appear
      await this.page.waitForTimeout(100);
      
      // Click on the desired language in the dropdown
      if (lang === 'de') {
        await this.page.locator('button:has-text("Deutsch")').click();
      } else {
        await this.page.locator('button:has-text("English")').click();
      }
      
      // Wait for language change to take effect
      await this.page.waitForTimeout(500);
    }
  }

  async expectError(message: string | RegExp) {
    await this.page.waitForSelector('[role="alert"]');
    const errorText = await this.errorMessage.textContent();
    if (typeof message === 'string') {
      return errorText?.includes(message);
    }
    return message.test(errorText || '');
  }
}