import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, Handshake, Building, Shield, Award, CheckCircle, Globe, TrendingUp } from 'lucide-react';

interface Partner {
  id: number;
  name: string;
  logo: string;
  description: string;
  type: string;
}

export const Partners: React.FC = () => {
  const { t } = useTranslation();

  const partners: Partner[] = [
    {
      id: 1,
      name: 'TechSecure GmbH',
      logo: '/partners/techsecure.png',
      description: t('partners.list.techsecure'),
      type: 'technology'
    },
    {
      id: 2,
      name: 'CloudGuard Solutions',
      logo: '/partners/cloudguard.png',
      description: t('partners.list.cloudguard'),
      type: 'technology'
    },
    {
      id: 3,
      name: 'ComplianceFirst AG',
      logo: '/partners/compliance.png',
      description: t('partners.list.compliance'),
      type: 'consulting'
    },
    {
      id: 4,
      name: 'SecureNet Partners',
      logo: '/partners/securenet.png',
      description: t('partners.list.securenet'),
      type: 'reseller'
    }
  ];

  const partnerBenefits = [
    { icon: TrendingUp, title: t('partners.benefits.growth'), description: t('partners.benefits.growthDesc') },
    { icon: Shield, title: t('partners.benefits.support'), description: t('partners.benefits.supportDesc') },
    { icon: Award, title: t('partners.benefits.certification'), description: t('partners.benefits.certificationDesc') },
    { icon: Globe, title: t('partners.benefits.network'), description: t('partners.benefits.networkDesc') }
  ];

  const partnerTypes = [
    {
      title: t('partners.types.technology.title'),
      description: t('partners.types.technology.description'),
      benefits: [
        t('partners.types.technology.benefit1'),
        t('partners.types.technology.benefit2'),
        t('partners.types.technology.benefit3')
      ]
    },
    {
      title: t('partners.types.reseller.title'),
      description: t('partners.types.reseller.description'),
      benefits: [
        t('partners.types.reseller.benefit1'),
        t('partners.types.reseller.benefit2'),
        t('partners.types.reseller.benefit3')
      ]
    },
    {
      title: t('partners.types.consulting.title'),
      description: t('partners.types.consulting.description'),
      benefits: [
        t('partners.types.consulting.benefit1'),
        t('partners.types.consulting.benefit2'),
        t('partners.types.consulting.benefit3')
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('common.back')}
        </Link>

        {/* Hero Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4 flex items-center">
            <Handshake className="w-10 h-10 mr-3 text-blue-600" />
            {t('partners.title')}
          </h1>
          <p className="text-xl text-gray-600">
            {t('partners.subtitle')}
          </p>
        </div>

        {/* Current Partners */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('partners.current')}</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {partners.map((partner) => (
              <div key={partner.id} className="text-center p-6 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                <div className="w-24 h-24 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <Building className="w-12 h-12 text-gray-400" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{partner.name}</h3>
                <p className="text-sm text-gray-600">{partner.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Partner Types */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('partners.types.title')}</h2>
          <div className="space-y-8">
            {partnerTypes.map((type, index) => (
              <div key={index} className="border-l-4 border-blue-600 pl-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{type.title}</h3>
                <p className="text-gray-700 mb-4">{type.description}</p>
                <ul className="space-y-2">
                  {type.benefits.map((benefit, idx) => (
                    <li key={idx} className="flex items-start">
                      <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Partner Benefits */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('partners.benefits.title')}</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {partnerBenefits.map((benefit, index) => (
              <div key={index} className="text-center">
                <benefit.icon className="w-12 h-12 text-blue-600 mx-auto mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">{benefit.title}</h3>
                <p className="text-gray-600 text-sm">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Partner Requirements */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('partners.requirements.title')}</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('partners.requirements.general')}</h3>
              <ul className="space-y-2">
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('partners.requirements.req1')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('partners.requirements.req2')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('partners.requirements.req3')}</span>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('partners.requirements.technical')}</h3>
              <ul className="space-y-2">
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('partners.requirements.tech1')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('partners.requirements.tech2')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('partners.requirements.tech3')}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="bg-blue-600 rounded-lg shadow-md p-8 text-white text-center">
          <h2 className="text-2xl font-bold mb-4">{t('partners.cta.title')}</h2>
          <p className="mb-6">{t('partners.cta.subtitle')}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="mailto:partners@bootstrap-academy.com"
              className="inline-flex items-center justify-center px-6 py-3 bg-white text-blue-600 font-medium rounded-md hover:bg-gray-100 transition-colors"
            >
              {t('partners.cta.apply')}
            </a>
            <Link
              to="/contact"
              className="inline-flex items-center justify-center px-6 py-3 border-2 border-white text-white font-medium rounded-md hover:bg-white hover:text-blue-600 transition-colors"
            >
              {t('partners.cta.contact')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};