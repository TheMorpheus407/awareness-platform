import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, ArrowLeft, Users, Target, Award, TrendingUp } from 'lucide-react';
import { LanguageSwitcher } from '../../components/Common';

const About = () => {
  const { t } = useTranslation();

  const milestones = [
    { year: '2020', event: 'Gründung der Bootstrap Academy GmbH' },
    { year: '2021', event: 'Launch der ersten Phishing-Simulation Platform' },
    { year: '2022', event: 'ISO 27001 Zertifizierung erhalten' },
    { year: '2023', event: 'Expansion in 5 europäische Länder' },
    { year: '2024', event: 'Über 500 Unternehmenskunden' },
  ];

  const teamMembers = [
    {
      name: 'Dr. Max Mustermann',
      role: 'CEO & Founder',
      bio: 'Cybersecurity-Experte mit über 15 Jahren Erfahrung in der IT-Sicherheit.',
    },
    {
      name: 'Erika Musterfrau',
      role: 'CTO & Co-Founder',
      bio: 'Spezialistin für Cloud-Architekturen und sichere Softwareentwicklung.',
    },
    {
      name: 'Thomas Schmidt',
      role: 'Head of Security Research',
      bio: 'Ethical Hacker und Trainer für Cybersecurity-Awareness.',
    },
    {
      name: 'Sarah Weber',
      role: 'Head of Customer Success',
      bio: 'Expertin für Enterprise-Kunden und Compliance-Management.',
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
              {t('about.title', 'Über Bootstrap Academy')}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {t('about.subtitle', 
                'Wir sind Ihr Partner für umfassende Cybersecurity-Awareness und schützen Unternehmen vor digitalen Bedrohungen durch innovative Schulungslösungen.'
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Mission Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-6">
                {t('about.mission.title', 'Unsere Mission')}
              </h2>
              <p className="text-lg text-gray-700 mb-4">
                {t('about.mission.paragraph1',
                  'Bootstrap Academy wurde mit dem Ziel gegründet, Unternehmen dabei zu helfen, ihre größte Schwachstelle in der Cybersicherheit zu adressieren: den menschlichen Faktor.'
                )}
              </p>
              <p className="text-lg text-gray-700 mb-4">
                {t('about.mission.paragraph2',
                  'Durch praxisnahe Simulationen und interaktive Schulungen schaffen wir ein Bewusstsein für Cybergefahren und befähigen Mitarbeiter, sich und ihr Unternehmen aktiv zu schützen.'
                )}
              </p>
              <p className="text-lg text-gray-700">
                {t('about.mission.paragraph3',
                  'Unsere Plattform kombiniert modernste Technologie mit bewährten pädagogischen Konzepten, um nachhaltige Verhaltensänderungen zu bewirken.'
                )}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-blue-50 rounded-lg p-6 text-center">
                <Target className="w-12 h-12 text-blue-600 mx-auto mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">Zielgerichtet</h3>
                <p className="text-sm text-gray-600">Maßgeschneiderte Lösungen für Ihre Branche</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-6 text-center">
                <Users className="w-12 h-12 text-blue-600 mx-auto mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">Benutzerfreundlich</h3>
                <p className="text-sm text-gray-600">Intuitive Plattform für alle Mitarbeiter</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-6 text-center">
                <Award className="w-12 h-12 text-blue-600 mx-auto mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">Zertifiziert</h3>
                <p className="text-sm text-gray-600">ISO 27001 und GDPR-konform</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-6 text-center">
                <TrendingUp className="w-12 h-12 text-blue-600 mx-auto mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">Messbar</h3>
                <p className="text-sm text-gray-600">Detaillierte Analysen und Reports</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Timeline Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('about.timeline.title', 'Unsere Geschichte')}
          </h2>
          <div className="relative">
            <div className="absolute left-1/2 transform -translate-x-1/2 h-full w-0.5 bg-gray-300"></div>
            {milestones.map((milestone, index) => (
              <div key={index} className={`relative flex items-center ${index % 2 === 0 ? 'justify-start' : 'justify-end'} mb-8`}>
                <div className={`w-5/12 ${index % 2 === 0 ? 'text-right pr-8' : 'text-left pl-8'}`}>
                  <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-xl font-bold text-blue-600 mb-2">{milestone.year}</h3>
                    <p className="text-gray-700">{milestone.event}</p>
                  </div>
                </div>
                <div className="absolute left-1/2 transform -translate-x-1/2 w-4 h-4 bg-blue-600 rounded-full"></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('about.team.title', 'Unser Team')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {teamMembers.map((member, index) => (
              <div key={index} className="text-center">
                <div className="w-32 h-32 bg-gray-300 rounded-full mx-auto mb-4"></div>
                <h3 className="text-xl font-semibold text-gray-900 mb-1">{member.name}</h3>
                <p className="text-blue-600 font-medium mb-3">{member.role}</p>
                <p className="text-gray-600 text-sm">{member.bio}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-12">
            {t('about.values.title', 'Unsere Werte')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-xl font-semibold mb-3">Sicherheit</h3>
              <p className="text-blue-100">
                Wir leben Cybersicherheit in allem was wir tun und setzen höchste Standards für uns und unsere Kunden.
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-3">Innovation</h3>
              <p className="text-blue-100">
                Wir entwickeln kontinuierlich neue Ansätze, um den sich ständig verändernden Bedrohungen einen Schritt voraus zu sein.
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-3">Partnerschaft</h3>
              <p className="text-blue-100">
                Wir sehen uns als verlässlichen Partner unserer Kunden und arbeiten gemeinsam an ihrer Sicherheit.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            {t('about.cta.title', 'Bereit für mehr Sicherheit?')}
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            {t('about.cta.subtitle', 'Lassen Sie uns gemeinsam Ihre Cybersecurity-Awareness auf das nächste Level bringen.')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/contact" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              {t('about.cta.contact', 'Kontakt aufnehmen')}
            </Link>
            <Link 
              to="/demo" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-blue-600 border-2 border-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
            >
              {t('about.cta.demo', 'Demo anfordern')}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;