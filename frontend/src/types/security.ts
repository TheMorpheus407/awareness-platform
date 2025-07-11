/**
 * Security-related TypeScript interfaces to replace 'any' types
 */

// API Response types
export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  message?: string;
  error?: ApiError;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  field?: string;
}

export interface ApiConfig {
  headers?: Record<string, string>;
  params?: Record<string, string | number | boolean>;
  timeout?: number;
  withCredentials?: boolean;
  signal?: AbortSignal;
}

// WebSocket types
export interface WebSocketMessage<T = unknown> {
  type: string;
  payload: T;
  timestamp: number;
  id?: string;
}

export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

// Form data types
export interface FormFieldValue {
  value: string | number | boolean | File | FileList;
  error?: string;
  touched?: boolean;
}

export interface FormData {
  [key: string]: FormFieldValue | FormData;
}

// Event handler types
export interface ChangeEvent<T = HTMLInputElement> {
  target: T;
  currentTarget: T;
  preventDefault: () => void;
  stopPropagation: () => void;
}

export interface SubmitEvent {
  preventDefault: () => void;
  stopPropagation: () => void;
}

// Component prop types
export interface BaseComponentProps {
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

export interface LoadingSpinnerProps extends BaseComponentProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
}

export interface ErrorMessageProps extends BaseComponentProps {
  message: string;
  type?: 'error' | 'warning' | 'info';
  onDismiss?: () => void;
}

// User management types
export interface UserUpdateData {
  first_name?: string;
  last_name?: string;
  role?: string;
  department?: string;
  is_active?: boolean;
}

export interface CompanyCreateData {
  name: string;
  industry: string;
  size: string;
  domains: string[];
}

export interface CompanyUpdateData {
  name?: string;
  industry?: string;
  size?: string;
  domains?: string[];
  settings?: CompanySettings;
}

export interface CompanySettings {
  enforce_2fa?: boolean;
  password_policy?: PasswordPolicy;
  session_timeout?: number;
  allowed_domains?: string[];
}

export interface PasswordPolicy {
  min_length: number;
  require_uppercase: boolean;
  require_lowercase: boolean;
  require_numbers: boolean;
  require_special: boolean;
  max_age_days?: number;
}

// Email preferences types
export interface EmailPreference {
  key: string;
  value: boolean | string | number;
  label: string;
  description?: string;
}

export interface EmailPreferenceUpdate {
  [key: string]: boolean | string | number;
}

// Phishing types
export interface PhishingLocationData {
  ip?: string;
  country?: string;
  city?: string;
  region?: string;
  user_agent?: string;
}

export interface PhishingStats {
  department_stats: DepartmentStat[];
  role_stats: RoleStat[];
}

export interface DepartmentStat {
  department: string;
  click_rate: number;
  report_rate: number;
  total_users: number;
}

export interface RoleStat {
  role: string;
  click_rate: number;
  report_rate: number;
  total_users: number;
}

export interface RiskAssessment {
  high_risk_users: RiskUser[];
  departmental_risk_scores: DepartmentalRisk[];
}

export interface RiskUser {
  user_id: string;
  email: string;
  risk_score: number;
  factors: string[];
}

export interface DepartmentalRisk {
  department: string;
  average_risk_score: number;
  user_count: number;
}

// Analytics types
export interface AnalyticsData {
  labels: string[];
  datasets: Dataset[];
}

export interface Dataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
}

// i18n types
export interface TranslationProps {
  children: string | React.ReactNode;
  values?: Record<string, string | number>;
}

// Test setup types
export interface MockedFunction<T extends (...args: any[]) => any> {
  (...args: Parameters<T>): ReturnType<T>;
  mockClear(): void;
  mockReset(): void;
  mockRestore(): void;
  mockReturnValue(value: ReturnType<T>): void;
  mockResolvedValue(value: Awaited<ReturnType<T>>): void;
  mockRejectedValue(error: any): void;
}

// Error handling types
export interface ErrorWithMessage {
  message: string;
  code?: string;
  statusCode?: number;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

// Validation types
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => string | undefined;
}

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

// Security headers
export interface SecurityHeaders {
  'X-Content-Type-Options': string;
  'X-Frame-Options': string;
  'X-XSS-Protection': string;
  'Referrer-Policy': string;
  'Content-Security-Policy': string;
  'Strict-Transport-Security'?: string;
  'Permissions-Policy': string;
}

// Rate limiting
export interface RateLimitInfo {
  limited: boolean;
  limits?: Record<string, number>;
  current_usage?: Record<string, number>;
  retry_after?: number;
}

// CSRF token
export interface CSRFToken {
  token: string;
  expiresAt: number;
}