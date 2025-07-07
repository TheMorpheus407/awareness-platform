import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import apiClient from './api';

// Create a mock adapter
const mock = new MockAdapter(axios);

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Mock window.location
delete (window as any).location;
window.location = { href: '' } as any;

describe('ApiClient', () => {
  beforeEach(() => {
    mock.reset();
    localStorageMock.getItem.mockClear();
    localStorageMock.removeItem.mockClear();
    window.location.href = '';
  });

  afterAll(() => {
    mock.restore();
  });

  describe('Request Interceptor', () => {
    it('adds authorization header when token exists', async () => {
      const token = 'test-token';
      localStorageMock.getItem.mockReturnValue(token);

      // Create a new mock for the specific axios instance
      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/test').reply((config) => {
        expect(config.headers?.Authorization).toBe(`Bearer ${token}`);
        return [200, { success: true }];
      });

      await apiClient.axios.get('/test');
      expect(localStorageMock.getItem).toHaveBeenCalledWith('access_token');
      
      apiMock.restore();
    });

    it('does not add authorization header when no token', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/test').reply((config) => {
        expect(config.headers?.Authorization).toBeUndefined();
        return [200, { success: true }];
      });

      await apiClient.axios.get('/test');
      expect(localStorageMock.getItem).toHaveBeenCalledWith('access_token');
      
      apiMock.restore();
    });
  });

  describe('Response Interceptor', () => {
    it('handles 401 errors by removing token and redirecting', async () => {
      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/test').reply(401, { detail: 'Unauthorized' });

      try {
        await apiClient.axios.get('/test');
      } catch (error) {
        // Expected to throw
      }

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(window.location.href).toBe('/login');
      
      apiMock.restore();
    });

    it('passes through successful responses', async () => {
      const responseData = { success: true };
      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/test').reply(200, responseData);

      const response = await apiClient.axios.get('/test');
      expect(response.data).toEqual(responseData);
      
      apiMock.restore();
    });

    it('passes through non-401 errors', async () => {
      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/test').reply(500, { detail: 'Server error' });

      await expect(apiClient.axios.get('/test')).rejects.toThrow();
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
      expect(window.location.href).toBe('');
      
      apiMock.restore();
    });
  });

  describe('Auth Endpoints', () => {
    it('login sends correct form data', async () => {
      const email = 'test@example.com';
      const password = 'password123';
      const responseData = { access_token: 'token', token_type: 'bearer' };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onPost('/auth/login').reply((config) => {
        expect(config.headers?.['Content-Type']).toBe('application/x-www-form-urlencoded');
        
        // Check form data
        const formData = new URLSearchParams(config.data);
        expect(formData.get('username')).toBe(email);
        expect(formData.get('password')).toBe(password);
        
        return [200, responseData];
      });

      const result = await apiClient.login(email, password);
      expect(result).toEqual(responseData);
      
      apiMock.restore();
    });

    it('register sends correct JSON data', async () => {
      const registrationData = {
        email: 'new@example.com',
        password: 'password123',
        full_name: 'New User',
        company_name: 'Test Company',
      };
      const responseData = { id: 1, ...registrationData };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onPost('/auth/register').reply((config) => {
        expect(JSON.parse(config.data)).toEqual(registrationData);
        return [200, responseData];
      });

      const result = await apiClient.register(registrationData);
      expect(result).toEqual(responseData);
      
      apiMock.restore();
    });

    it('getCurrentUser fetches user data', async () => {
      const userData = { id: 1, email: 'user@example.com', full_name: 'Test User' };
      
      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/auth/me').reply(200, userData);

      const result = await apiClient.getCurrentUser();
      expect(result).toEqual(userData);
      
      apiMock.restore();
    });
  });

  describe('Users Endpoints', () => {
    it('getUsers fetches paginated users', async () => {
      const page = 2;
      const size = 10;
      const usersData = {
        items: [{ id: 1, email: 'user1@example.com' }],
        total: 100,
        pages: 10,
      };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/users').reply((config) => {
        expect(config.params).toEqual({ page, size });
        return [200, usersData];
      });

      const result = await apiClient.getUsers(page, size);
      expect(result).toEqual(usersData);
      
      apiMock.restore();
    });

    it('getUsers uses default pagination', async () => {
      const usersData = { items: [], total: 0, pages: 0 };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/users').reply((config) => {
        expect(config.params).toEqual({ page: 1, size: 20 });
        return [200, usersData];
      });

      await apiClient.getUsers();
      
      apiMock.restore();
    });

    it('getUser fetches single user', async () => {
      const userId = '123';
      const userData = { id: userId, email: 'user@example.com' };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet(`/users/${userId}`).reply(200, userData);

      const result = await apiClient.getUser(userId);
      expect(result).toEqual(userData);
      
      apiMock.restore();
    });

    it('updateUser sends PUT request', async () => {
      const userId = '123';
      const updateData = { email: 'updated@example.com' };
      const responseData = { id: userId, ...updateData };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onPut(`/users/${userId}`).reply((config) => {
        expect(JSON.parse(config.data)).toEqual(updateData);
        return [200, responseData];
      });

      const result = await apiClient.updateUser(userId, updateData);
      expect(result).toEqual(responseData);
      
      apiMock.restore();
    });

    it('deleteUser sends DELETE request', async () => {
      const userId = '123';
      const responseData = { message: 'User deleted' };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onDelete(`/users/${userId}`).reply(200, responseData);

      const result = await apiClient.deleteUser(userId);
      expect(result).toEqual(responseData);
      
      apiMock.restore();
    });
  });

  describe('Companies Endpoints', () => {
    it('getCompanies fetches paginated companies', async () => {
      const page = 1;
      const size = 15;
      const companiesData = {
        items: [{ id: 1, name: 'Company 1' }],
        total: 50,
        pages: 4,
      };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/companies').reply((config) => {
        expect(config.params).toEqual({ page, size });
        return [200, companiesData];
      });

      const result = await apiClient.getCompanies(page, size);
      expect(result).toEqual(companiesData);
      
      apiMock.restore();
    });

    it('getCompany fetches single company', async () => {
      const companyId = '456';
      const companyData = { id: companyId, name: 'Test Company' };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet(`/companies/${companyId}`).reply(200, companyData);

      const result = await apiClient.getCompany(companyId);
      expect(result).toEqual(companyData);
      
      apiMock.restore();
    });

    it('createCompany sends POST request', async () => {
      const createData = { name: 'New Company', domain: 'newcompany.com' };
      const responseData = { id: 1, ...createData };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onPost('/companies').reply((config) => {
        expect(JSON.parse(config.data)).toEqual(createData);
        return [201, responseData];
      });

      const result = await apiClient.createCompany(createData);
      expect(result).toEqual(responseData);
      
      apiMock.restore();
    });

    it('updateCompany sends PUT request', async () => {
      const companyId = '789';
      const updateData = { name: 'Updated Company' };
      const responseData = { id: companyId, ...updateData };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onPut(`/companies/${companyId}`).reply((config) => {
        expect(JSON.parse(config.data)).toEqual(updateData);
        return [200, responseData];
      });

      const result = await apiClient.updateCompany(companyId, updateData);
      expect(result).toEqual(responseData);
      
      apiMock.restore();
    });

    it('deleteCompany sends DELETE request', async () => {
      const companyId = '999';
      const responseData = { message: 'Company deleted' };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onDelete(`/companies/${companyId}`).reply(200, responseData);

      const result = await apiClient.deleteCompany(companyId);
      expect(result).toEqual(responseData);
      
      apiMock.restore();
    });
  });

  describe('Dashboard Endpoints', () => {
    it('getDashboardStats fetches stats', async () => {
      const statsData = {
        totalUsers: 100,
        activeCompanies: 25,
        completedCourses: 500,
        phishingCaught: 75,
      };

      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/dashboard/stats').reply(200, statsData);

      const result = await apiClient.getDashboardStats();
      expect(result).toEqual(statsData);
      
      apiMock.restore();
    });
  });

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/test').networkError();

      await expect(apiClient.axios.get('/test')).rejects.toThrow();
      
      apiMock.restore();
    });

    it('handles timeout errors', async () => {
      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onGet('/test').timeout();

      await expect(apiClient.axios.get('/test')).rejects.toThrow();
      
      apiMock.restore();
    });

    it('preserves error response data', async () => {
      const errorData = { detail: 'Validation error', errors: ['Invalid email'] };
      const apiMock = new MockAdapter(apiClient.axios);
      apiMock.onPost('/test').reply(400, errorData);

      try {
        await apiClient.axios.post('/test');
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(400);
        expect(error.response.data).toEqual(errorData);
      }
      
      apiMock.restore();
    });
  });
});