import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, FileText, Scale, Shield, AlertTriangle } from 'lucide-react';

export const Terms: React.FC = () => {
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
            <FileText className="w-8 h-8 mr-3 text-blue-600" />
            {t('legal.terms.title')}
          </h1>

          <div className="prose prose-lg max-w-none space-y-8">
            {/* Scope */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.terms.scope')}</h2>
              <p className="text-gray-700">
                {t('legal.terms.scopeText')}
              </p>
            </section>

            {/* Services */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <Shield className="w-5 h-5 mr-2 text-blue-600" />
                {t('legal.terms.services')}
              </h2>
              <div className="text-gray-700 space-y-4">
                <p>{t('legal.terms.servicesIntro')}</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>{t('legal.terms.services.training')}</li>
                  <li>{t('legal.terms.services.phishing')}</li>
                  <li>{t('legal.terms.services.analytics')}</li>
                  <li>{t('legal.terms.services.certificates')}</li>
                  <li>{t('legal.terms.services.support')}</li>
                </ul>
              </div>
            </section>

            {/* Account Registration */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.terms.registration')}</h2>
              <div className="text-gray-700 space-y-4">
                <p>{t('legal.terms.registrationText')}</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>{t('legal.terms.registration.accurate')}</li>
                  <li>{t('legal.terms.registration.confidential')}</li>
                  <li>{t('legal.terms.registration.responsible')}</li>
                  <li>{t('legal.terms.registration.notify')}</li>
                </ul>
              </div>
            </section>

            {/* User Obligations */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <Scale className="w-5 h-5 mr-2 text-blue-600" />
                {t('legal.terms.obligations')}
              </h2>
              <div className="text-gray-700 space-y-4">
                <p>{t('legal.terms.obligationsIntro')}</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>{t('legal.terms.obligations.lawful')}</li>
                  <li>{t('legal.terms.obligations.noMisuse')}</li>
                  <li>{t('legal.terms.obligations.noInterference')}</li>
                  <li>{t('legal.terms.obligations.noReverse')}</li>
                  <li>{t('legal.terms.obligations.respect')}</li>
                </ul>
              </div>
            </section>

            {/* Payment Terms */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.terms.payment')}</h2>
              <div className="text-gray-700 space-y-4">
                <p>{t('legal.terms.paymentText')}</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>{t('legal.terms.payment.subscription')}</li>
                  <li>{t('legal.terms.payment.automatic')}</li>
                  <li>{t('legal.terms.payment.failure')}</li>
                  <li>{t('legal.terms.payment.refunds')}</li>
                </ul>
              </div>
            </section>

            {/* Intellectual Property */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.terms.intellectual')}</h2>
              <p className="text-gray-700">
                {t('legal.terms.intellectualText')}
              </p>
            </section>

            {/* Limitation of Liability */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2 text-yellow-600" />
                {t('legal.terms.liability')}
              </h2>
              <div className="text-gray-700 space-y-4">
                <p>{t('legal.terms.liabilityText')}</p>
                <p className="font-semibold">{t('legal.terms.liabilityExclusion')}</p>
              </div>
            </section>

            {/* Termination */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.terms.termination')}</h2>
              <p className="text-gray-700">
                {t('legal.terms.terminationText')}
              </p>
            </section>

            {/* Governing Law */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.terms.governing')}</h2>
              <p className="text-gray-700">
                {t('legal.terms.governingText')}
              </p>
            </section>

            {/* Contact */}
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('legal.terms.contact')}</h2>
              <div className="text-gray-700 space-y-2">
                <p>{t('legal.terms.contactText')}</p>
                <p>Email: legal@bootstrap-academy.com</p>
                <p>Tel: +49 (0) 30 123456789</p>
              </div>
            </section>

            {/* Last Updated */}
            <section className="border-t pt-6">
              <p className="text-sm text-gray-600">
                {t('legal.terms.lastUpdated')}: {new Date().toLocaleDateString()}
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};