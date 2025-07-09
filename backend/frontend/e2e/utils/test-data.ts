import { APIRequestContext } from '@playwright/test';

export class TestDataManager {
  private createdUsers: string[] = [];
  private createdCompanies: string[] = [];
  
  constructor(private request: APIRequestContext) {}

  async createTestUser(userData: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    role?: 'admin' | 'instructor' | 'user';
  }) {
    const response = await this.request.post('/api/v1/auth/register', {
      data: {
        email: userData.email,
        password: userData.password,
        first_name: userData.firstName,
        last_name: userData.lastName,
        role: userData.role || 'user',
        is_active: true,
      },
    });

    if (response.ok()) {
      const user = await response.json();
      this.createdUsers.push(user.id);
      return user;
    }

    throw new Error(`Failed to create test user: ${response.statusText}`);
  }

  async createTestCompany(companyData: {
    name: string;
    domain: string;
    industry?: string;
    employeeCount?: number;
  }, authToken: string) {
    const response = await this.request.post('/api/v1/companies', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
      data: {
        name: companyData.name,
        domain: companyData.domain,
        industry: companyData.industry || 'Technology',
        employee_count: companyData.employeeCount || 100,
        is_active: true,
      },
    });

    if (response.ok()) {
      const company = await response.json();
      this.createdCompanies.push(company.id);
      return company;
    }

    throw new Error(`Failed to create test company: ${response.statusText}`);
  }

  async loginAsAdmin() {
    const response = await this.request.post('/api/v1/auth/login', {
      form: {
        username: 'admin@example.com',
        password: 'AdminPassword123!',
      },
    });

    if (response.ok()) {
      const { access_token } = await response.json();
      return access_token;
    }

    throw new Error('Failed to login as admin');
  }

  async cleanup(authToken: string) {
    // Delete created users
    for (const userId of this.createdUsers) {
      await this.request.delete(`/api/v1/users/${userId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });
    }

    // Delete created companies
    for (const companyId of this.createdCompanies) {
      await this.request.delete(`/api/v1/companies/${companyId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });
    }

    this.createdUsers = [];
    this.createdCompanies = [];
  }
}

export function generateTestEmail() {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `test_${timestamp}_${random}@example.com`;
}

export function generateCompanyDomain() {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `test-company-${timestamp}-${random}.com`;
}