import { test, expect } from '../fixtures/auth.fixture';
import { CompaniesPage } from '../pages/companies.page';
import { TestDataManager, generateCompanyDomain } from '../utils/test-data';

test.describe('Company Management', () => {
  let companiesPage: CompaniesPage;
  let testDataManager: TestDataManager;
  let authToken: string;

  test.beforeEach(async ({ page, authenticatedPage, request }) => {
    companiesPage = new CompaniesPage(page);
    testDataManager = new TestDataManager(request);
    
    // Get auth token for API calls
    authToken = await testDataManager.loginAsAdmin();
    
    await companiesPage.goto();
  });

  test.afterEach(async () => {
    // Cleanup test data
    await testDataManager.cleanup(authToken);
  });

  test('should display companies list', async ({ page }) => {
    await expect(companiesPage.companyTable).toBeVisible();
    await expect(companiesPage.addCompanyButton).toBeVisible();
    await expect(companiesPage.searchInput).toBeVisible();
  });

  test('should add new company', async ({ page }) => {
    const initialCount = await companiesPage.getCompanyCount();
    const testDomain = generateCompanyDomain();
    
    await companiesPage.addCompany({
      name: 'Test Company Inc.',
      domain: testDomain,
      industry: 'Technology',
      employeeCount: 150,
    });
    
    // Wait for success message
    await expect(page.getByText(/company created successfully/i)).toBeVisible();
    
    // Check company count increased
    const newCount = await companiesPage.getCompanyCount();
    expect(newCount).toBe(initialCount + 1);
    
    // Search for the new company
    await companiesPage.searchCompanies('Test Company Inc.');
    await expect(page.getByText('Test Company Inc.')).toBeVisible();
  });

  test('should edit existing company', async ({ page }) => {
    // First create a company
    const testCompany = await testDataManager.createTestCompany({
      name: 'Original Company',
      domain: generateCompanyDomain(),
      industry: 'Healthcare',
      employeeCount: 100,
    }, authToken);
    
    await page.reload();
    await companiesPage.searchCompanies(testCompany.name);
    
    // Edit the company
    await companiesPage.editCompany(0, {
      name: 'Updated Company Name',
      employeeCount: 200,
    });
    
    // Wait for success message
    await expect(page.getByText(/company updated successfully/i)).toBeVisible();
    
    // Verify changes
    await page.reload();
    await companiesPage.searchCompanies('Updated Company Name');
    const companyData = await companiesPage.getCompanyData(0);
    expect(companyData.name).toContain('Updated Company Name');
    expect(companyData.employeeCount).toContain('200');
  });

  test('should delete company', async ({ page }) => {
    // First create a company
    const testCompany = await testDataManager.createTestCompany({
      name: 'Company to Delete',
      domain: generateCompanyDomain(),
    }, authToken);
    
    await page.reload();
    await companiesPage.searchCompanies(testCompany.name);
    
    // Delete the company
    await companiesPage.deleteCompany(0);
    
    // Wait for success message
    await expect(page.getByText(/company deleted successfully/i)).toBeVisible();
    
    // Verify company is gone
    await page.reload();
    await companiesPage.searchCompanies(testCompany.name);
    const count = await companiesPage.getCompanyCount();
    expect(count).toBe(0);
  });

  test('should search companies', async ({ page }) => {
    // Create multiple test companies
    const companies = await Promise.all([
      testDataManager.createTestCompany({
        name: 'Alpha Technologies',
        domain: generateCompanyDomain(),
        industry: 'Technology',
      }, authToken),
      testDataManager.createTestCompany({
        name: 'Beta Healthcare',
        domain: generateCompanyDomain(),
        industry: 'Healthcare',
      }, authToken),
      testDataManager.createTestCompany({
        name: 'Gamma Financial',
        domain: generateCompanyDomain(),
        industry: 'Finance',
      }, authToken),
    ]);
    
    await page.reload();
    
    // Search by name
    await companiesPage.searchCompanies('Alpha');
    let count = await companiesPage.getCompanyCount();
    expect(count).toBe(1);
    await expect(page.getByText('Alpha Technologies')).toBeVisible();
    
    // Search by domain
    await companiesPage.searchCompanies(companies[1].domain);
    count = await companiesPage.getCompanyCount();
    expect(count).toBe(1);
    await expect(page.getByText(companies[1].domain)).toBeVisible();
    
    // Clear search
    await companiesPage.searchCompanies('');
    await page.waitForTimeout(500);
    count = await companiesPage.getCompanyCount();
    expect(count).toBeGreaterThanOrEqual(3);
  });

  test('should validate company form', async ({ page }) => {
    await companiesPage.addCompanyButton.click();
    
    // Try to submit empty form
    await companiesPage.submitButton.click();
    
    // Check validation messages
    await expect(page.getByText(/company name.*required/i)).toBeVisible();
    await expect(page.getByText(/domain.*required/i)).toBeVisible();
    
    // Test invalid domain
    await companiesPage.domainInput.fill('invalid domain');
    await companiesPage.submitButton.click();
    await expect(page.getByText(/invalid domain format/i)).toBeVisible();
  });

  test('should handle duplicate domain error', async ({ page }) => {
    // Create a company first
    const existingCompany = await testDataManager.createTestCompany({
      name: 'Existing Company',
      domain: 'existing-company.com',
    }, authToken);
    
    await page.reload();
    
    // Try to create another company with same domain
    await companiesPage.addCompany({
      name: 'Different Company',
      domain: 'existing-company.com',
      industry: 'Technology',
      employeeCount: 50,
    });
    
    // Should show error
    await expect(page.getByText(/domain already exists/i)).toBeVisible();
  });

  test('should filter companies by industry', async ({ page }) => {
    // Create companies in different industries
    await Promise.all([
      testDataManager.createTestCompany({
        name: 'Tech Company 1',
        domain: generateCompanyDomain(),
        industry: 'Technology',
      }, authToken),
      testDataManager.createTestCompany({
        name: 'Tech Company 2',
        domain: generateCompanyDomain(),
        industry: 'Technology',
      }, authToken),
      testDataManager.createTestCompany({
        name: 'Healthcare Company',
        domain: generateCompanyDomain(),
        industry: 'Healthcare',
      }, authToken),
    ]);
    
    await page.reload();
    
    // Filter by Technology
    await page.getByRole('combobox', { name: /filter by industry/i }).selectOption('Technology');
    await page.waitForTimeout(500);
    
    let count = await companiesPage.getCompanyCount();
    expect(count).toBeGreaterThanOrEqual(2);
    
    // Verify all displayed companies are Technology
    for (let i = 0; i < count; i++) {
      const data = await companiesPage.getCompanyData(i);
      expect(data.industry).toBe('Technology');
    }
  });

  test('should view company details', async ({ page }) => {
    const testCompany = await testDataManager.createTestCompany({
      name: 'Detailed Company',
      domain: generateCompanyDomain(),
      industry: 'Finance',
      employeeCount: 500,
    }, authToken);
    
    await page.reload();
    await companiesPage.searchCompanies(testCompany.name);
    
    // Click view details
    await companiesPage.viewDetailsButtons.first().click();
    
    // Should show company details modal or navigate to details page
    await expect(page.getByRole('heading', { name: testCompany.name })).toBeVisible();
    await expect(page.getByText(testCompany.domain)).toBeVisible();
    await expect(page.getByText('500')).toBeVisible();
    await expect(page.getByText('Finance')).toBeVisible();
  });
});