import type { User } from './api';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginWith2FACredentials {
  email: string;
  password: string;
  totp_code: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  full_name: string;
  company_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface TwoFactorSetupResponse {
  secret: string;
  qr_code: string;
  backup_codes: string[];
  manual_entry_key: string;
}

export interface TwoFactorVerifyRequest {
  totp_code: string;
}

export interface TwoFactorDisableRequest {
  password: string;
  totp_code: string;
}

export interface BackupCodesStatus {
  total_codes: number;
  used_codes: number;
  remaining_codes: number;
}