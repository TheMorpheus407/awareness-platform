import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, ArrowLeft, Cookie, Check } from 'lucide-react';
import { LanguageSwitcher } from '../../components/Common';

const CookieSettings = () => {
  const { t } = useTranslation();
  const [preferences, setPreferences] = useState({
    necessary: true,
    analytics: false,
    marketing: false,
    functional: true,
  });

  const handleSave = () => {
    // Save cookie preferences to localStorage or cookie
    localStorage.setItem('cookiePreferences', JSON.stringify(preferences));
    alert(t('cookieSettings.saved', 'Cookie-Einstellungen wurden gespeichert'));
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-sm z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link to="/" className="flex items-center space-x-2">
              <Shield className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">Bootstrap Academy</span>
            </Link>
            <div className="flex items-center space-x-6">
              <LanguageSwitcher />
              <Link to="/" className="text-gray-600 hover:text-gray-900 transition-colors">
                {t('common.backToHome')}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-8">
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('common.back')}
          </Link>

          <div className="flex items-center mb-8">
            <Cookie className="w-12 h-12 text-blue-600 mr-4" />
            <h1 className="text-4xl font-bold text-gray-900">{t('cookieSettings.title', 'Cookie-Einstellungen')}</h1>
          </div>

          <div className="prose prose-lg max-w-none text-gray-700 mb-8">
            <p>
              {t('cookieSettings.intro', 
                'Wir verwenden Cookies, um Ihre Erfahrung auf unserer Website zu verbessern. Sie können selbst entscheiden, welche Kategorien Sie zulassen möchten. Bitte beachten Sie, dass aufgrund Ihrer Einstellungen möglicherweise nicht alle Funktionen der Website verfügbar sind.'
              )}
            </p>
          </div>

          <div className="space-y-6">
            {/* Necessary Cookies */}
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {t('cookieSettings.necessary.title', 'Notwendige Cookies')}
                  </h3>
                  <p className="text-gray-600">
                    {t('cookieSettings.necessary.description', 
                      'Diese Cookies sind für die Grundfunktionen der Website erforderlich. Sie ermöglichen die Navigation auf der Website und die Nutzung ihrer Funktionen.'
                    )}
                  </p>
                  <div className="mt-3 text-sm text-gray-500">
                    <p className="font-medium">{t('cookieSettings.examples', 'Beispiele:')}</p>
                    <ul className="list-disc list-inside mt-1">
                      <li>Session-Cookies</li>
                      <li>Sicherheits-Cookies</li>
                      <li>Spracheinstellungen</li>
                    </ul>
                  </div>
                </div>
                <div className="ml-4">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={preferences.necessary}
                      disabled
                      className="sr-only"
                    />
                    <div className="w-14 h-8 bg-blue-600 rounded-full"></div>
                    <div className="absolute top-1 left-1 w-6 h-6 bg-white rounded-full shadow transform translate-x-6"></div>
                  </div>
                  <span className="text-xs text-gray-500 mt-1 block">
                    {t('cookieSettings.alwaysActive', 'Immer aktiv')}
                  </span>
                </div>
              </div>
            </div>

            {/* Analytics Cookies */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {t('cookieSettings.analytics.title', 'Analyse-Cookies')}
                  </h3>
                  <p className="text-gray-600">
                    {t('cookieSettings.analytics.description', 
                      'Diese Cookies helfen uns zu verstehen, wie Besucher mit unserer Website interagieren, indem Informationen anonym gesammelt und gemeldet werden.'
                    )}
                  </p>
                  <div className="mt-3 text-sm text-gray-500">
                    <p className="font-medium">{t('cookieSettings.examples', 'Beispiele:')}</p>
                    <ul className="list-disc list-inside mt-1">
                      <li>Matomo Analytics</li>
                      <li>Besucherzähler</li>
                      <li>Seitenaufrufe</li>
                    </ul>
                  </div>
                </div>
                <div className="ml-4">
                  <button
                    onClick={() => setPreferences({ ...preferences, analytics: !preferences.analytics })}
                    className="relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    style={{ backgroundColor: preferences.analytics ? '#2563eb' : '#e5e7eb' }}
                  >
                    <span
                      className={`inline-block h-6 w-6 transform rounded-full bg-white shadow transition-transform ${
                        preferences.analytics ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>

            {/* Marketing Cookies */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {t('cookieSettings.marketing.title', 'Marketing-Cookies')}
                  </h3>
                  <p className="text-gray-600">
                    {t('cookieSettings.marketing.description', 
                      'Diese Cookies werden verwendet, um Werbung zu liefern, die für Sie und Ihre Interessen relevanter ist.'
                    )}
                  </p>
                  <div className="mt-3 text-sm text-gray-500">
                    <p className="font-medium">{t('cookieSettings.examples', 'Beispiele:')}</p>
                    <ul className="list-disc list-inside mt-1">
                      <li>Retargeting-Cookies</li>
                      <li>Social Media Tracking</li>
                      <li>Werbenetzwerke</li>
                    </ul>
                  </div>
                </div>
                <div className="ml-4">
                  <button
                    onClick={() => setPreferences({ ...preferences, marketing: !preferences.marketing })}
                    className="relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    style={{ backgroundColor: preferences.marketing ? '#2563eb' : '#e5e7eb' }}
                  >
                    <span
                      className={`inline-block h-6 w-6 transform rounded-full bg-white shadow transition-transform ${
                        preferences.marketing ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>

            {/* Functional Cookies */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {t('cookieSettings.functional.title', 'Funktionale Cookies')}
                  </h3>
                  <p className="text-gray-600">
                    {t('cookieSettings.functional.description', 
                      'Diese Cookies ermöglichen der Website, erweiterte Funktionen und Personalisierung zur Verfügung zu stellen.'
                    )}
                  </p>
                  <div className="mt-3 text-sm text-gray-500">
                    <p className="font-medium">{t('cookieSettings.examples', 'Beispiele:')}</p>
                    <ul className="list-disc list-inside mt-1">
                      <li>Benutzereinstellungen</li>
                      <li>Theme-Präferenzen</li>
                      <li>Chat-Widgets</li>
                    </ul>
                  </div>
                </div>
                <div className="ml-4">
                  <button
                    onClick={() => setPreferences({ ...preferences, functional: !preferences.functional })}
                    className="relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    style={{ backgroundColor: preferences.functional ? '#2563eb' : '#e5e7eb' }}
                  >
                    <span
                      className={`inline-block h-6 w-6 transform rounded-full bg-white shadow transition-transform ${
                        preferences.functional ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-end">
            <button
              onClick={() => setPreferences({ necessary: true, analytics: false, marketing: false, functional: false })}
              className="px-6 py-3 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
            >
              {t('cookieSettings.rejectAll', 'Alle ablehnen')}
            </button>
            <button
              onClick={() => setPreferences({ necessary: true, analytics: true, marketing: true, functional: true })}
              className="px-6 py-3 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
            >
              {t('cookieSettings.acceptAll', 'Alle akzeptieren')}
            </button>
            <button
              onClick={handleSave}
              className="px-6 py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors flex items-center"
            >
              <Check className="w-5 h-5 mr-2" />
              {t('cookieSettings.savePreferences', 'Einstellungen speichern')}
            </button>
          </div>

          {/* Additional Info */}
          <div className="mt-12 p-6 bg-blue-50 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {t('cookieSettings.moreInfo.title', 'Weitere Informationen')}
            </h3>
            <p className="text-gray-700 mb-4">
              {t('cookieSettings.moreInfo.description', 
                'Detaillierte Informationen zu den von uns verwendeten Cookies und deren Zweck finden Sie in unserer Datenschutzerklärung.'
              )}
            </p>
            <Link to="/privacy" className="text-blue-600 hover:text-blue-700 font-medium">
              {t('cookieSettings.moreInfo.link', 'Zur Datenschutzerklärung')} →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CookieSettings;