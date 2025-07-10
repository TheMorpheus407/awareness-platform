import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  CreditCard,
  FileText,
  Calendar,
  Download,
  AlertCircle,
  Check,
  X,
} from 'lucide-react';
import { paymentService } from '../../services/paymentService';
import { LoadingSpinner } from '../Common';
import { format } from 'date-fns';
import { de, enUS } from 'date-fns/locale';
import { useAuthStore } from '../../store/authStore';

interface Subscription {
  id: string;
  status: string;
  billing_interval: string;
  amount: number;
  currency: string;
  current_period_start: string;
  current_period_end: string;
  trial_end: string | null;
  cancel_at: string | null;
}

interface PaymentMethod {
  id: string;
  type: string;
  is_default: boolean;
  display_name: string;
  card_brand?: string;
  card_last4?: string;
  card_exp_month?: number;
  card_exp_year?: number;
}

interface Invoice {
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
}

const BillingDashboard: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [showCancelModal, setShowCancelModal] = useState(false);

  useEffect(() => {
    loadBillingData();
  }, []);

  const loadBillingData = async () => {
    try {
      const [sub, methods, inv] = await Promise.all([
        paymentService.getSubscription(),
        paymentService.getPaymentMethods(),
        paymentService.getInvoices(),
      ]);
      
      setSubscription(sub);
      setPaymentMethods(methods);
      setInvoices(inv);
    } catch (error) {
      console.error('Failed to load billing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const locale = i18n.language === 'de' ? de : enUS;
    return format(date, 'PP', { locale });
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat(i18n.language === 'de' ? 'de-DE' : 'en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount / 100); // Convert cents to currency units
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'green',
      trialing: 'blue',
      past_due: 'red',
      canceled: 'gray',
      paid: 'green',
      open: 'yellow',
      uncollectible: 'red',
    };
    return colors[status] || 'gray';
  };

  const handleCancelSubscription = async () => {
    try {
      await paymentService.cancelSubscription(false);
      await loadBillingData();
      setShowCancelModal(false);
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
    }
  };

  const handleUpdatePaymentMethod = () => {
    // Navigate to payment method update page
    window.location.href = '/payment/update';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          {t('billing.title')}
        </h1>

        {/* Subscription Status */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              {t('billing.subscription.title')}
            </h2>
            
            {subscription ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">{t('billing.subscription.status')}</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium bg-${getStatusColor(subscription.status)}-100 text-${getStatusColor(subscription.status)}-800`}>
                    {t(`billing.subscription.statuses.${subscription.status}`)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-600">{t('billing.subscription.plan')}</span>
                  <span className="font-medium">
                    {formatCurrency(subscription.amount, subscription.currency)} / {t(`billing.subscription.intervals.${subscription.billing_interval}`)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-600">{t('billing.subscription.currentPeriod')}</span>
                  <span className="text-sm">
                    {formatDate(subscription.current_period_start)} - {formatDate(subscription.current_period_end)}
                  </span>
                </div>

                {subscription.trial_end && new Date(subscription.trial_end) > new Date() && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">{t('billing.subscription.trialEnds')}</span>
                    <span className="text-sm font-medium text-blue-600">
                      {formatDate(subscription.trial_end)}
                    </span>
                  </div>
                )}

                {subscription.cancel_at && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">{t('billing.subscription.cancelsAt')}</span>
                    <span className="text-sm font-medium text-red-600">
                      {formatDate(subscription.cancel_at)}
                    </span>
                  </div>
                )}

                <div className="pt-4 border-t flex justify-between">
                  <button
                    onClick={() => window.location.href = '/pricing'}
                    className="text-blue-600 hover:text-blue-800 font-medium"
                  >
                    {t('billing.subscription.changePlan')}
                  </button>
                  
                  {subscription.status !== 'canceled' && (
                    <button
                      onClick={() => setShowCancelModal(true)}
                      className="text-red-600 hover:text-red-800 font-medium"
                    >
                      {t('billing.subscription.cancel')}
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600 mb-4">{t('billing.subscription.none')}</p>
                <button
                  onClick={() => window.location.href = '/pricing'}
                  className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
                >
                  {t('billing.subscription.subscribe')}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Payment Methods */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                {t('billing.paymentMethods.title')}
              </h2>
              <button
                onClick={handleUpdatePaymentMethod}
                className="text-blue-600 hover:text-blue-800 font-medium text-sm"
              >
                {t('billing.paymentMethods.add')}
              </button>
            </div>

            {paymentMethods.length > 0 ? (
              <div className="space-y-3">
                {paymentMethods.map((method) => (
                  <div
                    key={method.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <CreditCard className="h-6 w-6 text-gray-400" />
                      <div>
                        <p className="font-medium">{method.display_name}</p>
                        {method.card_exp_month && method.card_exp_year && (
                          <p className="text-sm text-gray-600">
                            {t('billing.paymentMethods.expires')} {method.card_exp_month}/{method.card_exp_year}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {method.is_default && (
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">
                          {t('billing.paymentMethods.default')}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600 text-center py-4">
                {t('billing.paymentMethods.none')}
              </p>
            )}
          </div>
        </div>

        {/* Invoices */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              {t('billing.invoices.title')}
            </h2>

            {invoices.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('billing.invoices.number')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('billing.invoices.date')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('billing.invoices.amount')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('billing.invoices.status')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('billing.invoices.actions')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {invoices.map((invoice) => (
                      <tr key={invoice.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {invoice.invoice_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(invoice.period_start)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(invoice.total, invoice.currency)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-${getStatusColor(invoice.status)}-100 text-${getStatusColor(invoice.status)}-800`}>
                            {t(`billing.invoices.statuses.${invoice.status}`)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {invoice.invoice_pdf_url && (
                            <a
                              href={invoice.invoice_pdf_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 flex items-center"
                            >
                              <Download className="h-4 w-4 mr-1" />
                              {t('billing.invoices.download')}
                            </a>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-600 text-center py-4">
                {t('billing.invoices.none')}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Cancel Subscription Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <div className="flex items-center mb-4">
              <AlertCircle className="h-6 w-6 text-red-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">
                {t('billing.cancelModal.title')}
              </h3>
            </div>
            
            <p className="text-gray-600 mb-6">
              {t('billing.cancelModal.message')}
            </p>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowCancelModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleCancelSubscription}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                {t('billing.cancelModal.confirm')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BillingDashboard;