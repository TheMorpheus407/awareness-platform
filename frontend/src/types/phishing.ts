/**
 * Phishing simulation types
 */

export enum CampaignStatus {
  DRAFT = 'draft',
  SCHEDULED = 'scheduled',
  RUNNING = 'running',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export enum TemplateDifficulty {
  EASY = 'easy',
  MEDIUM = 'medium',
  HARD = 'hard'
}

export enum TemplateCategory {
  CREDENTIAL_HARVESTING = 'credential_harvesting',
  MALWARE = 'malware',
  BUSINESS_EMAIL_COMPROMISE = 'business_email_compromise',
  SOCIAL_ENGINEERING = 'social_engineering',
  TECH_SUPPORT = 'tech_support',
  INVOICE_FRAUD = 'invoice_fraud',
  PACKAGE_DELIVERY = 'package_delivery',
  SOCIAL_MEDIA = 'social_media',
  GENERAL = 'general'
}

export interface PhishingTemplate {
  id: number;
  name: string;
  category: TemplateCategory;
  difficulty: TemplateDifficulty;
  subject: string;
  sender_name: string;
  sender_email: string;
  html_content: string;
  text_content?: string;
  landing_page_html?: string;
  language: string;
  is_public: boolean;
  company_id?: number;
  created_at: string;
  updated_at: string;
}

export interface CampaignTargetGroup {
  type: 'department' | 'role' | 'users';
  value: string[];
}

export interface CampaignSettings {
  track_opens: boolean;
  track_clicks: boolean;
  capture_credentials: boolean;
  redirect_url?: string;
  landing_page_url?: string;
  training_url?: string;
  send_rate_per_hour?: number;
  randomize_send_times: boolean;
}

export interface PhishingCampaign {
  id: number;
  company_id: number;
  created_by_id: number;
  name: string;
  description?: string;
  status: CampaignStatus;
  template_id: number;
  target_groups: CampaignTargetGroup[];
  scheduled_at?: string;
  started_at?: string;
  completed_at?: string;
  settings: CampaignSettings;
  created_at: string;
  updated_at: string;
  
  // Statistics
  total_recipients: number;
  emails_sent: number;
  emails_opened: number;
  links_clicked: number;
  credentials_entered: number;
  reported: number;
  
  // Rates
  open_rate: number;
  click_rate: number;
  report_rate: number;
  
  // Relations
  template?: PhishingTemplate;
}

export interface PhishingResult {
  id: number;
  campaign_id: number;
  user_id: number;
  email_sent_at?: string;
  email_opened_at?: string;
  link_clicked_at?: string;
  data_submitted_at?: string;
  reported_at?: string;
  ip_address?: string;
  user_agent?: string;
  location_data?: any;
  created_at: string;
  updated_at: string;
  
  // Computed
  was_clicked: boolean;
  was_reported: boolean;
  response_time_seconds?: number;
}

export interface CampaignAnalytics {
  campaign_id: number;
  campaign_name: string;
  status: CampaignStatus;
  
  // Timing
  scheduled_at?: string;
  started_at?: string;
  completed_at?: string;
  duration_hours?: number;
  
  // Recipients
  total_recipients: number;
  emails_sent: number;
  emails_pending: number;
  emails_failed: number;
  
  // Engagement
  unique_opens: number;
  total_opens: number;
  unique_clicks: number;
  total_clicks: number;
  credentials_entered: number;
  reported_suspicious: number;
  
  // Rates
  delivery_rate: number;
  open_rate: number;
  click_rate: number;
  report_rate: number;
  failure_rate: number;
  
  // Time metrics
  avg_time_to_open_minutes?: number;
  avg_time_to_click_minutes?: number;
  fastest_click_minutes?: number;
  
  // Risk
  risk_score: number;
  
  // Breakdown
  department_stats: any[];
  role_stats: any[];
}

export interface ComplianceReport {
  company_id: number;
  report_period_start: string;
  report_period_end: string;
  
  // Campaign statistics
  total_campaigns: number;
  total_users_tested: number;
  unique_users_tested: number;
  
  // Results
  total_emails_sent: number;
  total_clicks: number;
  overall_click_rate: number;
  overall_report_rate: number;
  
  // Trends
  click_rate_trend: 'improving' | 'stable' | 'declining';
  report_rate_trend: 'improving' | 'stable' | 'declining';
  
  // Training
  users_requiring_training: number;
  users_completed_training: number;
  training_completion_rate: number;
  
  // Risk
  high_risk_users: any[];
  departmental_risk_scores: any[];
  
  // Compliance
  testing_frequency_compliant: boolean;
  coverage_compliant: boolean;
  training_compliant: boolean;
  overall_compliance_score: number;
}

export interface PhishingDashboard {
  total_campaigns: number;
  active_campaigns: number;
  total_users_tested: number;
  overall_click_rate: number;
  recent_campaigns: Array<{
    id: number;
    name: string;
    status: CampaignStatus;
    click_rate: number;
    started_at?: string;
  }>;
}

// Form types
export interface PhishingTemplateForm {
  name: string;
  category: TemplateCategory;
  difficulty: TemplateDifficulty;
  subject: string;
  sender_name: string;
  sender_email: string;
  html_content: string;
  text_content?: string;
  landing_page_html?: string;
  language: string;
  is_public: boolean;
}

export interface PhishingCampaignForm {
  name: string;
  description?: string;
  template_id: number;
  target_groups: CampaignTargetGroup[];
  scheduled_at?: string;
  settings: CampaignSettings;
}