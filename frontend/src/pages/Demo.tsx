import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, ArrowLeft, Play, CheckCircle, Calendar, Clock, Users, ChevronRight } from 'lucide-react';
import { LanguageSwitcher } from '../components/Common';

const Demo = () => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    company: '',
    phone: '',
    employees: '',
    message: '',
    preferredDate: '',
    preferredTime: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle demo request submission
    console.log('Demo request:', formData);
    alert(t('demo.form.success', 'Vielen Dank! Wir werden uns innerhalb von 24 Stunden bei Ihnen melden.'));
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const demoFeatures = [
    'Live-Phishing-Simulation durchführen',
    'Dashboard und Reporting-Funktionen erkunden',
    'Schulungsmodule testen',
    'Compliance-Features kennenlernen',
    'Integration in bestehende Systeme besprechen',
    'Individuelle Anpassungsmöglichkeiten',
  ];

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

      {/* Hero Section */}
      <div className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto">
          <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-8">
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('common.back')}
          </Link>

          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              {t('demo.title', 'Erleben Sie Bootstrap Academy live')}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {t('demo.subtitle', 
                'Überzeugen Sie sich in einer persönlichen Demo von den Möglichkeiten unserer Plattform.'
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Demo Form */}
            <div>
              <div className="bg-white rounded-lg shadow-lg p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  {t('demo.form.title', 'Demo anfordern')}
                </h2>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('demo.form.firstName', 'Vorname')} *
                      </label>
                      <input
                        type="text"
                        id="firstName"
                        name="firstName"
                        required
                        value={formData.firstName}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('demo.form.lastName', 'Nachname')} *
                      </label>
                      <input
                        type="text"
                        id="lastName"
                        name="lastName"
                        required
                        value={formData.lastName}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('demo.form.email', 'Geschäftliche E-Mail')} *
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      required
                      value={formData.email}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('demo.form.company', 'Unternehmen')} *
                    </label>
                    <input
                      type="text"
                      id="company"
                      name="company"
                      required
                      value={formData.company}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('demo.form.phone', 'Telefon')}
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label htmlFor="employees" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('demo.form.employees', 'Anzahl Mitarbeiter')} *
                    </label>
                    <select
                      id="employees"
                      name="employees"
                      required
                      value={formData.employees}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">{t('demo.form.selectEmployees', 'Bitte wählen')}</option>
                      <option value="1-50">1-50</option>
                      <option value="51-200">51-200</option>
                      <option value="201-500">201-500</option>
                      <option value="501-1000">501-1000</option>
                      <option value="1000+">1000+</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="preferredDate" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('demo.form.preferredDate', 'Wunschtermin')}
                      </label>
                      <input
                        type="date"
                        id="preferredDate"
                        name="preferredDate"
                        value={formData.preferredDate}
                        onChange={handleChange}
                        min={new Date().toISOString().split('T')[0]}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label htmlFor="preferredTime" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('demo.form.preferredTime', 'Bevorzugte Uhrzeit')}
                      </label>
                      <select
                        id="preferredTime"
                        name="preferredTime"
                        value={formData.preferredTime}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="">{t('demo.form.selectTime', 'Bitte wählen')}</option>
                        <option value="morning">9:00 - 12:00</option>
                        <option value="afternoon">12:00 - 15:00</option>
                        <option value="late-afternoon">15:00 - 18:00</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('demo.form.message', 'Ihre Nachricht')}
                    </label>
                    <textarea
                      id="message"
                      name="message"
                      rows={4}
                      value={formData.message}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder={t('demo.form.messagePlaceholder', 'Gibt es spezielle Themen, die Sie interessieren?')}
                    />
                  </div>
                  <div>
                    <button
                      type="submit"
                      className="w-full px-8 py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center"
                    >
                      <Calendar className="w-5 h-5 mr-2" />
                      {t('demo.form.submit', 'Demo vereinbaren')}
                    </button>
                  </div>
                </form>
              </div>
            </div>

            {/* Demo Info */}
            <div className="space-y-8">
              {/* What to expect */}
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  {t('demo.expect.title', 'Was Sie erwartet')}
                </h2>
                <div className="bg-blue-50 rounded-lg p-6">
                  <div className="flex items-start mb-4">
                    <Play className="w-6 h-6 text-blue-600 mt-1 mr-3" />
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">
                        {t('demo.expect.duration', '30-45 Minuten Live-Demo')}
                      </h3>
                      <p className="text-gray-600">
                        {t('demo.expect.durationDesc', 
                          'Unsere Experten zeigen Ihnen die wichtigsten Funktionen und beantworten Ihre Fragen.'
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start mb-4">
                    <Users className="w-6 h-6 text-blue-600 mt-1 mr-3" />
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">
                        {t('demo.expect.personalized', 'Auf Sie zugeschnitten')}
                      </h3>
                      <p className="text-gray-600">
                        {t('demo.expect.personalizedDesc', 
                          'Wir passen die Demo an Ihre Branche und spezifischen Anforderungen an.'
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <Clock className="w-6 h-6 text-blue-600 mt-1 mr-3" />
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">
                        {t('demo.expect.flexible', 'Flexible Terminvereinbarung')}
                      </h3>
                      <p className="text-gray-600">
                        {t('demo.expect.flexibleDesc', 
                          'Wir richten uns nach Ihrem Zeitplan - auch außerhalb der regulären Geschäftszeiten.'
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Demo topics */}
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  {t('demo.topics.title', 'Das zeigen wir Ihnen')}
                </h3>
                <ul className="space-y-3">
                  {demoFeatures.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <CheckCircle className="w-5 h-5 text-green-500 mr-3 mt-0.5" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Testimonial */}
              <div className="bg-gray-50 rounded-lg p-6">
                <p className="text-gray-700 italic mb-4">
                  "Die Demo hat uns überzeugt! Besonders beeindruckt hat uns die einfache Bedienung und die 
                  detaillierten Analysen. Innerhalb einer Woche waren wir startklar."
                </p>
                <div>
                  <p className="font-semibold text-gray-900">Michael Schmidt</p>
                  <p className="text-sm text-gray-600">IT-Leiter, TechCorp GmbH</p>
                </div>
              </div>

              {/* No commitment */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 mb-2">
                  {t('demo.noCommitment.title', 'Unverbindlich & kostenlos')}
                </h3>
                <p className="text-gray-700">
                  {t('demo.noCommitment.description', 
                    'Die Demo ist völlig unverbindlich. Sie gehen keine Verpflichtungen ein und können sich in Ruhe entscheiden.'
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('demo.faq.title', 'Häufige Fragen zur Demo')}
          </h2>
          <div className="space-y-8">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {t('demo.faq.q1', 'Muss ich mich auf die Demo vorbereiten?')}
              </h3>
              <p className="text-gray-600">
                {t('demo.faq.a1', 
                  'Nein, eine spezielle Vorbereitung ist nicht notwendig. Es ist hilfreich, wenn Sie bereits eine Vorstellung von Ihren Anforderungen haben, aber wir führen Sie durch alle wichtigen Punkte.'
                )}
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {t('demo.faq.q2', 'Können mehrere Personen an der Demo teilnehmen?')}
              </h3>
              <p className="text-gray-600">
                {t('demo.faq.a2', 
                  'Selbstverständlich! Wir empfehlen sogar, dass alle Entscheidungsträger teilnehmen. Teilen Sie uns einfach die Anzahl der Teilnehmer mit.'
                )}
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {t('demo.faq.q3', 'Erhalte ich nach der Demo einen Testzugang?')}
              </h3>
              <p className="text-gray-600">
                {t('demo.faq.a3', 
                  'Ja, auf Wunsch richten wir Ihnen gerne einen kostenlosen Testzugang für 14 Tage ein, damit Sie die Plattform ausgiebig testen können.'
                )}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-blue-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            {t('demo.cta.title', 'Noch Fragen?')}
          </h2>
          <p className="text-lg text-blue-100 mb-8">
            {t('demo.cta.subtitle', 
              'Unser Team steht Ihnen gerne zur Verfügung.'
            )}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/contact" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-blue-600 bg-white rounded-lg hover:bg-gray-100 transition-colors"
            >
              {t('demo.cta.contact', 'Kontakt aufnehmen')}
            </Link>
            <a 
              href="tel:+4930123456100" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white border-2 border-white rounded-lg hover:bg-white/10 transition-colors"
            >
              {t('demo.cta.call', 'Direkt anrufen')}
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Demo;