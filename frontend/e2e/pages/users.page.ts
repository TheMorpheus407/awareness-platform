import type { Page, Locator } from '@playwright/test';

export class UsersPage {
  readonly page: Page;
  readonly addUserButton: Locator;
  readonly searchInput: Locator;
  readonly userTable: Locator;
  readonly userRows: Locator;
  readonly editButtons: Locator;
  readonly deleteButtons: Locator;
  readonly confirmDeleteButton: Locator;
  readonly cancelButton: Locator;
  
  // Form fields
  readonly emailInput: Locator;
  readonly firstNameInput: Locator;
  readonly lastNameInput: Locator;
  readonly roleSelect: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.addUserButton = page.getByRole('button', { name: /add user|benutzer hinzufügen/i });
    this.searchInput = page.getByPlaceholder(/search|suchen/i);
    this.userTable = page.getByRole('table');
    this.userRows = page.locator('tbody tr');
    this.editButtons = page.getByRole('button', { name: /edit|bearbeiten/i });
    this.deleteButtons = page.getByRole('button', { name: /delete|löschen/i });
    this.confirmDeleteButton = page.getByRole('button', { name: /confirm|bestätigen/i });
    this.cancelButton = page.getByRole('button', { name: /cancel|abbrechen/i });
    
    // Form fields
    this.emailInput = page.getByLabel(/email/i);
    this.firstNameInput = page.getByLabel(/first name|vorname/i);
    this.lastNameInput = page.getByLabel(/last name|nachname/i);
    this.roleSelect = page.getByLabel(/role|rolle/i);
    this.submitButton = page.getByRole('button', { name: /save|speichern/i });
  }

  async goto() {
    await this.page.goto('/users');
  }

  async searchUsers(query: string) {
    await this.searchInput.fill(query);
    // Wait for debounce
    await this.page.waitForTimeout(500);
  }

  async addUser(userData: {
    email: string;
    firstName: string;
    lastName: string;
    role: 'admin' | 'instructor' | 'user';
  }) {
    await this.addUserButton.click();
    await this.emailInput.fill(userData.email);
    await this.firstNameInput.fill(userData.firstName);
    await this.lastNameInput.fill(userData.lastName);
    await this.roleSelect.selectOption(userData.role);
    await this.submitButton.click();
  }

  async editUser(index: number, updates: Partial<{
    firstName: string;
    lastName: string;
    role: string;
  }>) {
    await this.editButtons.nth(index).click();
    
    if (updates.firstName) {
      await this.firstNameInput.clear();
      await this.firstNameInput.fill(updates.firstName);
    }
    
    if (updates.lastName) {
      await this.lastNameInput.clear();
      await this.lastNameInput.fill(updates.lastName);
    }
    
    if (updates.role) {
      await this.roleSelect.selectOption(updates.role);
    }
    
    await this.submitButton.click();
  }

  async deleteUser(index: number) {
    await this.deleteButtons.nth(index).click();
    await this.confirmDeleteButton.click();
  }

  async getUserCount() {
    return await this.userRows.count();
  }

  async getUserData(index: number) {
    const row = this.userRows.nth(index);
    const cells = row.locator('td');
    
    return {
      email: await cells.nth(0).textContent(),
      name: await cells.nth(1).textContent(),
      role: await cells.nth(2).textContent(),
      status: await cells.nth(3).textContent(),
    };
  }
}