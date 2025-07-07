import { Page, Locator } from '@playwright/test';

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
    this.emailInput = page.getByLabel(/email/i);
    this.passwordInput = page.getByLabel(/password/i);
    this.submitButton = page.getByRole('button', { name: /sign in|anmelden/i });
    this.registerLink = page.getByRole('link', { name: /register|registrieren/i });
    this.errorMessage = page.getByRole('alert');
    this.languageSwitcher = page.getByRole('button', { name: /EN|DE/i });
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
    if ((lang === 'en' && currentLang === 'DE') || (lang === 'de' && currentLang === 'EN')) {
      await this.languageSwitcher.click();
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