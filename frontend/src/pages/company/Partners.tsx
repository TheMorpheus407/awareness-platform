import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, ArrowLeft, Handshake, Award, Globe, Users, Briefcase, ChevronRight } from 'lucide-react';
import { LanguageSwitcher } from '../../components/Common';

const Partners = () => {
  const { t } = useTranslation();

  const partnerTypes = [
    {
      type: 'Technology Partners',
      icon: <Globe className="w-8 h-8 text-blue-600" />,
      description: 'Integrationen mit führenden Sicherheits- und IT-Management-Plattformen',
      partners: ['Microsoft', 'Google Workspace', 'Slack', 'Okta', 'ServiceNow'],
      benefits: [
        'Nahtlose Integration in bestehende Systeme',
        'Single Sign-On (SSO) Support',
        'Automatisierte Benutzer-Synchronisation',
        'Erweiterte API-Funktionen',
      ],
    },
    {
      type: 'Channel Partners',
      icon: <Briefcase className="w-8 h-8 text-blue-600" />,
      description: 'Vertriebspartner, die unsere Lösungen in ihren Märkten anbieten',
      partners: ['IT-Systemhäuser', 'Managed Service Provider', 'Cybersecurity-Beratungen'],
      benefits: [
        'Attraktive Margen und Provisionen',
        'Dedizierter Partner-Support',
        'Co-Marketing-Möglichkeiten',
        'Technische Schulungen und Zertifizierungen',
      ],
    },
    {
      type: 'Consulting Partners',
      icon: <Users className="w-8 h-8 text-blue-600" />,
      description: 'Beratungsunternehmen, die unsere Plattform in ihre Services integrieren',
      partners: ['Big Four Beratungen', 'Spezialisierte Security-Berater', 'Compliance-Experten'],
      benefits: [
        'White-Label-Optionen',
        'Erweiterte Reporting-Funktionen',
        'Individuelle Anpassungen',
        'Gemeinsame Kundenbetreuung',
      ],
    },
  ];

  const partnerBenefits = [
    {
      title: 'Wachstum',
      description: 'Erweitern Sie Ihr Portfolio und erschließen Sie neue Umsatzquellen',
      icon: '📈',
    },
    {
      title: 'Support',
      description: 'Umfassende technische und vertriebliche Unterstützung',
      icon: '🤝',
    },
    {
      title: 'Training',
      description: 'Regelmäßige Schulungen und Zertifizierungsprogramme',
      icon: '🎓',
    },
    {
      title: 'Marketing',
      description: 'Gemeinsame Marketing-Aktivitäten und Lead-Generierung',
      icon: '📢',
    },
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
            <Handshake className="w-16 h-16 text-blue-600 mx-auto mb-6" />
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              {t('partners.title', 'Partner-Programm')}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {t('partners.subtitle', 
                'Gemeinsam machen wir Unternehmen sicherer. Werden Sie Teil unseres wachsenden Partner-Ökosystems.'
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Partner Types */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('partners.types.title', 'Unsere Partner-Programme')}
          </h2>
          <div className="space-y-12">
            {partnerTypes.map((type, index) => (
              <div key={index} className="bg-white rounded-lg shadow-lg p-8">
                <div className="flex items-start mb-6">
                  {type.icon}
                  <div className="ml-4">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{type.type}</h3>
                    <p className="text-gray-600">{type.description}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">{t('partners.currentPartners', 'Aktuelle Partner')}</h4>
                    <div className="flex flex-wrap gap-3">
                      {type.partners.map((partner, idx) => (
                        <span key={idx} className="px-4 py-2 bg-gray-100 rounded-lg text-gray-700">
                          {partner}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">{t('partners.benefits', 'Ihre Vorteile')}</h4>
                    <ul className="space-y-2">
                      {type.benefits.map((benefit, idx) => (
                        <li key={idx} className="flex items-start">
                          <ChevronRight className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                          <span className="text-gray-600">{benefit}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('partners.whyPartner.title', 'Warum Partner werden?')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {partnerBenefits.map((benefit, index) => (
              <div key={index} className="text-center">
                <div className="text-5xl mb-4">{benefit.icon}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{benefit.title}</h3>
                <p className="text-gray-600">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Success Stories */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('partners.success.title', 'Partner-Erfolgsgeschichten')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <Award className="w-12 h-12 text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">TechPartner GmbH</h3>
              <p className="text-gray-600 mb-4">
                "Durch die Partnerschaft mit Bootstrap Academy konnten wir unser Security-Portfolio erweitern und 
                unseren Umsatz um 45% steigern."
              </p>
              <p className="text-sm text-gray-500">
                <strong>Johannes Meyer</strong><br />
                Geschäftsführer
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow-lg p-6">
              <Award className="w-12 h-12 text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">SecureIT Solutions</h3>
              <p className="text-gray-600 mb-4">
                "Die technische Integration war nahtlos und der Support ist erstklassig. Unsere Kunden sind begeistert."
              </p>
              <p className="text-sm text-gray-500">
                <strong>Maria Schmidt</strong><br />
                Head of Partnerships
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow-lg p-6">
              <Award className="w-12 h-12 text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Cyber Consulting AG</h3>
              <p className="text-gray-600 mb-4">
                "Bootstrap Academy ist ein verlässlicher Partner, der uns hilft, unseren Kunden einen echten Mehrwert zu bieten."
              </p>
              <p className="text-sm text-gray-500">
                <strong>Dr. Thomas Weber</strong><br />
                Senior Consultant
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Partner Requirements */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">
            {t('partners.requirements.title', 'Partner-Anforderungen')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-3">Expertise</h3>
              <p className="text-blue-100">
                Nachgewiesene Erfahrung im Bereich Cybersecurity oder IT-Management
              </p>
            </div>
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-3">Engagement</h3>
              <p className="text-blue-100">
                Aktive Beteiligung an gemeinsamen Vertriebs- und Marketing-Aktivitäten
              </p>
            </div>
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-3">Qualität</h3>
              <p className="text-blue-100">
                Hohe Service-Standards und Kundenzufriedenheit
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Application Process */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('partners.process.title', 'So werden Sie Partner')}
          </h2>
          <div className="space-y-6">
            <div className="flex items-start">
              <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                1
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Bewerbung</h3>
                <p className="text-gray-600">
                  Füllen Sie unser Partner-Bewerbungsformular aus und teilen Sie uns Ihre Expertise mit.
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                2
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Evaluation</h3>
                <p className="text-gray-600">
                  Unser Partner-Team prüft Ihre Bewerbung und vereinbart ein erstes Gespräch.
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                3
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Onboarding</h3>
                <p className="text-gray-600">
                  Nach erfolgreicher Prüfung durchlaufen Sie unser Partner-Onboarding-Programm.
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                4
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Start</h3>
                <p className="text-gray-600">
                  Sie erhalten Zugang zu allen Partner-Ressourcen und können sofort loslegen.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            {t('partners.cta.title', 'Bereit für eine erfolgreiche Partnerschaft?')}
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            {t('partners.cta.subtitle', 
              'Lassen Sie uns gemeinsam wachsen und die digitale Welt sicherer machen.'
            )}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/contact" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              {t('partners.cta.apply', 'Jetzt bewerben')}
            </Link>
            <a 
              href="/partners-brochure.pdf" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-blue-600 border-2 border-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
            >
              {t('partners.cta.download', 'Partner-Broschüre')}
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Partners;