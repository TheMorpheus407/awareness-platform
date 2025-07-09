import { describe, it, expect } from 'vitest';
import { APP_NAME, APP_VERSION, USER_ROLES, PASSWORD_REQUIREMENTS, API_ENDPOINTS } from './constants';

describe('Constants', () => {
  describe('App Info', () => {
    it('defines app name and version', () => {
      expect(APP_NAME).toBe('CyberAware');
      expect(APP_VERSION).toBe('1.0.0');
    });
  });

  describe('USER_ROLES', () => {
    it('defines correct user roles', () => {
      expect(USER_ROLES.ADMIN).toBe('admin');
      expect(USER_ROLES.USER).toBe('user');
      expect(USER_ROLES.COMPANY_ADMIN).toBe('company_admin');
    });
  });

  describe('PASSWORD_REQUIREMENTS', () => {
    it('defines password requirements', () => {
      expect(PASSWORD_REQUIREMENTS.MIN_LENGTH).toBe(8);
      expect(PASSWORD_REQUIREMENTS.REQUIRE_UPPERCASE).toBe(true);
      expect(PASSWORD_REQUIREMENTS.REQUIRE_LOWERCASE).toBe(true);
      expect(PASSWORD_REQUIREMENTS.REQUIRE_NUMBER).toBe(true);
      expect(PASSWORD_REQUIREMENTS.REQUIRE_SPECIAL).toBe(true);
    });
  });

  describe('API_ENDPOINTS', () => {
    it('defines auth endpoints', () => {
      expect(API_ENDPOINTS.AUTH.LOGIN).toBe('/auth/login');
      expect(API_ENDPOINTS.AUTH.REGISTER).toBe('/auth/register');
      expect(API_ENDPOINTS.AUTH.LOGOUT).toBe('/auth/logout');
      expect(API_ENDPOINTS.AUTH.ME).toBe('/auth/me');
    });

    it('defines other endpoints', () => {
      expect(API_ENDPOINTS.USERS).toBe('/users');
      expect(API_ENDPOINTS.COMPANIES).toBe('/companies');
      expect(API_ENDPOINTS.COURSES).toBe('/courses');
      expect(API_ENDPOINTS.PHISHING).toBe('/phishing');
      expect(API_ENDPOINTS.REPORTS).toBe('/reports');
      expect(API_ENDPOINTS.DASHBOARD).toBe('/dashboard');
    });
  });
});