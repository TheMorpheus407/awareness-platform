export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'company_admin' | 'user';
  company_id?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
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

export interface Company {
  id: string;
  name: string;
  domain: string;
  employee_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}