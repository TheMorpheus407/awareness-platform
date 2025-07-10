import { create } from 'zustand';
import type { User, AuthResponse } from '../types';
import apiClient from '../services/api';
import toast from 'react-hot-toast';
import { secureStorage } from '../utils/secureStorage';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; full_name: string; company_name?: string }) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const response: AuthResponse = await apiClient.login(email, password);
      const { access_token, user } = response;
      
      secureStorage.setAccessToken(access_token);
      set({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
      });
      
      toast.success('Login successful!');
    } catch (error: any) {
      set({ isLoading: false });
      toast.error(error.response?.data?.detail || 'Login failed');
      throw error;
    }
  },

  register: async (data) => {
    set({ isLoading: true });
    try {
      const response: AuthResponse = await apiClient.register(data);
      const { access_token, user } = response;
      
      secureStorage.setAccessToken(access_token);
      set({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
      });
      
      toast.success('Registration successful!');
    } catch (error: any) {
      set({ isLoading: false });
      toast.error(error.response?.data?.detail || 'Registration failed');
      throw error;
    }
  },

  logout: () => {
    secureStorage.clearTokens();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
    toast.success('Logged out successfully');
  },

  checkAuth: async () => {
    const token = secureStorage.getAccessToken();
    if (!token) {
      set({ isAuthenticated: false, user: null, token: null });
      return;
    }

    try {
      const user = await apiClient.getCurrentUser();
      set({
        user,
        token,
        isAuthenticated: true,
      });
    } catch (error) {
      secureStorage.clearTokens();
      set({
        user: null,
        token: null,
        isAuthenticated: false,
      });
    }
  },
}));