import type { Page, Locator } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly userMenu: Locator;
  readonly logoutButton: Locator;
  readonly statsCards: Locator;
  readonly welcomeMessage: Locator;
  readonly navigationLinks: {
    dashboard: Locator;
    users: Locator;
    companies: Locator;
  };

  constructor(page: Page) {
    this.page = page;
    this.userMenu = page.getByRole('button', { name: /user menu|benutzermenü/i });
    this.logoutButton = page.getByRole('button', { name: /logout|abmelden/i });
    this.statsCards = page.locator('[data-testid="stats-card"]');
    this.welcomeMessage = page.getByRole('heading', { level: 1 });
    
    this.navigationLinks = {
      dashboard: page.getByRole('link', { name: /dashboard/i }),
      users: page.getByRole('link', { name: /users|benutzer/i }),
      companies: page.getByRole('link', { name: /companies|unternehmen/i }),
    };
  }

  async goto() {
    await this.page.goto('/dashboard');
  }

  async logout() {
    await this.userMenu.click();
    await this.logoutButton.click();
  }

  async navigateTo(section: keyof typeof this.navigationLinks) {
    await this.navigationLinks[section].click();
  }

  async getStatsCount() {
    return await this.statsCards.count();
  }

  async getWelcomeText() {
    return await this.welcomeMessage.textContent();
  }
}