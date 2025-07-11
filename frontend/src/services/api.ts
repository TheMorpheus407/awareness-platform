import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import type { ApiError, UserUpdateData, CompanyCreateData, CompanyUpdateData, ApiConfig } from '../types';
import { secureStorage } from '../utils/secureStorage';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiClient {
  private client: AxiosInstance;
  private csrfToken: string | null = null;

  constructor() {
    // Migrate any existing tokens from localStorage
    secureStorage.migrateFromLocalStorage();

    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Enable sending cookies
    });

    // Initialize CSRF token
    this.initializeCsrfToken();

    // Request interceptor to add token and CSRF token
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token
        const token = secureStorage.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add CSRF token for state-changing requests
        const isStateChangingMethod = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(config.method?.toUpperCase() || '');
        const isExcludedPath = ['/auth/login', '/auth/register', '/auth/csrf-token'].some(path => 
          config.url?.includes(path)
        );
        
        if (isStateChangingMethod && !isExcludedPath && this.csrfToken) {
          config.headers['X-CSRF-Token'] = this.csrfToken;
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        // Extract CSRF token from response headers if present
        const csrfToken = response.headers['x-csrf-token'];
        if (csrfToken) {
          this.csrfToken = csrfToken;
        }
        return response;
      },
      async (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          secureStorage.clearTokens();
          
          // Only redirect to login if we're not already on a public page
          const publicPaths = ['/', '/login', '/register', '/pricing'];
          const currentPath = window.location.pathname;
          
          if (!publicPaths.includes(currentPath)) {
            window.location.href = '/login';
          }
        } else if (error.response?.status === 403 && error.response?.data?.detail?.includes('CSRF')) {
          // CSRF token missing or invalid, try to refresh it
          try {
            await this.fetchCsrfToken();
            // Retry the original request
            if (error.config) {
              error.config.headers['X-CSRF-Token'] = this.csrfToken;
              return this.client.request(error.config);
            }
          } catch (csrfError) {
            console.error('Failed to refresh CSRF token:', csrfError);
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private async initializeCsrfToken() {
    try {
      await this.fetchCsrfToken();
    } catch (error) {
      console.warn('Failed to initialize CSRF token:', error);
    }
  }

  private async fetchCsrfToken() {
    try {
      const response = await this.client.get('/auth/csrf-token');
      this.csrfToken = response.data.csrf_token;
      return this.csrfToken;
    } catch (error) {
      console.error('Failed to fetch CSRF token:', error);
      throw error;
    }
  }

  get axios() {
    return this.client;
  }

  // Auth endpoints
  async login(email: string, password: string) {
    // Create URL-encoded form data
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    
    try {
      const response = await this.client.post('/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      // Refresh CSRF token after successful login
      await this.fetchCsrfToken();
      
      return response.data;
    } catch (error) {
      // Check if 2FA is required
      if (error.response?.status === 428) {
        throw { requires2FA: true, ...error };
      }
      throw error;
    }
  }

  async loginWith2FA(email: string, password: string, totpCode: string) {
    const response = await this.client.post('/auth/login-2fa', {
      email,
      password,
      totp_code: totpCode,
    });
    
    // Refresh CSRF token after successful login
    await this.fetchCsrfToken();
    
    return response.data;
  }

  async loginWithBackupCode(email: string, password: string, backupCode: string) {
    const response = await this.client.post('/auth/login-backup-code', {
      email,
      password,
      backup_code: backupCode,
    });
    
    // Refresh CSRF token after successful login
    await this.fetchCsrfToken();
    
    return response.data;
  }

  async register(data: { email: string; password: string; full_name: string; company_name?: string }) {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // 2FA endpoints
  async setup2FA(password: string) {
    const response = await this.client.post('/auth/2fa/setup', { password });
    return response.data;
  }

  async verify2FASetup(totpCode: string) {
    const response = await this.client.post('/auth/2fa/verify', { totp_code: totpCode });
    return response.data;
  }

  async disable2FA(password: string, totpCode: string) {
    const response = await this.client.post('/auth/2fa/disable', { 
      password, 
      totp_code: totpCode 
    });
    return response.data;
  }

  async getBackupCodesStatus() {
    const response = await this.client.get('/auth/2fa/backup-codes');
    return response.data;
  }

  async regenerateBackupCodes(password: string, totpCode: string) {
    const response = await this.client.post('/auth/2fa/regenerate-backup-codes', {
      password,
      totp_code: totpCode
    });
    return response.data;
  }

  // Users endpoints
  async getUsers(page = 1, size = 20) {
    const response = await this.client.get('/users', {
      params: { page, size },
    });
    return response.data;
  }

  async getUser(id: string) {
    const response = await this.client.get(`/users/${id}`);
    return response.data;
  }

  async updateUser(id: string, data: UserUpdateData) {
    const response = await this.client.put(`/users/${id}`, data);
    return response.data;
  }

  async deleteUser(id: string) {
    const response = await this.client.delete(`/users/${id}`);
    return response.data;
  }

  // Companies endpoints
  async getCompanies(page = 1, size = 20) {
    const response = await this.client.get('/companies', {
      params: { page, size },
    });
    return response.data;
  }

  async getCompany(id: string) {
    const response = await this.client.get(`/companies/${id}`);
    return response.data;
  }

  async createCompany(data: CompanyCreateData) {
    const response = await this.client.post('/companies', data);
    return response.data;
  }

  async updateCompany(id: string, data: CompanyUpdateData) {
    const response = await this.client.put(`/companies/${id}`, data);
    return response.data;
  }

  async deleteCompany(id: string) {
    const response = await this.client.delete(`/companies/${id}`);
    return response.data;
  }

  // Dashboard
  async getDashboardStats() {
    const response = await this.client.get('/dashboard/stats');
    return response.data;
  }

  // Convenience methods for direct HTTP calls
  get<T = unknown>(url: string, config?: ApiConfig) {
    return this.client.get<T>(url, config);
  }

  post<T = unknown>(url: string, data?: unknown, config?: ApiConfig) {
    return this.client.post<T>(url, data, config);
  }

  put<T = unknown>(url: string, data?: unknown, config?: ApiConfig) {
    return this.client.put<T>(url, data, config);
  }

  patch<T = unknown>(url: string, data?: unknown, config?: ApiConfig) {
    return this.client.patch<T>(url, data, config);
  }

  delete<T = unknown>(url: string, config?: ApiConfig) {
    return this.client.delete<T>(url, config);
  }
}

export const apiClient = new ApiClient();
export const api = apiClient;
export default apiClient;