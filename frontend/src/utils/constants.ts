export const APP_NAME = 'CyberAware';
export const APP_VERSION = '1.0.0';

export const USER_ROLES = {
  ADMIN: 'admin',
  COMPANY_ADMIN: 'company_admin',
  USER: 'user',
} as const;

export const PASSWORD_REQUIREMENTS = {
  MIN_LENGTH: 8,
  REQUIRE_UPPERCASE: true,
  REQUIRE_LOWERCASE: true,
  REQUIRE_NUMBER: true,
  REQUIRE_SPECIAL: true,
};

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    ME: '/auth/me',
    LOGOUT: '/auth/logout',
  },
  USERS: '/users',
  COMPANIES: '/companies',
  COURSES: '/courses',
  PHISHING: '/phishing',
  REPORTS: '/reports',
  DASHBOARD: '/dashboard',
};