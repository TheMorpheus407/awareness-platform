import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Check, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { paymentService } from '../../services/paymentService';
import { LoadingSpinner } from '../Common';

interface PricingTier {
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

const PricingPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [pricing, setPricing] = useState<PricingTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedInterval, setSelectedInterval] = useState<'monthly' | 'yearly'>('monthly');

  useEffect(() => {
    loadPricing();
  }, []);

  const loadPricing = async () => {
    try {
      const prices = await paymentService.getPricing();
      setPricing(prices);
    } catch (error) {
      console.error('Failed to load pricing:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredPricing = () => {
    return pricing.filter(price => price.interval === selectedInterval);
  };

  const formatPrice = (amount: number, currency: string) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const getTierColor = (tier: string) => {
    const colors: Record<string, string> = {
      basic: 'blue',
      starter: 'green',
      premium: 'purple',
      professional: 'orange',
      enterprise: 'red',
    };
    return colors[tier.toLowerCase()] || 'gray';
  };

  const handleSelectPlan = (priceId: string) => {
    navigate(`/checkout?price_id=${priceId}`);
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  const filteredPricing = getFilteredPricing();

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            {t('pricing.title')}
          </h2>
          <p className="mt-4 text-xl text-gray-600">
            {t('pricing.subtitle')}
          </p>
        </div>

        {/* Interval selector */}
        <div className="mt-8 flex justify-center">
          <div className="relative bg-gray-100 p-1 rounded-lg flex">
            <button
              onClick={() => setSelectedInterval('monthly')}
              className={`${
                selectedInterval === 'monthly'
                  ? 'bg-white shadow-sm text-gray-900'
                  : 'text-gray-500'
              } relative py-2 px-6 rounded-md font-medium transition-all`}
            >
              {t('pricing.monthly')}
            </button>
            <button
              onClick={() => setSelectedInterval('yearly')}
              className={`${
                selectedInterval === 'yearly'
                  ? 'bg-white shadow-sm text-gray-900'
                  : 'text-gray-500'
              } relative py-2 px-6 rounded-md font-medium transition-all`}
            >
              {t('pricing.yearly')}
              <span className="ml-2 text-green-600 text-sm">
                {t('pricing.yearlySave')}
              </span>
            </button>
          </div>
        </div>

        {/* Pricing cards */}
        <div className="mt-12 grid gap-8 lg:grid-cols-3 lg:gap-x-8">
          {filteredPricing.map((tier) => {
            const color = getTierColor(tier.tier);
            const isPopular = tier.tier.toLowerCase() === 'premium';

            return (
              <div
                key={tier.price_id}
                className={`relative flex flex-col rounded-2xl shadow-xl ${
                  isPopular ? 'ring-2 ring-purple-600' : ''
                }`}
              >
                {isPopular && (
                  <div className="absolute -top-5 left-0 right-0 mx-auto w-32">
                    <div className="rounded-full bg-purple-600 px-3 py-1 text-sm font-medium text-white text-center">
                      {t('pricing.popular')}
                    </div>
                  </div>
                )}

                <div className="p-8">
                  <h3 className={`text-2xl font-semibold text-${color}-600`}>
                    {tier.product_name}
                  </h3>
                  
                  <div className="mt-4 flex items-baseline">
                    <span className="text-5xl font-extrabold tracking-tight text-gray-900">
                      {formatPrice(tier.amount, tier.currency)}
                    </span>
                    <span className="ml-1 text-xl font-semibold text-gray-500">
                      /{t(`pricing.interval.${tier.interval}`)}
                    </span>
                  </div>

                  <ul className="mt-8 space-y-4">
                    {tier.features.map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                        <span className="ml-3 text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => handleSelectPlan(tier.price_id)}
                    className={`mt-8 w-full py-3 px-6 border border-transparent rounded-md text-center font-medium text-white bg-${color}-600 hover:bg-${color}-700 transition-colors`}
                  >
                    {t('pricing.selectPlan')}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Enterprise contact */}
        <div className="mt-12 text-center">
          <p className="text-lg text-gray-600">
            {t('pricing.enterprise.need')}{' '}
            <a
              href={`mailto:${t('pricing.enterprise.contactEmail')}`}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              {t('pricing.enterprise.contact')}
            </a>
          </p>
        </div>

        {/* Features comparison */}
        <div className="mt-16">
          <h3 className="text-2xl font-bold text-gray-900 text-center mb-8">
            {t('pricing.comparison.title')}
          </h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('pricing.comparison.feature')}
                  </th>
                  {filteredPricing.map((tier) => (
                    <th
                      key={tier.price_id}
                      className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {tier.product_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {/* Add feature comparison rows here */}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;