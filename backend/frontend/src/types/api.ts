export interface ApiError {
  detail: string;
  status?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface DashboardStats {
  total_users: number;
  active_users: number;
  total_companies: number;
  courses_completed: number;
  phishing_campaigns: number;
  compliance_score: number;
}

export interface Company {
  id: string;
  name: string;
  domain: string;
  size: 'small' | 'medium' | 'large' | 'enterprise';
  subscription_tier: 'free' | 'starter' | 'professional' | 'enterprise';
  max_users: number;
  industry?: string;
  country?: string;
  city?: string;
  address?: string;
  postal_code?: string;
  phone?: string;
  website?: string;
  is_active: boolean;
  employee_count?: number;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  role: 'user' | 'company_admin' | 'admin';
  company_id?: string;
  company?: Company;
  department?: string;
  job_title?: string;
  phone?: string;
  phone_number?: string;
  language: string;
  timezone: string;
  is_active: boolean;
  is_verified: boolean;
  email_notifications_enabled: boolean;
  totp_enabled: boolean;
  has_2fa_enabled: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}