import api from './api';
import type {
  Campaign,
  CampaignCreate,
  CampaignUpdate,
  CampaignStatus,
  EmailTemplate,
  EmailTemplateCreate,
  EmailTemplateUpdate,
  EmailTemplateType,
  EmailPreferences,
  EmailPreferencesUpdate,
  CampaignStats,
  EmailLog,
} from '../types/emailCampaign';

class EmailCampaignService {
  // Email Templates
  async getTemplates(
    type?: EmailTemplateType,
    isActive?: boolean
  ): Promise<EmailTemplate[]> {
    const params = new URLSearchParams();
    if (type) params.append('type', type);
    if (isActive !== undefined) params.append('is_active', String(isActive));

    const response = await api.get(`/email/templates?${params}`);
    return response.data;
  }

  async getTemplate(templateId: string): Promise<EmailTemplate> {
    const response = await api.get(`/email/templates/${templateId}`);
    return response.data;
  }

  async createTemplate(template: EmailTemplateCreate): Promise<EmailTemplate> {
    const response = await api.post('/email/templates', template);
    return response.data;
  }

  async updateTemplate(
    templateId: string,
    updates: EmailTemplateUpdate
  ): Promise<EmailTemplate> {
    const response = await api.patch(`/email/templates/${templateId}`, updates);
    return response.data;
  }

  async deleteTemplate(templateId: string): Promise<void> {
    await api.delete(`/email/templates/${templateId}`);
  }

  async testTemplate(
    templateId: string,
    toEmail: string,
    variables?: Record<string, any>
  ): Promise<void> {
    await api.post(`/email/templates/${templateId}/test`, {
      to_email: toEmail,
      variables: variables || {},
    });
  }

  // Email Campaigns
  async getCampaigns(status?: CampaignStatus): Promise<Campaign[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);

    const response = await api.get(`/email/campaigns?${params}`);
    return response.data;
  }

  async getCampaign(campaignId: string): Promise<Campaign> {
    const response = await api.get(`/email/campaigns/${campaignId}`);
    return response.data;
  }

  async createCampaign(campaign: CampaignCreate): Promise<Campaign> {
    const response = await api.post('/email/campaigns', campaign);
    return response.data;
  }

  async updateCampaign(
    campaignId: string,
    updates: CampaignUpdate
  ): Promise<Campaign> {
    const response = await api.patch(`/email/campaigns/${campaignId}`, updates);
    return response.data;
  }

  async sendCampaign(
    campaignId: string,
    options: {
      send_immediately: boolean;
      test_mode?: boolean;
      test_recipients?: string[];
    }
  ): Promise<{ message: string; task_id?: string }> {
    const response = await api.post(`/email/campaigns/${campaignId}/send`, options);
    return response.data;
  }

  async getCampaignRecipients(
    campaignId: string
  ): Promise<{
    total: number;
    recipients: Array<{
      id: string;
      email: string;
      name: string;
      role: string | null;
    }>;
  }> {
    const response = await api.get(`/email/campaigns/${campaignId}/recipients`);
    return response.data;
  }

  async getCampaignStats(campaignId: string): Promise<CampaignStats> {
    const response = await api.get(`/email/campaigns/${campaignId}/stats`);
    return response.data;
  }

  async getCampaignLogs(
    campaignId: string,
    status?: string,
    skip = 0,
    limit = 100
  ): Promise<EmailLog[]> {
    const params = new URLSearchParams({
      skip: String(skip),
      limit: String(limit),
    });
    if (status) params.append('status', status);

    const response = await api.get(
      `/email/campaigns/${campaignId}/logs?${params}`
    );
    return response.data;
  }

  // Email Preferences
  async getPreferences(): Promise<EmailPreferences> {
    const response = await api.get('/email/preferences');
    return response.data;
  }

  async updatePreferences(
    updates: EmailPreferencesUpdate
  ): Promise<EmailPreferences> {
    const response = await api.patch('/email/preferences', updates);
    return response.data;
  }

  async unsubscribe(userId: string, token: string): Promise<void> {
    await api.post(`/email/unsubscribe?user=${userId}&token=${token}`);
  }

  // Helper methods
  getTemplateVariables(template: EmailTemplate): string[] {
    const variableNames = Object.keys(template.variables || {});
    return variableNames;
  }

  validateTemplateVariables(
    template: EmailTemplate,
    providedVariables: Record<string, any>
  ): string[] {
    const required = this.getTemplateVariables(template);
    const provided = Object.keys(providedVariables);
    return required.filter((v) => !provided.includes(v));
  }
}

export const emailCampaignService = new EmailCampaignService();