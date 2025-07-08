import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from './authStore';
import apiClient from '../services/api';
import toast from 'react-hot-toast';

// Mock dependencies
vi.mock('../services/api', () => ({
  default: {
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

describe('authStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    
    // Reset store state
    const { result } = renderHook(() => useAuthStore());
    act(() => {
      result.current.logout();
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useAuthStore());
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Login', () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      first_name: 'Test',
      last_name: 'User',
      full_name: 'Test User',
      role: 'user',
      is_active: true,
      is_verified: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    const mockAuthResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      user: mockUser,
    };

    it('should login successfully', async () => {
      vi.mocked(apiClient.login).mockResolvedValueOnce(mockAuthResponse);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });
      
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe('test-token');
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'test-token');
      expect(toast.success).toHaveBeenCalledWith('Login successful!');
    });

    it('should handle login failure', async () => {
      const errorMessage = 'Invalid credentials';
      vi.mocked(apiClient.login).mockRejectedValueOnce({
        response: { data: { detail: errorMessage } },
      });
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await expect(result.current.login('test@example.com', 'wrongpassword')).rejects.toThrow();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
      expect(toast.error).toHaveBeenCalledWith(errorMessage);
    });

    it('should handle generic login error', async () => {
      vi.mocked(apiClient.login).mockRejectedValueOnce(new Error('Network error'));
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await expect(result.current.login('test@example.com', 'password')).rejects.toThrow();
      });
      
      expect(toast.error).toHaveBeenCalledWith('Login failed');
    });

    it('should set isLoading during login', async () => {
      let resolveLogin: any;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });
      
      vi.mocked(apiClient.login).mockReturnValueOnce(loginPromise);
      
      const { result } = renderHook(() => useAuthStore());
      
      // Start login
      act(() => {
        result.current.login('test@example.com', 'password');
      });
      
      // Check loading state
      expect(result.current.isLoading).toBe(true);
      
      // Resolve login
      await act(async () => {
        resolveLogin(mockAuthResponse);
        await loginPromise;
      });
      
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Register', () => {
    const mockUser = {
      id: 1,
      email: 'new@example.com',
      username: 'newuser',
      first_name: 'New',
      last_name: 'User',
      full_name: 'New User',
      role: 'user',
      is_active: true,
      is_verified: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    const mockAuthResponse = {
      access_token: 'new-token',
      token_type: 'bearer',
      user: mockUser,
    };

    const registrationData = {
      email: 'new@example.com',
      password: 'password123',
      full_name: 'New User',
      company_name: 'Test Company',
    };

    it('should register successfully', async () => {
      vi.mocked(apiClient.register).mockResolvedValueOnce(mockAuthResponse);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.register(registrationData);
      });
      
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe('new-token');
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'new-token');
      expect(toast.success).toHaveBeenCalledWith('Registration successful!');
    });

    it('should handle registration failure', async () => {
      const errorMessage = 'Email already registered';
      vi.mocked(apiClient.register).mockRejectedValueOnce({
        response: { data: { detail: errorMessage } },
      });
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await expect(result.current.register(registrationData)).rejects.toThrow();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
      expect(toast.error).toHaveBeenCalledWith(errorMessage);
    });

    it('should handle generic registration error', async () => {
      vi.mocked(apiClient.register).mockRejectedValueOnce(new Error('Network error'));
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await expect(result.current.register(registrationData)).rejects.toThrow();
      });
      
      expect(toast.error).toHaveBeenCalledWith('Registration failed');
    });
  });

  describe('Logout', () => {
    it('should clear auth state on logout', () => {
      const { result } = renderHook(() => useAuthStore());
      
      // Set some initial state
      act(() => {
        result.current.logout();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(toast.success).toHaveBeenCalledWith('Logged out successfully');
    });
  });

  describe('CheckAuth', () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      first_name: 'Test',
      last_name: 'User',
      full_name: 'Test User',
      role: 'user',
      is_active: true,
      is_verified: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should check auth with valid token', async () => {
      localStorageMock.getItem.mockReturnValueOnce('valid-token');
      vi.mocked(apiClient.getCurrentUser).mockResolvedValueOnce(mockUser);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.checkAuth();
      });
      
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe('valid-token');
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should clear auth when no token exists', async () => {
      localStorageMock.getItem.mockReturnValueOnce(null);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.checkAuth();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(apiClient.getCurrentUser).not.toHaveBeenCalled();
    });

    it('should clear auth when token is invalid', async () => {
      localStorageMock.getItem.mockReturnValueOnce('invalid-token');
      vi.mocked(apiClient.getCurrentUser).mockRejectedValueOnce(new Error('Unauthorized'));
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.checkAuth();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
    });
  });

  describe('Store Persistence', () => {
    it('should maintain state across multiple hook instances', () => {
      const { result: result1 } = renderHook(() => useAuthStore());
      const { result: result2 } = renderHook(() => useAuthStore());
      
      // Both should have same initial state
      expect(result1.current.isAuthenticated).toBe(false);
      expect(result2.current.isAuthenticated).toBe(false);
      
      // Update state in one instance
      act(() => {
        result1.current.logout();
      });
      
      // Both should reflect the change
      expect(result1.current.isAuthenticated).toBe(false);
      expect(result2.current.isAuthenticated).toBe(false);
    });
  });
});