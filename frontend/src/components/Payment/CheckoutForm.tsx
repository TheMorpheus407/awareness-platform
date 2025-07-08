import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  PaymentElement,
  Elements,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { paymentService } from '../../services/paymentService';
import { LoadingSpinner, ErrorMessage } from '../Common';
import { useAuthStore } from '../../store/authStore';

// Load Stripe outside of component to avoid recreating on every render
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || '');

interface CheckoutFormProps {
  priceId: string;
  clientSecret: string;
}

const CheckoutFormContent: React.FC<CheckoutFormProps> = ({ priceId, clientSecret }) => {
  const { t } = useTranslation();
  const stripe = useStripe();
  const elements = useElements();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Confirm the setup intent
      const { error: confirmError } = await stripe.confirmSetup({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/payment/success`,
        },
        redirect: 'if_required',
      });

      if (confirmError) {
        setError(confirmError.message || t('payment.error.generic'));
      } else {
        // If no redirect was required, create the subscription
        const paymentMethodId = await getPaymentMethodId();
        if (paymentMethodId) {
          await paymentService.createSubscription({
            price_id: priceId,
            payment_method_id: paymentMethodId,
          });
          navigate('/billing');
        }
      }
    } catch (err: any) {
      setError(err.message || t('payment.error.generic'));
    } finally {
      setIsProcessing(false);
    }
  };

  const getPaymentMethodId = async (): Promise<string | null> => {
    if (!stripe || !elements) return null;

    const { error, setupIntent } = await stripe.retrieveSetupIntent(clientSecret);
    if (error || !setupIntent) return null;

    return setupIntent.payment_method as string;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          {t('payment.checkout.paymentDetails')}
        </h3>
        
        <PaymentElement
          options={{
            layout: 'tabs',
          }}
        />
      </div>

      {error && <ErrorMessage message={error} />}

      <div className="flex justify-between items-center">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="text-gray-600 hover:text-gray-900"
        >
          {t('common.back')}
        </button>

        <button
          type="submit"
          disabled={!stripe || isProcessing}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? (
            <span className="flex items-center">
              <LoadingSpinner size="small" className="mr-2" />
              {t('payment.checkout.processing')}
            </span>
          ) : (
            t('payment.checkout.subscribe')
          )}
        </button>
      </div>
    </form>
  );
};

const CheckoutForm: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const priceId = searchParams.get('price_id');

  useEffect(() => {
    if (!priceId) {
      navigate('/pricing');
      return;
    }

    if (!user) {
      navigate('/login');
      return;
    }

    createSetupIntent();
  }, [priceId, user, navigate]);

  const createSetupIntent = async () => {
    try {
      const { client_secret } = await paymentService.createSetupIntent();
      setClientSecret(client_secret);
    } catch (err: any) {
      setError(err.message || t('payment.error.setupIntent'));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-8">
        <ErrorMessage message={error} />
        <button
          onClick={() => navigate('/pricing')}
          className="mt-4 text-blue-600 hover:text-blue-800"
        >
          {t('payment.checkout.backToPricing')}
        </button>
      </div>
    );
  }

  if (!clientSecret || !priceId) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-extrabold text-gray-900">
            {t('payment.checkout.title')}
          </h2>
          <p className="mt-2 text-gray-600">
            {t('payment.checkout.subtitle')}
          </p>
        </div>

        <Elements
          stripe={stripePromise}
          options={{
            clientSecret,
            appearance: {
              theme: 'stripe',
              variables: {
                colorPrimary: '#1976d2',
              },
            },
          }}
        >
          <CheckoutFormContent priceId={priceId} clientSecret={clientSecret} />
        </Elements>
      </div>
    </div>
  );
};

export default CheckoutForm;