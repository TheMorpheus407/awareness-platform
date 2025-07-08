import { api } from './api';

export interface SetupIntentResponse {
  client_secret: string;
  setup_intent_id: string;
}

export interface PaymentMethod {
  id: string;
  type: string;
  is_default: boolean;
  display_name: string;
  card_brand?: string;
  card_last4?: string;
  card_exp_month?: number;
  card_exp_year?: number;
  created_at: string;
}

export interface Subscription {
  id: string;
  status: string;
  billing_interval: string;
  amount: number;
  currency: string;
  current_period_start: string;
  current_period_end: string;
  trial_end: string | null;
  cancel_at: string | null;
  created_at: string;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  status: string;
  total: number;
  currency: string;
  period_start: string;
  period_end: string;
  due_date: string | null;
  paid_at: string | null;
  invoice_pdf_url: string | null;
  hosted_invoice_url: string | null;
  created_at: string;
}

export interface Payment {
  id: string;
  status: string;
  amount: number;
  currency: string;
  payment_method_type: string;
  paid_at: string | null;
  failure_message: string | null;
  created_at: string;
}

export interface PricingTier {
  price_id: string;
  product_id: string;
  product_name: string;
  tier: string;
  amount: number;
  currency: string;
  interval: string;
  interval_count: number;
  features: string[];
}

export interface SubscriptionCreateData {
  price_id: string;
  payment_method_id?: string;
}

export interface SubscriptionUpdateData {
  price_id: string;
  prorate?: boolean;
}

export interface PaymentMethodCreateData {
  payment_method_id: string;
  set_as_default?: boolean;
}

class PaymentService {
  // Setup Intent
  async createSetupIntent(): Promise<SetupIntentResponse> {
    const response = await api.post<SetupIntentResponse>('/payments/setup-intent');
    return response.data;
  }

  // Payment Methods
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    const response = await api.get<PaymentMethod[]>('/payments/payment-methods');
    return response.data;
  }

  async addPaymentMethod(data: PaymentMethodCreateData): Promise<PaymentMethod> {
    const response = await api.post<PaymentMethod>('/payments/payment-methods', data);
    return response.data;
  }

  async removePaymentMethod(paymentMethodId: string): Promise<void> {
    await api.delete(`/payments/payment-methods/${paymentMethodId}`);
  }

  // Subscriptions
  async getSubscription(): Promise<Subscription | null> {
    const response = await api.get<Subscription | null>('/payments/subscription');
    return response.data;
  }

  async createSubscription(data: SubscriptionCreateData): Promise<Subscription> {
    const response = await api.post<Subscription>('/payments/subscription', data);
    return response.data;
  }

  async updateSubscription(data: SubscriptionUpdateData): Promise<Subscription> {
    const response = await api.put<Subscription>('/payments/subscription', data);
    return response.data;
  }

  async cancelSubscription(immediate: boolean = false): Promise<void> {
    await api.delete('/payments/subscription', {
      params: { immediate },
    });
  }

  // Invoices
  async getInvoices(limit: number = 50, offset: number = 0): Promise<Invoice[]> {
    const response = await api.get<Invoice[]>('/payments/invoices', {
      params: { limit, offset },
    });
    return response.data;
  }

  async getInvoice(invoiceId: string): Promise<Invoice> {
    const response = await api.get<Invoice>(`/payments/invoices/${invoiceId}`);
    return response.data;
  }

  // Payments
  async getPayments(limit: number = 50, offset: number = 0): Promise<Payment[]> {
    const response = await api.get<Payment[]>('/payments/payments', {
      params: { limit, offset },
    });
    return response.data;
  }

  // Pricing
  async getPricing(): Promise<PricingTier[]> {
    const response = await api.get<PricingTier[]>('/payments/prices');
    return response.data;
  }

  // Usage
  async recordUsage(metricName: string, quantity: number, timestamp?: Date): Promise<void> {
    await api.post('/payments/usage', {
      metric_name: metricName,
      quantity,
      timestamp: timestamp?.toISOString(),
    });
  }
}

export const paymentService = new PaymentService();