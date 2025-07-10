import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, ArrowLeft, Briefcase, MapPin, Clock, ChevronRight } from 'lucide-react';
import { LanguageSwitcher } from '../../components/Common';

const Careers = () => {
  const { t } = useTranslation();

  const openPositions = [
    {
      id: 1,
      title: 'Senior Frontend Developer',
      department: 'Engineering',
      location: 'Berlin / Remote',
      type: 'Vollzeit',
      description: 'Wir suchen einen erfahrenen Frontend-Entwickler mit React und TypeScript Expertise.',
    },
    {
      id: 2,
      title: 'Cybersecurity Analyst',
      department: 'Security',
      location: 'Berlin',
      type: 'Vollzeit',
      description: 'Verstärken Sie unser Security-Team und entwickeln Sie innovative Phishing-Simulationen.',
    },
    {
      id: 3,
      title: 'Customer Success Manager',
      department: 'Customer Success',
      location: 'Berlin / München',
      type: 'Vollzeit',
      description: 'Betreuen Sie unsere Enterprise-Kunden und helfen Sie ihnen, das Beste aus unserer Plattform herauszuholen.',
    },
    {
      id: 4,
      title: 'DevOps Engineer',
      department: 'Engineering',
      location: 'Remote',
      type: 'Vollzeit',
      description: 'Optimieren Sie unsere Cloud-Infrastruktur und CI/CD-Pipelines.',
    },
    {
      id: 5,
      title: 'Content Marketing Manager',
      department: 'Marketing',
      location: 'Berlin',
      type: 'Vollzeit',
      description: 'Erstellen Sie hochwertige Inhalte rund um Cybersecurity und Awareness-Training.',
    },
  ];

  const benefits = [
    {
      title: 'Flexible Arbeitszeiten',
      description: 'Home-Office und flexible Arbeitszeiten für eine optimale Work-Life-Balance.',
    },
    {
      title: 'Weiterbildung',
      description: 'Jährliches Budget für Konferenzen, Kurse und Zertifizierungen.',
    },
    {
      title: 'Moderne Ausstattung',
      description: 'Neueste Hardware und Software nach Ihren Wünschen.',
    },
    {
      title: 'Team-Events',
      description: 'Regelmäßige Team-Events und gemeinsame Aktivitäten.',
    },
    {
      title: 'Gesundheit',
      description: 'Betriebliche Krankenversicherung und Fitness-Zuschuss.',
    },
    {
      title: 'Mobilität',
      description: 'JobRad-Leasing oder ÖPNV-Zuschuss.',
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
              {t('careers.title', 'Werde Teil unseres Teams')}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {t('careers.subtitle', 
                'Gestalten Sie mit uns die Zukunft der Cybersecurity-Awareness und machen Sie das Internet zu einem sichereren Ort.'
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Why Join Us Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('careers.whyJoin.title', 'Warum Bootstrap Academy?')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Mission mit Impact</h3>
              <p className="text-gray-600">
                Tragen Sie aktiv dazu bei, Unternehmen und ihre Mitarbeiter vor Cyberbedrohungen zu schützen.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Briefcase className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Wachstum & Entwicklung</h3>
              <p className="text-gray-600">
                Kontinuierliche Weiterbildung und Karriereentwicklung in einem schnell wachsenden Unternehmen.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Clock className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Work-Life-Balance</h3>
              <p className="text-gray-600">
                Flexible Arbeitsmodelle und eine Kultur, die Ihre persönlichen Bedürfnisse respektiert.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('careers.benefits.title', 'Unsere Benefits')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {benefits.map((benefit, index) => (
              <div key={index} className="bg-white rounded-lg p-6 shadow-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{benefit.title}</h3>
                <p className="text-gray-600">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Open Positions Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('careers.openPositions.title', 'Offene Stellen')}
          </h2>
          <div className="space-y-4">
            {openPositions.map((position) => (
              <Link
                key={position.id}
                to={`/careers/${position.id}`}
                className="block bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">{position.title}</h3>
                    <p className="text-gray-600 mb-3">{position.description}</p>
                    <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                      <span className="flex items-center">
                        <Briefcase className="w-4 h-4 mr-1" />
                        {position.department}
                      </span>
                      <span className="flex items-center">
                        <MapPin className="w-4 h-4 mr-1" />
                        {position.location}
                      </span>
                      <span className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        {position.type}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="w-6 h-6 text-gray-400 ml-4" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Culture Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">
            {t('careers.culture.title', 'Unsere Kultur')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            <div>
              <h3 className="text-2xl font-semibold mb-4">Gemeinsam stark</h3>
              <p className="text-blue-100 mb-4">
                Bei Bootstrap Academy arbeiten wir in einem dynamischen, internationalen Team zusammen. 
                Wir schätzen Vielfalt, fördern Innovation und feiern gemeinsame Erfolge.
              </p>
              <p className="text-blue-100 mb-4">
                Unsere flachen Hierarchien ermöglichen schnelle Entscheidungen und geben jedem die 
                Möglichkeit, Verantwortung zu übernehmen und eigene Ideen einzubringen.
              </p>
              <p className="text-blue-100">
                Wir glauben an kontinuierliches Lernen und unterstützen unsere Mitarbeiter dabei, 
                sich persönlich und fachlich weiterzuentwickeln.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/10 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold mb-2">50+</div>
                <p className="text-blue-100">Mitarbeiter</p>
              </div>
              <div className="bg-white/10 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold mb-2">12</div>
                <p className="text-blue-100">Nationalitäten</p>
              </div>
              <div className="bg-white/10 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold mb-2">4.8</div>
                <p className="text-blue-100">Kununu Score</p>
              </div>
              <div className="bg-white/10 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold mb-2">95%</div>
                <p className="text-blue-100">Weiterempfehlung</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Application Process Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('careers.process.title', 'Unser Bewerbungsprozess')}
          </h2>
          <div className="max-w-4xl mx-auto">
            <div className="space-y-8">
              <div className="flex items-start">
                <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  1
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Online-Bewerbung</h3>
                  <p className="text-gray-600">
                    Senden Sie uns Ihre aussagekräftige Bewerbung über unser Online-Formular.
                  </p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  2
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Erstes Gespräch</h3>
                  <p className="text-gray-600">
                    Telefonisches oder Video-Interview zum gegenseitigen Kennenlernen.
                  </p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  3
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Fachgespräch</h3>
                  <p className="text-gray-600">
                    Detailliertes Gespräch mit dem Team und ggf. praktische Aufgabe.
                  </p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  4
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Angebot & Start</h3>
                  <p className="text-gray-600">
                    Bei gegenseitigem Interesse erhalten Sie ein attraktives Angebot von uns.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            {t('careers.cta.title', 'Keine passende Stelle dabei?')}
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            {t('careers.cta.subtitle', 
              'Wir freuen uns auch über Initiativbewerbungen. Zeigen Sie uns, wie Sie Bootstrap Academy bereichern können!'
            )}
          </p>
          <Link 
            to="/contact" 
            className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            {t('careers.cta.button', 'Initiativbewerbung senden')}
          </Link>
        </div>
      </section>
    </div>
  );
};

export default Careers;