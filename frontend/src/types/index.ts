export * from './auth';
export * from './api';
export * from './user';
export * from './course';

export interface ApiError {
  detail: string;
  status_code?: number;
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
  total_courses: number;
  completion_rate: number;
}