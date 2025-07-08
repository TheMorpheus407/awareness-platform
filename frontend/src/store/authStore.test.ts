import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useAuthStore } from './authStore';

// Create mock functions
const mockLogin = vi.fn();
const mockRegister = vi.fn();
const mockGetCurrentUser = vi.fn();
const mockToastSuccess = vi.fn();
const mockToastError = vi.fn();

// Mock the entire api module
vi.mock('../services/api', () => ({
  default: {
    login: mockLogin,
    register: mockRegister,
    getCurrentUser: mockGetCurrentUser,
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: mockToastSuccess,
    error: mockToastError,
  },
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('authStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
    
    // Reset store to initial state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
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
      mockLogin.mockResolvedValueOnce(mockAuthResponse);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });
      
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe('test-token');
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'test-token');
      expect(mockToastSuccess).toHaveBeenCalledWith('Login successful!');
    });

    it('should handle login failure', async () => {
      const errorMessage = 'Invalid credentials';
      const error = {
        response: { data: { detail: errorMessage } },
      };
      mockLogin.mockRejectedValueOnce(error);
      
      const { result } = renderHook(() => useAuthStore());
      
      let thrownError;
      try {
        await act(async () => {
          await result.current.login('test@example.com', 'wrongpassword');
        });
      } catch (e) {
        thrownError = e;
      }
      
      expect(thrownError).toBeDefined();
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
      expect(mockToastError).toHaveBeenCalledWith(errorMessage);
    });
  });

  describe('Logout', () => {
    it('should clear auth state on logout', () => {
      const { result } = renderHook(() => useAuthStore());
      
      // Set some initial state first
      act(() => {
        useAuthStore.setState({
          user: { id: 1, email: 'test@example.com' } as any,
          token: 'test-token',
          isAuthenticated: true,
        });
      });
      
      // Now logout
      act(() => {
        result.current.logout();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockToastSuccess).toHaveBeenCalledWith('Logged out successfully');
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
      mockGetCurrentUser.mockResolvedValueOnce(mockUser);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.checkAuth();
      });
      
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe('valid-token');
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should clear auth when token is invalid', async () => {
      localStorageMock.getItem.mockReturnValueOnce('invalid-token');
      mockGetCurrentUser.mockRejectedValueOnce(new Error('Unauthorized'));
      
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
});