import { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { secureStorage } from '../utils/secureStorage';

export const useAuth = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    checkAuth,
  } = useAuthStore();

  useEffect(() => {
    // Only check auth if there's a token, preventing unnecessary 401s on public pages
    const token = secureStorage.getAccessToken();
    if (token) {
      checkAuth();
    }
  }, []);

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
  };
};