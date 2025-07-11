import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuth } from './useAuth';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';

// Mock the API module
vi.mock('../services/api', () => ({
  default: {
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
    enable2FA: vi.fn(),
    disable2FA: vi.fn(),
    verify2FA: vi.fn(),
  },
  setAuthToken: vi.fn(),
  removeAuthToken: vi.fn(),
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

describe('useAuth Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
    // Reset auth store
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  describe('Login', () => {
    it('should login successfully', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'employee',
      };
      const mockTokens = {
        access_token: 'access-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer',
      };

      vi.mocked(api.login).mockResolvedValue(mockTokens);
      vi.mocked(api.getCurrentUser).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });

      expect(api.login).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', mockTokens.access_token);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', mockTokens.refresh_token);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });

    it('should handle login with 2FA', async () => {
      const mock2FAResponse = {
        requires_2fa: true,
        temp_token: 'temp-token-123',
      };

      vi.mocked(api.login).mockResolvedValue(mock2FAResponse);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        const response = await result.current.login('test@example.com', 'password123');
        expect(response).toEqual(mock2FAResponse);
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('2fa_temp_token', mock2FAResponse.temp_token);
    });

    it('should handle login failure', async () => {
      const mockError = new Error('Invalid credentials');
      vi.mocked(api.login).mockRejectedValue(mockError);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        try {
          await result.current.login('test@example.com', 'wrongpassword');
        } catch (error) {
          expect(error).toBe(mockError);
        }
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.error).toBe('Invalid credentials');
    });
  });

  describe('Registration', () => {
    it('should register successfully', async () => {
      const registrationData = {
        email: 'new@example.com',
        password: 'SecurePass123!',
        firstName: 'New',
        lastName: 'User',
        companyName: 'New Company',
      };

      const mockResponse = {
        id: 1,
        ...registrationData,
        message: 'Registration successful',
      };

      vi.mocked(api.register).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        const response = await result.current.register(registrationData);
        expect(response).toEqual(mockResponse);
      });

      expect(api.register).toHaveBeenCalledWith(registrationData);
    });

    it('should handle registration failure', async () => {
      const mockError = new Error('Email already exists');
      vi.mocked(api.register).mockRejectedValue(mockError);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        try {
          await result.current.register({
            email: 'existing@example.com',
            password: 'password123',
            firstName: 'Test',
            lastName: 'User',
          });
        } catch (error) {
          expect(error).toBe(mockError);
        }
      });

      expect(result.current.error).toBe('Email already exists');
    });
  });

  describe('Logout', () => {
    it('should logout successfully', async () => {
      // Set initial authenticated state
      useAuthStore.setState({
        user: { id: 1, email: 'test@example.com' },
        isAuthenticated: true,
      });

      vi.mocked(api.logout).mockResolvedValue({ message: 'Logged out' });

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.logout();
      });

      expect(api.logout).toHaveBeenCalled();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('should handle logout failure gracefully', async () => {
      vi.mocked(api.logout).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.logout();
      });

      // Should still clear local state even if API call fails
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Check Auth Status', () => {
    it('should restore auth from localStorage', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
      };

      localStorageMock.getItem.mockReturnValue('valid-token');
      vi.mocked(api.getCurrentUser).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(api.getCurrentUser).toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });

    it('should handle invalid token', async () => {
      localStorageMock.getItem.mockReturnValue('invalid-token');
      vi.mocked(api.getCurrentUser).mockRejectedValue(new Error('Unauthorized'));

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('should handle no token', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(api.getCurrentUser).not.toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Update Profile', () => {
    it('should update profile successfully', async () => {
      const updateData = {
        firstName: 'Updated',
        lastName: 'Name',
        phoneNumber: '+1234567890',
      };

      const updatedUser = {
        id: 1,
        email: 'test@example.com',
        ...updateData,
      };

      vi.mocked(api.updateProfile).mockResolvedValue(updatedUser);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.updateProfile(updateData);
      });

      expect(api.updateProfile).toHaveBeenCalledWith(updateData);
      expect(result.current.user).toEqual(updatedUser);
    });
  });

  describe('Change Password', () => {
    it('should change password successfully', async () => {
      vi.mocked(api.changePassword).mockResolvedValue({ message: 'Password changed' });

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.changePassword('oldPassword', 'newPassword');
      });

      expect(api.changePassword).toHaveBeenCalledWith('oldPassword', 'newPassword');
    });

    it('should handle password change failure', async () => {
      const mockError = new Error('Invalid current password');
      vi.mocked(api.changePassword).mockRejectedValue(mockError);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        try {
          await result.current.changePassword('wrongPassword', 'newPassword');
        } catch (error) {
          expect(error).toBe(mockError);
        }
      });
    });
  });

  describe('Two-Factor Authentication', () => {
    it('should enable 2FA successfully', async () => {
      const mock2FASetup = {
        secret: 'secret-key',
        qr_code: 'data:image/png;base64,qrcode',
        backup_codes: ['code1', 'code2', 'code3'],
      };

      vi.mocked(api.enable2FA).mockResolvedValue(mock2FASetup);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        const response = await result.current.enable2FA();
        expect(response).toEqual(mock2FASetup);
      });

      expect(api.enable2FA).toHaveBeenCalled();
    });

    it('should disable 2FA successfully', async () => {
      vi.mocked(api.disable2FA).mockResolvedValue({ message: '2FA disabled' });

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.disable2FA('password123');
      });

      expect(api.disable2FA).toHaveBeenCalledWith('password123');
    });

    it('should verify 2FA code successfully', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
      };
      const mockTokens = {
        access_token: 'access-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer',
      };

      localStorageMock.getItem.mockReturnValue('temp-token');
      vi.mocked(api.verify2FA).mockResolvedValue(mockTokens);
      vi.mocked(api.getCurrentUser).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.verify2FA('123456');
      });

      expect(api.verify2FA).toHaveBeenCalledWith('temp-token', '123456');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('2fa_temp_token');
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });
  });

  describe('Token Refresh', () => {
    it('should refresh token automatically', async () => {
      const newTokens = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
      };

      vi.mocked(api.refreshToken).mockResolvedValue(newTokens);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.refreshAuthToken();
      });

      expect(api.refreshToken).toHaveBeenCalled();
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', newTokens.access_token);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', newTokens.refresh_token);
    });

    it('should handle refresh token failure', async () => {
      vi.mocked(api.refreshToken).mockRejectedValue(new Error('Invalid refresh token'));

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.refreshAuthToken();
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Permission Checks', () => {
    it('should check if user has role', () => {
      useAuthStore.setState({
        user: {
          id: 1,
          email: 'test@example.com',
          role: 'admin',
        },
        isAuthenticated: true,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.hasRole('admin')).toBe(true);
      expect(result.current.hasRole('employee')).toBe(false);
    });

    it('should check if user has permission', () => {
      useAuthStore.setState({
        user: {
          id: 1,
          email: 'test@example.com',
          role: 'admin',
          permissions: ['manage_users', 'view_reports'],
        },
        isAuthenticated: true,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.hasPermission('manage_users')).toBe(true);
      expect(result.current.hasPermission('delete_company')).toBe(false);
    });

    it('should return false for permissions when not authenticated', () => {
      const { result } = renderHook(() => useAuth());

      expect(result.current.hasRole('admin')).toBe(false);
      expect(result.current.hasPermission('any_permission')).toBe(false);
    });
  });
});