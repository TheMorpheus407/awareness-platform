import { vi } from 'vitest';

const mockAuthStore = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  checkAuth: vi.fn(),
  setUser: vi.fn(),
  setLoading: vi.fn(),
};

export const useAuthStore = vi.fn(() => mockAuthStore);