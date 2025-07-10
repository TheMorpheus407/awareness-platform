import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import type { ApiError } from '../types';
import { secureStorage } from '../utils/secureStorage';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiClient {
  private client: AxiosInstance;

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

    // Request interceptor to add token
    this.client.interceptors.request.use(
      (config) => {
        const token = secureStorage.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          secureStorage.clearTokens();
          
          // Only redirect to login if we're not already on a public page
          const publicPaths = ['/', '/login', '/register', '/pricing'];
          const currentPath = window.location.pathname;
          
          if (!publicPaths.includes(currentPath)) {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  get axios() {
    return this.client;
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    try {
      const response = await this.client.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      return response.data;
    } catch (error: any) {
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
    return response.data;
  }

  async loginWithBackupCode(email: string, password: string, backupCode: string) {
    const response = await this.client.post('/auth/login-backup-code', {
      email,
      password,
      backup_code: backupCode,
    });
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

  async updateUser(id: string, data: any) {
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

  async createCompany(data: any) {
    const response = await this.client.post('/companies', data);
    return response.data;
  }

  async updateCompany(id: string, data: any) {
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
  get(url: string, config?: any) {
    return this.client.get(url, config);
  }

  post(url: string, data?: any, config?: any) {
    return this.client.post(url, data, config);
  }

  put(url: string, data?: any, config?: any) {
    return this.client.put(url, data, config);
  }

  patch(url: string, data?: any, config?: any) {
    return this.client.patch(url, data, config);
  }

  delete(url: string, config?: any) {
    return this.client.delete(url, config);
  }
}

export const apiClient = new ApiClient();
export const api = apiClient;
export default apiClient;