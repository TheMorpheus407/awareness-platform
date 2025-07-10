import type { Page, Locator } from '@playwright/test';

export class CompaniesPage {
  readonly page: Page;
  readonly addCompanyButton: Locator;
  readonly searchInput: Locator;
  readonly companyTable: Locator;
  readonly companyRows: Locator;
  readonly editButtons: Locator;
  readonly deleteButtons: Locator;
  readonly viewDetailsButtons: Locator;
  
  // Form fields
  readonly nameInput: Locator;
  readonly domainInput: Locator;
  readonly industrySelect: Locator;
  readonly employeeCountInput: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.addCompanyButton = page.getByRole('button', { name: /add company|unternehmen hinzufügen/i });
    this.searchInput = page.getByPlaceholder(/search|suchen/i);
    this.companyTable = page.getByRole('table');
    this.companyRows = page.locator('tbody tr');
    this.editButtons = page.getByRole('button', { name: /edit|bearbeiten/i });
    this.deleteButtons = page.getByRole('button', { name: /delete|löschen/i });
    this.viewDetailsButtons = page.getByRole('button', { name: /view|anzeigen/i });
    
    // Form fields
    this.nameInput = page.getByLabel(/company name|unternehmensname/i);
    this.domainInput = page.getByLabel(/domain/i);
    this.industrySelect = page.getByLabel(/industry|branche/i);
    this.employeeCountInput = page.getByLabel(/employee count|mitarbeiterzahl/i);
    this.submitButton = page.getByRole('button', { name: /save|speichern/i });
    this.cancelButton = page.getByRole('button', { name: /cancel|abbrechen/i });
  }

  async goto() {
    await this.page.goto('/companies');
  }

  async searchCompanies(query: string) {
    await this.searchInput.fill(query);
    // Wait for debounce
    await this.page.waitForTimeout(500);
  }

  async addCompany(companyData: {
    name: string;
    domain: string;
    industry: string;
    employeeCount: number;
  }) {
    await this.addCompanyButton.click();
    await this.nameInput.fill(companyData.name);
    await this.domainInput.fill(companyData.domain);
    await this.industrySelect.selectOption(companyData.industry);
    await this.employeeCountInput.fill(companyData.employeeCount.toString());
    await this.submitButton.click();
  }

  async editCompany(index: number, updates: Partial<{
    name: string;
    domain: string;
    industry: string;
    employeeCount: number;
  }>) {
    await this.editButtons.nth(index).click();
    
    if (updates.name) {
      await this.nameInput.clear();
      await this.nameInput.fill(updates.name);
    }
    
    if (updates.domain) {
      await this.domainInput.clear();
      await this.domainInput.fill(updates.domain);
    }
    
    if (updates.industry) {
      await this.industrySelect.selectOption(updates.industry);
    }
    
    if (updates.employeeCount) {
      await this.employeeCountInput.clear();
      await this.employeeCountInput.fill(updates.employeeCount.toString());
    }
    
    await this.submitButton.click();
  }

  async deleteCompany(index: number) {
    await this.deleteButtons.nth(index).click();
    // Confirm in dialog
    await this.page.getByRole('button', { name: /confirm|bestätigen/i }).click();
  }

  async getCompanyCount() {
    return await this.companyRows.count();
  }

  async getCompanyData(index: number) {
    const row = this.companyRows.nth(index);
    const cells = row.locator('td');
    
    return {
      name: await cells.nth(0).textContent(),
      domain: await cells.nth(1).textContent(),
      industry: await cells.nth(2).textContent(),
      employeeCount: await cells.nth(3).textContent(),
      status: await cells.nth(4).textContent(),
    };
  }
}