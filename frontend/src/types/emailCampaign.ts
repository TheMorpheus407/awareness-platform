export enum EmailTemplateType {
  TRANSACTIONAL = 'transactional',
  CAMPAIGN = 'campaign',
  NEWSLETTER = 'newsletter',
  NOTIFICATION = 'notification',
  WELCOME = 'welcome',
  COURSE_UPDATE = 'course_update',
  PHISHING_ALERT = 'phishing_alert',
  SECURITY_ALERT = 'security_alert',
}

export enum CampaignStatus {
  DRAFT = 'draft',
  SCHEDULED = 'scheduled',
  SENDING = 'sending',
  SENT = 'sent',
  PAUSED = 'paused',
  CANCELLED = 'cancelled',
  COMPLETED = 'completed',
}

export enum EmailStatus {
  PENDING = 'pending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  OPENED = 'opened',
  CLICKED = 'clicked',
  BOUNCED = 'bounced',
  FAILED = 'failed',
  UNSUBSCRIBED = 'unsubscribed',
  MARKED_SPAM = 'marked_spam',
}

export enum EmailFrequency {
  IMMEDIATELY = 'immediately',
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
  NEVER = 'never',
}

export interface EmailTemplate {
  id: string;
  name: string;
  slug: string;
  type: EmailTemplateType;
  subject: string;
  html_content: string;
  text_content?: string;
  variables?: Record<string, any>;
  preview_text?: string;
  from_name?: string;
  from_email?: string;
  reply_to?: string;
  is_active: boolean;
  is_default: boolean;
  created_by_id?: string;
  created_at: string;
  updated_at: string;
  total_sent: number;
  total_opened: number;
  total_clicked: number;
  avg_open_rate: number;
  avg_click_rate: number;
}

export interface EmailTemplateCreate {
  name: string;
  slug: string;
  type: EmailTemplateType;
  subject: string;
  html_content: string;
  text_content?: string;
  variables?: Record<string, any>;
  preview_text?: string;
  from_name?: string;
  from_email?: string;
  reply_to?: string;
  is_active?: boolean;
}

export interface EmailTemplateUpdate {
  name?: string;
  subject?: string;
  html_content?: string;
  text_content?: string;
  variables?: Record<string, any>;
  preview_text?: string;
  from_name?: string;
  from_email?: string;
  reply_to?: string;
  is_active?: boolean;
}

export interface Campaign {
  id: string;
  name: string;
  description?: string;
  template_id: string;
  company_id?: string;
  status: CampaignStatus;
  scheduled_at?: string;
  sent_at?: string;
  completed_at?: string;
  target_all_users: boolean;
  target_user_roles: string[];
  target_user_ids: string[];
  target_segments: Record<string, any>;
  exclude_unsubscribed: boolean;
  custom_subject?: string;
  custom_preview_text?: string;
  custom_variables?: Record<string, any>;
  total_recipients: number;
  total_sent: number;
  total_delivered: number;
  total_opened: number;
  total_clicked: number;
  total_bounced: number;
  total_unsubscribed: number;
  delivery_rate: number;
  open_rate: number;
  click_rate: number;
  bounce_rate: number;
  unsubscribe_rate: number;
  created_by_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CampaignCreate {
  name: string;
  description?: string;
  template_id: string;
  scheduled_at?: string;
  target_all_users?: boolean;
  target_user_roles?: string[];
  target_user_ids?: string[];
  target_segments?: Record<string, any>;
  exclude_unsubscribed?: boolean;
  custom_subject?: string;
  custom_preview_text?: string;
  custom_variables?: Record<string, any>;
}

export interface CampaignUpdate {
  name?: string;
  description?: string;
  template_id?: string;
  scheduled_at?: string;
  status?: CampaignStatus;
  target_all_users?: boolean;
  target_user_roles?: string[];
  target_user_ids?: string[];
  target_segments?: Record<string, any>;
  exclude_unsubscribed?: boolean;
  custom_subject?: string;
  custom_preview_text?: string;
  custom_variables?: Record<string, any>;
}

export interface EmailLog {
  id: string;
  campaign_id?: string;
  template_id?: string;
  user_id?: string;
  to_email: string;
  from_email: string;
  subject: string;
  status: EmailStatus;
  sent_at?: string;
  delivered_at?: string;
  opened_at?: string;
  first_opened_at?: string;
  clicked_at?: string;
  first_clicked_at?: string;
  bounced_at?: string;
  unsubscribed_at?: string;
  open_count: number;
  click_count: number;
  clicked_links: string[];
  error_message?: string;
  bounce_type?: string;
  provider?: string;
  message_id?: string;
  created_at: string;
  updated_at: string;
}

export interface EmailPreferences {
  id: string;
  user_id: string;
  is_subscribed: boolean;
  marketing_emails: boolean;
  course_updates: boolean;
  security_alerts: boolean;
  newsletter: boolean;
  promotional: boolean;
  email_frequency: EmailFrequency;
  digest_day?: number;
  digest_hour?: number;
  unsubscribed_at?: string;
  unsubscribe_token?: string;
  created_at: string;
  updated_at: string;
}

export interface EmailPreferencesUpdate {
  is_subscribed?: boolean;
  marketing_emails?: boolean;
  course_updates?: boolean;
  security_alerts?: boolean;
  newsletter?: boolean;
  promotional?: boolean;
  email_frequency?: EmailFrequency;
  digest_day?: number;
  digest_hour?: number;
}

export interface CampaignStats {
  campaign_id: string;
  name: string;
  status: CampaignStatus;
  scheduled_at?: string;
  sent_at?: string;
  completed_at?: string;
  total_recipients: number;
  total_sent: number;
  total_delivered: number;
  total_opened: number;
  total_clicked: number;
  total_bounced: number;
  total_unsubscribed: number;
  delivery_rate: number;
  open_rate: number;
  click_rate: number;
  bounce_rate: number;
  unsubscribe_rate: number;
  opens_by_hour: Record<number, number>;
  clicks_by_hour: Record<number, number>;
  opens_by_device: Record<string, number>;
  clicks_by_device: Record<string, number>;
  link_clicks: Array<{
    url: string;
    clicks: number;
    unique_clicks: number;
  }>;
}