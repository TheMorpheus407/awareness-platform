export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  company_id?: number;
  created_at: string;
  updated_at: string;
}