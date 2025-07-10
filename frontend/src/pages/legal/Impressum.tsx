import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, Building2, Mail, Phone, Globe } from 'lucide-react';

export const Impressum: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('common.back')}
        </Link>

        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">{t('legal.impressum.title')}</h1>

          <div className="space-y-8">
            {/* Company Information */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <Building2 className="w-5 h-5 mr-2 text-blue-600" />
                {t('legal.impressum.company')}
              </h2>
              <div className="text-gray-700 space-y-2">
                <p>Bootstrap Academy GmbH</p>
                <p>Musterstraße 123</p>
                <p>10115 Berlin</p>
                <p>Deutschland</p>
              </div>
            </section>

            {/* Contact */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.impressum.contact')}</h2>
              <div className="text-gray-700 space-y-2">
                <p className="flex items-center">
                  <Phone className="w-4 h-4 mr-2 text-gray-500" />
                  +49 (0) 30 123456789
                </p>
                <p className="flex items-center">
                  <Mail className="w-4 h-4 mr-2 text-gray-500" />
                  info@bootstrap-academy.com
                </p>
                <p className="flex items-center">
                  <Globe className="w-4 h-4 mr-2 text-gray-500" />
                  www.bootstrap-academy.com
                </p>
              </div>
            </section>

            {/* Legal Representatives */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.impressum.representatives')}</h2>
              <div className="text-gray-700">
                <p>{t('legal.impressum.ceo')}: Dr. Max Mustermann</p>
                <p>{t('legal.impressum.cto')}: Sarah Schmidt</p>
              </div>
            </section>

            {/* Registration */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.impressum.registration')}</h2>
              <div className="text-gray-700 space-y-2">
                <p>{t('legal.impressum.court')}: Amtsgericht Berlin-Charlottenburg</p>
                <p>{t('legal.impressum.registerNumber')}: HRB 123456 B</p>
                <p>{t('legal.impressum.vatId')}: DE123456789</p>
              </div>
            </section>

            {/* Responsible for Content */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.impressum.contentResponsible')}</h2>
              <div className="text-gray-700">
                <p>Dr. Max Mustermann</p>
                <p>Bootstrap Academy GmbH</p>
                <p>Musterstraße 123</p>
                <p>10115 Berlin</p>
              </div>
            </section>

            {/* Dispute Resolution */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.impressum.disputeResolution')}</h2>
              <div className="text-gray-700 space-y-4">
                <p>{t('legal.impressum.disputeText1')}</p>
                <p>{t('legal.impressum.disputeText2')}</p>
                <p>
                  <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    https://ec.europa.eu/consumers/odr
                  </a>
                </p>
              </div>
            </section>

            {/* Liability Disclaimer */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.impressum.liability')}</h2>
              <div className="text-gray-700 space-y-4">
                <p>{t('legal.impressum.liabilityText')}</p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};