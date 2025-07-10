import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, Shield, Lock, Eye, Database, UserCheck, AlertCircle } from 'lucide-react';

export const Privacy: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('common.back')}
        </Link>

        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8 flex items-center">
            <Shield className="w-8 h-8 mr-3 text-blue-600" />
            {t('legal.privacy.title')}
          </h1>

          <div className="prose prose-lg max-w-none space-y-8">
            {/* Introduction */}
            <section>
              <p className="text-gray-700 leading-relaxed">
                {t('legal.privacy.introduction')}
              </p>
            </section>

            {/* Data Controller */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <UserCheck className="w-5 h-5 mr-2 text-blue-600" />
                {t('legal.privacy.dataController')}
              </h2>
              <div className="text-gray-700 space-y-2">
                <p>Bootstrap Academy GmbH</p>
                <p>Musterstraße 123, 10115 Berlin</p>
                <p>Email: privacy@bootstrap-academy.com</p>
                <p>Tel: +49 (0) 30 123456789</p>
              </div>
            </section>

            {/* Data Collection */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <Database className="w-5 h-5 mr-2 text-blue-600" />
                {t('legal.privacy.dataCollection')}
              </h2>
              <div className="text-gray-700 space-y-4">
                <h3 className="font-semibold">{t('legal.privacy.personalData')}</h3>
                <ul className="list-disc pl-6 space-y-2">
                  <li>{t('legal.privacy.data.name')}</li>
                  <li>{t('legal.privacy.data.email')}</li>
                  <li>{t('legal.privacy.data.company')}</li>
                  <li>{t('legal.privacy.data.usage')}</li>
                  <li>{t('legal.privacy.data.training')}</li>
                </ul>
              </div>
            </section>

            {/* Purpose of Processing */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <Eye className="w-5 h-5 mr-2 text-blue-600" />
                {t('legal.privacy.purpose')}
              </h2>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>{t('legal.privacy.purpose.service')}</li>
                <li>{t('legal.privacy.purpose.security')}</li>
                <li>{t('legal.privacy.purpose.communication')}</li>
                <li>{t('legal.privacy.purpose.improvement')}</li>
                <li>{t('legal.privacy.purpose.compliance')}</li>
              </ul>
            </section>

            {/* Legal Basis */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.privacy.legalBasis')}</h2>
              <div className="text-gray-700 space-y-2">
                <p>{t('legal.privacy.legalBasis.gdpr')}</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>{t('legal.privacy.legalBasis.contract')}</li>
                  <li>{t('legal.privacy.legalBasis.legal')}</li>
                  <li>{t('legal.privacy.legalBasis.legitimate')}</li>
                  <li>{t('legal.privacy.legalBasis.consent')}</li>
                </ul>
              </div>
            </section>

            {/* Data Security */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <Lock className="w-5 h-5 mr-2 text-blue-600" />
                {t('legal.privacy.security')}
              </h2>
              <p className="text-gray-700">
                {t('legal.privacy.securityText')}
              </p>
            </section>

            {/* Your Rights */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <AlertCircle className="w-5 h-5 mr-2 text-blue-600" />
                {t('legal.privacy.rights')}
              </h2>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>{t('legal.privacy.rights.access')}</li>
                <li>{t('legal.privacy.rights.rectification')}</li>
                <li>{t('legal.privacy.rights.erasure')}</li>
                <li>{t('legal.privacy.rights.restriction')}</li>
                <li>{t('legal.privacy.rights.portability')}</li>
                <li>{t('legal.privacy.rights.object')}</li>
                <li>{t('legal.privacy.rights.withdraw')}</li>
              </ul>
            </section>

            {/* Contact */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.privacy.contact')}</h2>
              <p className="text-gray-700">
                {t('legal.privacy.contactText')}
              </p>
              <p className="text-gray-700 mt-2">
                Email: privacy@bootstrap-academy.com
              </p>
            </section>

            {/* Last Updated */}
            <section className="border-t pt-6">
              <p className="text-sm text-gray-600">
                {t('legal.privacy.lastUpdated')}: {new Date().toLocaleDateString()}
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};