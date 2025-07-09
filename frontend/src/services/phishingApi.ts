/**
 * Phishing simulation API client
 */

import { apiClient } from './api';
import type {
  PhishingTemplate,
  PhishingCampaign,
  CampaignAnalytics,
  ComplianceReport,
  PhishingDashboard,
  PhishingTemplateForm,
  PhishingCampaignForm,
  CampaignStatus
} from '../types/phishing';

export const phishingApi = {
  // Template endpoints
  async getTemplates(params?: {
    categories?: string[];
    difficulties?: string[];
    languages?: string[];
    is_public?: boolean;
    search?: string;
  }): Promise<PhishingTemplate[]> {
    const { data } = await apiClient.axios.get('/phishing/templates', { params });
    return data;
  },

  async getTemplate(id: number): Promise<PhishingTemplate> {
    const { data } = await apiClient.axios.get(`/phishing/templates/${id}`);
    return data;
  },

  async createTemplate(template: PhishingTemplateForm): Promise<PhishingTemplate> {
    const { data } = await apiClient.axios.post('/phishing/templates', template);
    return data;
  },

  async updateTemplate(id: number, template: Partial<PhishingTemplateForm>): Promise<PhishingTemplate> {
    const { data } = await apiClient.axios.put(`/phishing/templates/${id}`, template);
    return data;
  },

  async deleteTemplate(id: number): Promise<void> {
    await apiClient.axios.delete(`/phishing/templates/${id}`);
  },

  // Campaign endpoints
  async getCampaigns(params?: {
    status?: CampaignStatus;
    limit?: number;
    offset?: number;
  }): Promise<PhishingCampaign[]> {
    const { data } = await apiClient.axios.get('/phishing/campaigns', { params });
    return data;
  },

  async getCampaign(id: number): Promise<PhishingCampaign> {
    const { data } = await apiClient.axios.get(`/phishing/campaigns/${id}`);
    return data;
  },

  async createCampaign(campaign: PhishingCampaignForm): Promise<PhishingCampaign> {
    const { data } = await apiClient.axios.post('/phishing/campaigns', campaign);
    return data;
  },

  async updateCampaign(id: number, campaign: Partial<PhishingCampaignForm>): Promise<PhishingCampaign> {
    const { data } = await apiClient.axios.put(`/phishing/campaigns/${id}`, campaign);
    return data;
  },

  async scheduleCampaign(id: number, scheduledAt: string): Promise<PhishingCampaign> {
    const { data } = await apiClient.axios.post(`/phishing/campaigns/${id}/schedule`, null, {
      params: { scheduled_at: scheduledAt }
    });
    return data;
  },

  async startCampaign(id: number): Promise<PhishingCampaign> {
    const { data } = await apiClient.axios.post(`/phishing/campaigns/${id}/start`);
    return data;
  },

  async cancelCampaign(id: number): Promise<PhishingCampaign> {
    const { data } = await apiClient.axios.post(`/phishing/campaigns/${id}/cancel`);
    return data;
  },

  // Analytics endpoints
  async getCampaignAnalytics(id: number): Promise<CampaignAnalytics> {
    const { data } = await apiClient.axios.get(`/phishing/campaigns/${id}/analytics`);
    return data;
  },

  async getComplianceReport(startDate: string, endDate: string): Promise<ComplianceReport> {
    const { data } = await apiClient.axios.get('/phishing/compliance-report', {
      params: { start_date: startDate, end_date: endDate }
    });
    return data;
  },

  async getDashboard(): Promise<PhishingDashboard> {
    const { data } = await apiClient.axios.get('/phishing/dashboard');
    return data;
  },

  // Reporting endpoint
  async reportPhishing(campaignId: number, reason?: string, comments?: string): Promise<void> {
    await apiClient.axios.post('/phishing/report', {
      campaign_id: campaignId,
      reason,
      comments
    });
  }
};