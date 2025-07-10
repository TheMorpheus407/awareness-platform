import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, ArrowLeft, Building, Users, TrendingUp, Award, Download, ChevronRight } from 'lucide-react';
import { LanguageSwitcher } from '../../components/Common';

const CaseStudies = () => {
  const { t } = useTranslation();

  const caseStudies = [
    {
      id: 1,
      company: 'TechCorp GmbH',
      industry: 'Technologie',
      size: '500+ Mitarbeiter',
      logo: '/logos/techcorp.png',
      challenge: 'Hohe Phishing-Anfälligkeit und mangelndes Sicherheitsbewusstsein',
      solution: 'Implementierung von monatlichen Phishing-Simulationen und gezielten Schulungen',
      results: [
        '92% Reduktion erfolgreicher Phishing-Angriffe',
        '85% der Mitarbeiter bestanden Sicherheitstests',
        'ROI von 340% im ersten Jahr',
      ],
      quote: {
        text: 'Bootstrap Academy hat unsere Sicherheitskultur revolutioniert. Die Plattform ist intuitiv und die Ergebnisse sprechen für sich.',
        author: 'Michael Schmidt',
        role: 'IT-Leiter',
      },
    },
    {
      id: 2,
      company: 'FinanzPro AG',
      industry: 'Finanzdienstleistungen',
      size: '2000+ Mitarbeiter',
      logo: '/logos/finanzpro.png',
      challenge: 'Strenge Compliance-Anforderungen und komplexe Sicherheitsrichtlinien',
      solution: 'Maßgeschneiderte Compliance-Schulungen und automatisierte Reporting-Funktionen',
      results: [
        '100% Compliance mit BaFin-Anforderungen',
        '78% weniger Sicherheitsvorfälle',
        'Erfolgreiche Audits ohne Beanstandungen',
      ],
      quote: {
        text: 'Die Compliance-Features haben uns enorm geholfen. Wir können jetzt alle regulatorischen Anforderungen problemlos erfüllen.',
        author: 'Dr. Sarah Weber',
        role: 'Chief Compliance Officer',
      },
    },
    {
      id: 3,
      company: 'MediCare Kliniken',
      industry: 'Gesundheitswesen',
      size: '1000+ Mitarbeiter',
      logo: '/logos/medicare.png',
      challenge: 'Schutz sensibler Patientendaten und DSGVO-Konformität',
      solution: 'Spezialisierte Schulungen für Gesundheitsdaten und Datenschutz',
      results: [
        '95% Reduktion von Datenschutzverletzungen',
        'Vollständige DSGVO-Compliance erreicht',
        '€2.1M potenzielle Strafen vermieden',
      ],
      quote: {
        text: 'Der Schutz unserer Patientendaten hat oberste Priorität. Bootstrap Academy hilft uns dabei, dieses Ziel zu erreichen.',
        author: 'Prof. Dr. Thomas Müller',
        role: 'Ärztlicher Direktor',
      },
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
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              {t('caseStudies.title', 'Erfolgsgeschichten unserer Kunden')}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {t('caseStudies.subtitle', 
                'Erfahren Sie, wie führende Unternehmen ihre Cybersicherheit mit Bootstrap Academy verbessert haben.'
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-blue-600">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-white mb-2">500+</div>
              <p className="text-blue-100">{t('caseStudies.stats.companies', 'Unternehmen geschützt')}</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-white mb-2">89%</div>
              <p className="text-blue-100">{t('caseStudies.stats.reduction', 'Weniger Sicherheitsvorfälle')}</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-white mb-2">€15M+</div>
              <p className="text-blue-100">{t('caseStudies.stats.saved', 'Schäden verhindert')}</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-white mb-2">98%</div>
              <p className="text-blue-100">{t('caseStudies.stats.satisfaction', 'Kundenzufriedenheit')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Case Studies */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="space-y-16">
            {caseStudies.map((study, index) => (
              <div key={study.id} className={`${index % 2 === 0 ? '' : 'bg-gray-50 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-12'}`}>
                <div className="max-w-7xl mx-auto">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                    <div className={`${index % 2 === 0 ? '' : 'lg:order-2'}`}>
                      <div className="bg-white rounded-lg shadow-lg p-8">
                        <div className="flex items-center justify-between mb-6">
                          <div>
                            <h2 className="text-2xl font-bold text-gray-900">{study.company}</h2>
                            <div className="flex items-center space-x-4 text-sm text-gray-600 mt-2">
                              <span className="flex items-center">
                                <Building className="w-4 h-4 mr-1" />
                                {study.industry}
                              </span>
                              <span className="flex items-center">
                                <Users className="w-4 h-4 mr-1" />
                                {study.size}
                              </span>
                            </div>
                          </div>
                          <div className="w-20 h-20 bg-gray-200 rounded-lg"></div>
                        </div>

                        <div className="space-y-6">
                          <div>
                            <h3 className="font-semibold text-gray-900 mb-2">{t('caseStudies.challenge', 'Herausforderung')}</h3>
                            <p className="text-gray-600">{study.challenge}</p>
                          </div>

                          <div>
                            <h3 className="font-semibold text-gray-900 mb-2">{t('caseStudies.solution', 'Lösung')}</h3>
                            <p className="text-gray-600">{study.solution}</p>
                          </div>

                          <div>
                            <h3 className="font-semibold text-gray-900 mb-2">{t('caseStudies.results', 'Ergebnisse')}</h3>
                            <ul className="space-y-2">
                              {study.results.map((result, idx) => (
                                <li key={idx} className="flex items-start">
                                  <TrendingUp className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                                  <span className="text-gray-600">{result}</span>
                                </li>
                              ))}
                            </ul>
                          </div>

                          <div className="border-t pt-6">
                            <p className="text-gray-700 italic mb-3">"{study.quote.text}"</p>
                            <div>
                              <p className="font-semibold text-gray-900">{study.quote.author}</p>
                              <p className="text-sm text-gray-600">{study.quote.role}</p>
                            </div>
                          </div>

                          <div className="flex items-center justify-between pt-4">
                            <Link 
                              to={`/case-studies/${study.id}`}
                              className="text-blue-600 hover:text-blue-700 font-medium flex items-center"
                            >
                              {t('caseStudies.readMore', 'Vollständige Fallstudie lesen')}
                              <ChevronRight className="w-4 h-4 ml-1" />
                            </Link>
                            <button className="flex items-center text-gray-600 hover:text-gray-900">
                              <Download className="w-4 h-4 mr-1" />
                              PDF
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className={`${index % 2 === 0 ? '' : 'lg:order-1'}`}>
                      <div className="bg-gray-200 rounded-lg h-96"></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-blue-600">
        <div className="max-w-4xl mx-auto text-center">
          <Award className="w-16 h-16 text-white mx-auto mb-6" />
          <h2 className="text-3xl font-bold text-white mb-4">
            {t('caseStudies.cta.title', 'Werden Sie unsere nächste Erfolgsgeschichte')}
          </h2>
          <p className="text-lg text-blue-100 mb-8">
            {t('caseStudies.cta.subtitle', 
              'Starten Sie noch heute und verbessern Sie Ihre Cybersicherheit nachhaltig.'
            )}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/demo" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-blue-600 bg-white rounded-lg hover:bg-gray-100 transition-colors"
            >
              {t('caseStudies.cta.demo', 'Demo anfordern')}
            </Link>
            <Link 
              to="/contact" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white border-2 border-white rounded-lg hover:bg-white/10 transition-colors"
            >
              {t('caseStudies.cta.contact', 'Beratung vereinbaren')}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default CaseStudies;