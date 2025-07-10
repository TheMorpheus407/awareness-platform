import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, ArrowLeft, Mail, Phone, MapPin, Clock, Send } from 'lucide-react';
import { LanguageSwitcher } from '../../components/Common';

const Contact = () => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    phone: '',
    subject: '',
    message: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle form submission
    console.log('Form submitted:', formData);
    alert(t('contact.form.success', 'Vielen Dank für Ihre Nachricht. Wir werden uns umgehend bei Ihnen melden.'));
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
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

      {/* Hero Section */}
      <div className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto">
          <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-8">
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('common.back')}
          </Link>

          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              {t('contact.title', 'Kontaktieren Sie uns')}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {t('contact.subtitle', 
                'Haben Sie Fragen zu unseren Lösungen? Unser Team steht Ihnen gerne zur Verfügung.'
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Contact Information */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            {/* Contact Form */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-lg p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  {t('contact.form.title', 'Nachricht senden')}
                </h2>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('contact.form.name', 'Name')} *
                      </label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        required
                        value={formData.name}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('contact.form.email', 'E-Mail')} *
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
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('contact.form.company', 'Unternehmen')}
                      </label>
                      <input
                        type="text"
                        id="company"
                        name="company"
                        value={formData.company}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('contact.form.phone', 'Telefon')}
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
                  </div>
                  <div>
                    <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('contact.form.subject', 'Betreff')} *
                    </label>
                    <select
                      id="subject"
                      name="subject"
                      required
                      value={formData.subject}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">{t('contact.form.selectSubject', 'Bitte wählen')}</option>
                      <option value="sales">{t('contact.form.subjects.sales', 'Vertriebsanfrage')}</option>
                      <option value="support">{t('contact.form.subjects.support', 'Technischer Support')}</option>
                      <option value="partnership">{t('contact.form.subjects.partnership', 'Partnerschaft')}</option>
                      <option value="demo">{t('contact.form.subjects.demo', 'Demo-Anfrage')}</option>
                      <option value="other">{t('contact.form.subjects.other', 'Sonstiges')}</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('contact.form.message', 'Nachricht')} *
                    </label>
                    <textarea
                      id="message"
                      name="message"
                      rows={6}
                      required
                      value={formData.message}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder={t('contact.form.messagePlaceholder', 'Wie können wir Ihnen helfen?')}
                    />
                  </div>
                  <div>
                    <button
                      type="submit"
                      className="w-full md:w-auto inline-flex items-center justify-center px-8 py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <Send className="w-5 h-5 mr-2" />
                      {t('contact.form.submit', 'Nachricht senden')}
                    </button>
                  </div>
                </form>
              </div>
            </div>

            {/* Contact Info */}
            <div className="space-y-6">
              {/* Address */}
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-start">
                  <MapPin className="w-6 h-6 text-blue-600 mt-1 mr-4" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {t('contact.info.address.title', 'Hauptsitz')}
                    </h3>
                    <p className="text-gray-600">
                      Bootstrap Academy GmbH<br />
                      Musterstraße 123<br />
                      10115 Berlin<br />
                      Deutschland
                    </p>
                  </div>
                </div>
              </div>

              {/* Phone */}
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-start">
                  <Phone className="w-6 h-6 text-blue-600 mt-1 mr-4" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {t('contact.info.phone.title', 'Telefon')}
                    </h3>
                    <p className="text-gray-600">
                      {t('contact.info.phone.sales', 'Vertrieb')}: +49 (0) 30 123456-100<br />
                      {t('contact.info.phone.support', 'Support')}: +49 (0) 30 123456-200
                    </p>
                  </div>
                </div>
              </div>

              {/* Email */}
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-start">
                  <Mail className="w-6 h-6 text-blue-600 mt-1 mr-4" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {t('contact.info.email.title', 'E-Mail')}
                    </h3>
                    <p className="text-gray-600">
                      {t('contact.info.email.general', 'Allgemein')}: info@bootstrap-academy.de<br />
                      {t('contact.info.email.sales', 'Vertrieb')}: sales@bootstrap-academy.de<br />
                      {t('contact.info.email.support', 'Support')}: support@bootstrap-academy.de
                    </p>
                  </div>
                </div>
              </div>

              {/* Business Hours */}
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-start">
                  <Clock className="w-6 h-6 text-blue-600 mt-1 mr-4" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {t('contact.info.hours.title', 'Geschäftszeiten')}
                    </h3>
                    <p className="text-gray-600">
                      {t('contact.info.hours.weekdays', 'Montag - Freitag')}: 9:00 - 18:00 Uhr<br />
                      {t('contact.info.hours.support', '24/7 Support für Enterprise-Kunden')}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Map Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('contact.map.title', 'So finden Sie uns')}
          </h2>
          <div className="bg-gray-300 rounded-lg h-96 flex items-center justify-center">
            <p className="text-gray-600">
              {t('contact.map.placeholder', 'Interaktive Karte')}
            </p>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('contact.faq.title', 'Häufig gestellte Fragen')}
          </h2>
          <div className="space-y-8">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {t('contact.faq.q1', 'Wie schnell erhalte ich eine Antwort?')}
              </h3>
              <p className="text-gray-600">
                {t('contact.faq.a1', 
                  'Wir bemühen uns, alle Anfragen innerhalb von 24 Stunden zu beantworten. Bei dringenden Anliegen nutzen Sie bitte unsere Hotline.'
                )}
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {t('contact.faq.q2', 'Bieten Sie auch vor-Ort-Beratungen an?')}
              </h3>
              <p className="text-gray-600">
                {t('contact.faq.a2', 
                  'Ja, für Enterprise-Kunden bieten wir persönliche Beratungstermine an. Kontaktieren Sie uns für weitere Details.'
                )}
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {t('contact.faq.q3', 'Wie kann ich eine Demo vereinbaren?')}
              </h3>
              <p className="text-gray-600">
                {t('contact.faq.a3', 
                  'Nutzen Sie unser Kontaktformular und wählen Sie "Demo-Anfrage" als Betreff. Wir melden uns umgehend bei Ihnen.'
                )}
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Contact;