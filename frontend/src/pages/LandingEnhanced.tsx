import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Shield, 
  CheckCircle, 
  BarChart3, 
  Lock, 
  Mail, 
  Globe,
  Award,
  ArrowRight,
  Star,
  Zap,
  FileCheck,
  Users,
  Building,
  TrendingUp,
  Clock,
  Play,
  Calculator,
  Briefcase,
  ShieldCheck,
  UserCheck,
  AlertTriangle,
  BookOpen,
  Target,
  ChevronRight
} from 'lucide-react';
import { LanguageSwitcher } from '../components/Common';
import { useScrollAnimation } from '../hooks/useScrollAnimation';
import { useState } from 'react';

const LandingEnhanced = () => {
  const { t } = useTranslation();
  const [activeIndustry, setActiveIndustry] = useState('finance');
  const [roiUsers, setRoiUsers] = useState(100);
  
  // Animation hooks for different sections
  const heroAnimation = useScrollAnimation();
  const trustAnimation = useScrollAnimation();
  const featuresAnimation = useScrollAnimation();
  const benefitsAnimation = useScrollAnimation();
  const industriesAnimation = useScrollAnimation();
  const complianceAnimation = useScrollAnimation();
  const pricingAnimation = useScrollAnimation();
  const testimonialsAnimation = useScrollAnimation();
  const securityAnimation = useScrollAnimation();
  const ctaAnimation = useScrollAnimation();
  
  // Smooth scroll handler
  const handleSmoothScroll = (e: React.MouseEvent<HTMLAnchorElement>, targetId: string) => {
    e.preventDefault();
    const element = document.getElementById(targetId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // ROI Calculator
  const calculateROI = () => {
    const avgBreachCost = 4500000; // €4.5M average breach cost
    const reductionRate = 0.90; // 90% reduction in incidents
    const platformCost = roiUsers * 12 * 12; // Annual cost
    const potentialSavings = avgBreachCost * reductionRate;
    const roi = ((potentialSavings - platformCost) / platformCost * 100).toFixed(0);
    return {
      savings: potentialSavings.toLocaleString('de-DE'),
      roi: roi
    };
  };

  const features = [
    {
      icon: <Mail className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.phishing.title'),
      description: t('landing.features.phishing.description'),
      stats: t('landing.features.phishing.stats')
    },
    {
      icon: <Globe className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.training.title'),
      description: t('landing.features.training.description'),
      stats: t('landing.features.training.stats')
    },
    {
      icon: <BarChart3 className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.analytics.title'),
      description: t('landing.features.analytics.description'),
      stats: t('landing.features.analytics.stats')
    },
    {
      icon: <FileCheck className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.compliance.title'),
      description: t('landing.features.compliance.description'),
      stats: t('landing.features.compliance.stats')
    }
  ];

  const industries = {
    finance: {
      icon: <Briefcase className="w-12 h-12" />,
      title: t('landing.industries.finance.title'),
      challenges: [t('landing.industries.finance.challenge1'), t('landing.industries.finance.challenge2'), t('landing.industries.finance.challenge3')],
      solutions: [t('landing.industries.finance.solution1'), t('landing.industries.finance.solution2'), t('landing.industries.finance.solution3')]
    },
    healthcare: {
      icon: <UserCheck className="w-12 h-12" />,
      title: t('landing.industries.healthcare.title'),
      challenges: [t('landing.industries.healthcare.challenge1'), t('landing.industries.healthcare.challenge2'), t('landing.industries.healthcare.challenge3')],
      solutions: [t('landing.industries.healthcare.solution1'), t('landing.industries.healthcare.solution2'), t('landing.industries.healthcare.solution3')]
    },
    manufacturing: {
      icon: <Building className="w-12 h-12" />,
      title: t('landing.industries.manufacturing.title'),
      challenges: [t('landing.industries.manufacturing.challenge1'), t('landing.industries.manufacturing.challenge2'), t('landing.industries.manufacturing.challenge3')],
      solutions: [t('landing.industries.manufacturing.solution1'), t('landing.industries.manufacturing.solution2'), t('landing.industries.manufacturing.solution3')]
    },
    government: {
      icon: <ShieldCheck className="w-12 h-12" />,
      title: t('landing.industries.government.title'),
      challenges: [t('landing.industries.government.challenge1'), t('landing.industries.government.challenge2'), t('landing.industries.government.challenge3')],
      solutions: [t('landing.industries.government.solution1'), t('landing.industries.government.solution2'), t('landing.industries.government.solution3')]
    }
  };

  const companyLogos = [
    { name: "Siemens", logo: "/logos/placeholder.svg" },
    { name: "Deutsche Bank", logo: "/logos/placeholder.svg" },
    { name: "SAP", logo: "/logos/placeholder.svg" },
    { name: "Volkswagen", logo: "/logos/placeholder.svg" },
    { name: "Allianz", logo: "/logos/placeholder.svg" },
    { name: "BASF", logo: "/logos/placeholder.svg" }
  ];

  const certifications = [
    { name: t('landing.certifications.iso27001'), icon: <Award className="w-16 h-16 text-blue-600" /> },
    { name: t('landing.certifications.soc2'), icon: <ShieldCheck className="w-16 h-16 text-blue-600" /> },
    { name: t('landing.certifications.gdpr'), icon: <FileCheck className="w-16 h-16 text-blue-600" /> },
    { name: t('landing.certifications.bsi'), icon: <Shield className="w-16 h-16 text-blue-600" /> }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-sm z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-2">
              <Shield className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">Bootstrap Academy</span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" onClick={(e) => handleSmoothScroll(e, 'features')} className="text-gray-600 hover:text-gray-900">{t('landing.nav.features')}</a>
              <a href="#industries" onClick={(e) => handleSmoothScroll(e, 'industries')} className="text-gray-600 hover:text-gray-900">{t('landing.nav.industries')}</a>
              <a href="#pricing" onClick={(e) => handleSmoothScroll(e, 'pricing')} className="text-gray-600 hover:text-gray-900">{t('landing.nav.pricing')}</a>
              <a href="#resources" className="text-gray-600 hover:text-gray-900">{t('landing.nav.resources')}</a>
            </div>
            <div className="flex items-center space-x-4">
              <LanguageSwitcher />
              <Link to="/login" className="text-gray-600 hover:text-gray-900 transition-colors">
                {t('auth.login.signIn')}
              </Link>
              <Link 
                to="/register" 
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                {t('landing.nav.getDemo')}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section with Video */}
      <section 
        ref={heroAnimation.ref as React.RefObject<HTMLElement>}
        className={`pt-24 pb-16 px-4 sm:px-6 lg:px-8 transition-all duration-1000 ${
          heroAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-medium mb-4">
                <AlertTriangle className="w-4 h-4 mr-2" />
                {t('landing.hero.nis2Badge')}
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
                Transform Your Employees Into Your Strongest <span className="text-blue-600">Security Asset</span>
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                {t('landing.hero.mainSubtitle')}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <Link 
                  to="/register" 
                  className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  {t('landing.hero.ctaPrimary')}
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Link>
                <button className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-blue-600 border-2 border-blue-600 rounded-lg hover:bg-blue-50 transition-colors">
                  <Play className="mr-2 w-5 h-5" />
                  {t('landing.hero.ctaSecondary')}
                </button>
              </div>
              <div className="flex items-center space-x-6 text-sm text-gray-600">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-1" />
                  {t('landing.hero.badge2')}
                </div>
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-1" />
                  {t('landing.hero.gdprCompliant')}
                </div>
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-1" />
                  {t('landing.hero.setupTime')}
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="aspect-video bg-gray-900 rounded-2xl shadow-2xl overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  <button className="bg-white/90 rounded-full p-6 hover:bg-white transition-colors group">
                    <Play className="w-8 h-8 text-blue-600 ml-1 group-hover:scale-110 transition-transform" />
                  </button>
                </div>
                {/* Dashboard preview would go here */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-blue-800 opacity-20" />
              </div>
              <div className="absolute -bottom-6 -right-6 bg-white rounded-lg shadow-lg p-4">
                <div className="flex items-center space-x-3">
                  <div className="bg-green-100 rounded-full p-2">
                    <TrendingUp className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">90%</p>
                    <p className="text-sm text-gray-600">{t('landing.hero.incidentReduction')}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Indicators */}
      <section 
        ref={trustAnimation.ref as React.RefObject<HTMLElement>}
        className={`py-12 px-4 sm:px-6 lg:px-8 bg-gray-50 transition-all duration-1000 delay-200 ${
          trustAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-8">
            <p className="text-gray-600 font-medium">{t('landing.trust.title')}</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 items-center">
            {companyLogos.map((company, index) => (
              <div key={index} className="flex items-center justify-center">
                <img 
                  src={company.logo} 
                  alt={company.name}
                  className="h-12 opacity-60 hover:opacity-100 transition-opacity grayscale hover:grayscale-0"
                />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section 
        ref={featuresAnimation.ref as React.RefObject<HTMLElement>}
        id="features" 
        className={`py-16 px-4 sm:px-6 lg:px-8 transition-all duration-1000 delay-300 ${
          featuresAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.features.mainTitle')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('landing.features.mainSubtitle')}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index} 
                className="feature-card bg-white p-6 rounded-xl shadow-lg hover:shadow-xl border border-gray-100"
              >
                <div className="mb-4">{feature.icon}</div>
                <div className="text-sm font-semibold text-blue-600 mb-2">{feature.stats}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
          
          {/* Additional Features Grid */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-start space-x-3">
              <Users className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-gray-900">{t('landing.features.multiTenant.title')}</h4>
                <p className="text-gray-600 text-sm">{t('landing.features.multiTenant.description')}</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Clock className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-gray-900">{t('landing.features.automated.title')}</h4>
                <p className="text-gray-600 text-sm">{t('landing.features.automated.description')}</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Target className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-gray-900">{t('landing.features.roleBased.title')}</h4>
                <p className="text-gray-600 text-sm">{t('landing.features.roleBased.description')}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Industry Solutions */}
      <section 
        ref={industriesAnimation.ref as React.RefObject<HTMLElement>}
        id="industries"
        className={`py-16 px-4 sm:px-6 lg:px-8 bg-gray-50 transition-all duration-1000 delay-400 ${
          industriesAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.industries.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('landing.industries.subtitle')}
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white rounded-xl p-6 shadow-lg">
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(industries).map(([key, industry]) => (
                  <button
                    key={key}
                    onClick={() => setActiveIndustry(key)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      activeIndustry === key 
                        ? 'border-blue-600 bg-blue-50' 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className={`mb-2 ${activeIndustry === key ? 'text-blue-600' : 'text-gray-600'}`}>
                      {industry.icon}
                    </div>
                    <p className="font-medium text-gray-900">{industry.title}</p>
                  </button>
                ))}
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-lg">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                {industries[activeIndustry as keyof typeof industries].title} {t('landing.industries.securityChallenges')}
              </h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">{t('landing.industries.keyChallenges')}</h4>
                  <ul className="space-y-2">
                    {industries[activeIndustry as keyof typeof industries].challenges.map((challenge, index) => (
                      <li key={index} className="flex items-start">
                        <AlertTriangle className="w-5 h-5 text-orange-500 mr-2 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-600">{challenge}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">{t('landing.industries.ourSolutions')}</h4>
                  <ul className="space-y-2">
                    {industries[activeIndustry as keyof typeof industries].solutions.map((solution, index) => (
                      <li key={index} className="flex items-start">
                        <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-600">{solution}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ROI Calculator */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-blue-600 rounded-2xl p-8 md:p-12 text-white">
            <div className="text-center mb-8">
              <Calculator className="w-16 h-16 mx-auto mb-4" />
              <h2 className="text-3xl font-bold mb-4">{t('landing.roi.title')}</h2>
              <p className="text-lg opacity-90">
                {t('landing.roi.subtitle')}
              </p>
            </div>
            
            <div className="bg-white/10 rounded-lg p-6 backdrop-blur-sm">
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">{t('landing.roi.numberOfEmployees')}</label>
                <input
                  type="range"
                  min="50"
                  max="5000"
                  step="50"
                  value={roiUsers}
                  onChange={(e) => setRoiUsers(Number(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-sm mt-2">
                  <span>50</span>
                  <span className="font-bold text-lg">{roiUsers.toLocaleString()}</span>
                  <span>5000+</span>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div className="bg-white/10 rounded-lg p-4">
                  <p className="text-sm opacity-90 mb-1">{t('landing.roi.platformCost')}</p>
                  <p className="text-2xl font-bold">€{(roiUsers * 12).toLocaleString()}/mo</p>
                </div>
                <div className="bg-white/10 rounded-lg p-4">
                  <p className="text-sm opacity-90 mb-1">{t('landing.roi.potentialSavings')}</p>
                  <p className="text-2xl font-bold">€{calculateROI().savings}</p>
                </div>
                <div className="bg-white/10 rounded-lg p-4">
                  <p className="text-sm opacity-90 mb-1">{t('landing.roi.roiLabel')}</p>
                  <p className="text-2xl font-bold">{calculateROI().roi}%</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Compliance Section */}
      <section 
        ref={complianceAnimation.ref as React.RefObject<HTMLElement>}
        className={`py-16 px-4 sm:px-6 lg:px-8 bg-gray-50 transition-all duration-1000 delay-500 ${
          complianceAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.compliance.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('landing.compliance.subtitle')}
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {certifications.map((cert, index) => (
              <div key={index} className="text-center">
                <div className="inline-flex items-center justify-center w-24 h-24 bg-blue-50 rounded-full mb-4">
                  {cert.icon}
                </div>
                <h3 className="font-semibold text-gray-900">{cert.name}</h3>
              </div>
            ))}
          </div>
          
          <div className="mt-12 bg-white rounded-xl shadow-lg p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">{t('landing.compliance.nis2.title')}</h3>
                <p className="text-gray-600 mb-4">
                  {t('landing.compliance.nis2.subtitle')}
                </p>
                <ul className="space-y-2">
                  <li className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{t('landing.compliance.nis2.feature1')}</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{t('landing.compliance.nis2.feature2')}</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{t('landing.compliance.nis2.feature3')}</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{t('landing.compliance.nis2.feature4')}</span>
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">{t('landing.compliance.dataProtection.title')}</h3>
                <p className="text-gray-600 mb-4">
                  {t('landing.compliance.dataProtection.subtitle')}
                </p>
                <ul className="space-y-2">
                  <li className="flex items-start">
                    <Lock className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{t('landing.compliance.dataProtection.feature1')}</span>
                  </li>
                  <li className="flex items-start">
                    <Lock className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{t('landing.compliance.dataProtection.feature2')}</span>
                  </li>
                  <li className="flex items-start">
                    <Lock className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{t('landing.compliance.dataProtection.feature3')}</span>
                  </li>
                  <li className="flex items-start">
                    <Lock className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{t('landing.compliance.dataProtection.feature4')}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section 
        ref={pricingAnimation.ref as React.RefObject<HTMLElement>}
        id="pricing" 
        className={`py-16 px-4 sm:px-6 lg:px-8 transition-all duration-1000 delay-600 ${
          pricingAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.pricing.mainTitle')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('landing.pricing.mainSubtitle')}
            </p>
          </div>
          
          {/* Pricing cards remain the same but with enhanced features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="pricing-card bg-white rounded-xl shadow-lg p-8">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{t('landing.pricing.starter.name')}</h3>
                <div className="text-4xl font-bold text-gray-900 mb-2">€49<span className="text-lg text-gray-600">/{t('landing.pricing.perUserYear')}</span></div>
                <p className="text-gray-600">{t('landing.pricing.starter.tagline')}</p>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.starter.users')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.starter.phishing')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.starter.training')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.starter.reports')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.starter.support')}</span>
                </li>
              </ul>
              <Link 
                to="/register" 
                className="block w-full text-center py-3 px-6 rounded-lg font-medium bg-gray-100 text-gray-900 hover:bg-gray-200 transition-colors"
              >
                {t('landing.pricing.starter.cta')}
              </Link>
            </div>
            
            <div className="pricing-card relative bg-white rounded-xl shadow-xl p-8 ring-2 ring-blue-600">
              <div className="absolute -top-5 left-1/2 transform -translate-x-1/2">
                <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                  {t('landing.pricing.mostPopular')}
                </span>
              </div>
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{t('landing.pricing.professional.name')}</h3>
                <div className="text-4xl font-bold text-blue-600 mb-2">€39<span className="text-lg text-gray-600">/{t('landing.pricing.perUserYear')}</span></div>
                <p className="text-gray-600">{t('landing.pricing.professional.tagline')}</p>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.professional.users')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.professional.phishing')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.professional.training')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.professional.analytics')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.professional.api')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.professional.support')}</span>
                </li>
              </ul>
              <Link 
                to="/register" 
                className="block w-full text-center py-3 px-6 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                {t('landing.pricing.starter.cta')}
              </Link>
            </div>
            
            <div className="pricing-card bg-white rounded-xl shadow-lg p-8">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{t('landing.pricing.enterprise.name')}</h3>
                <div className="text-4xl font-bold text-gray-900 mb-2">{t('landing.pricing.enterprise.price')}</div>
                <p className="text-gray-600">{t('landing.pricing.enterprise.tagline')}</p>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.enterprise.users')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.enterprise.phishing')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.enterprise.training')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.enterprise.sso')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.enterprise.manager')}</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('landing.pricing.enterprise.support')}</span>
                </li>
              </ul>
              <Link 
                to="/contact" 
                className="block w-full text-center py-3 px-6 rounded-lg font-medium bg-gray-900 text-white hover:bg-gray-800 transition-colors"
              >
                {t('landing.pricing.enterprise.cta')}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Case Studies / Testimonials */}
      <section 
        ref={testimonialsAnimation.ref as React.RefObject<HTMLElement>}
        className={`py-16 px-4 sm:px-6 lg:px-8 bg-gray-50 transition-all duration-1000 delay-700 ${
          testimonialsAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.testimonials.mainTitle')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('landing.testimonials.mainSubtitle')}
            </p>
          </div>
          
          {/* Enhanced testimonials with metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-gray-700 mb-4 italic">
                "{t('landing.testimonials.testimonial1.quote')}"
              </p>
              <div className="border-t pt-4">
                <p className="font-semibold text-gray-900">{t('landing.testimonials.testimonial1.author')}</p>
                <p className="text-sm text-gray-600">{t('landing.testimonials.testimonial1.role')}, {t('landing.testimonials.testimonial1.company')}</p>
                <div className="mt-3 flex items-center space-x-4 text-sm">
                  <span className="text-green-600 font-semibold">{t('landing.testimonials.testimonial1.stat1')}</span>
                  <span className="text-blue-600 font-semibold">{t('landing.testimonials.testimonial1.stat2')}</span>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-gray-700 mb-4 italic">
                "{t('landing.testimonials.testimonial2.quote')}"
              </p>
              <div className="border-t pt-4">
                <p className="font-semibold text-gray-900">{t('landing.testimonials.testimonial2.author')}</p>
                <p className="text-sm text-gray-600">{t('landing.testimonials.testimonial2.role')}, {t('landing.testimonials.testimonial2.company')}</p>
                <div className="mt-3 flex items-center space-x-4 text-sm">
                  <span className="text-green-600 font-semibold">{t('landing.testimonials.testimonial2.stat1')}</span>
                  <span className="text-blue-600 font-semibold">{t('landing.testimonials.testimonial2.stat2')}</span>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-gray-700 mb-4 italic">
                "{t('landing.testimonials.testimonial3.quote')}"
              </p>
              <div className="border-t pt-4">
                <p className="font-semibold text-gray-900">{t('landing.testimonials.testimonial3.author')}</p>
                <p className="text-sm text-gray-600">{t('landing.testimonials.testimonial3.role')}, {t('landing.testimonials.testimonial3.company')}</p>
                <div className="mt-3 flex items-center space-x-4 text-sm">
                  <span className="text-green-600 font-semibold">{t('landing.testimonials.testimonial3.stat1')}</span>
                  <span className="text-blue-600 font-semibold">{t('landing.testimonials.testimonial3.stat2')}</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Case study CTA */}
          <div className="mt-12 text-center">
            <Link to="/case-studies" className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium">
              {t('landing.testimonials.readCaseStudies')}
              <ChevronRight className="w-5 h-5 ml-1" />
            </Link>
          </div>
        </div>
      </section>

      {/* Integration Partners */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              {t('landing.integrations.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('landing.integrations.subtitle')}
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center">
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-2">
                <img src="/logos/placeholder.svg" alt="Microsoft" className="h-12 mx-auto" />
              </div>
              <p className="text-sm text-gray-600">{t('landing.integrations.azure')}</p>
            </div>
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-2">
                <img src="/logos/placeholder.svg" alt="Slack" className="h-12 mx-auto" />
              </div>
              <p className="text-sm text-gray-600">{t('landing.integrations.slack')}</p>
            </div>
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-2">
                <img src="/logos/placeholder.svg" alt="Teams" className="h-12 mx-auto" />
              </div>
              <p className="text-sm text-gray-600">{t('landing.integrations.teams')}</p>
            </div>
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-2">
                <img src="/logos/placeholder.svg" alt="SAP" className="h-12 mx-auto" />
              </div>
              <p className="text-sm text-gray-600">{t('landing.integrations.sap')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section 
        ref={ctaAnimation.ref as React.RefObject<HTMLElement>}
        className={`py-16 px-4 sm:px-6 lg:px-8 bg-blue-600 transition-all duration-1000 delay-800 ${
          ctaAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            {t('landing.cta.finalTitle')}
          </h2>
          <p className="text-lg text-blue-100 mb-8">
            {t('landing.cta.finalSubtitle')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/register" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-blue-600 bg-white rounded-lg hover:bg-gray-100 transition-colors"
            >
              {t('landing.cta.startTrial')}
              <Zap className="ml-2 w-5 h-5" />
            </Link>
            <Link 
              to="/demo" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white border-2 border-white rounded-lg hover:bg-white/10 transition-colors"
            >
              {t('landing.cta.scheduleDemo')}
              <Play className="ml-2 w-5 h-5" />
            </Link>
          </div>
          <p className="mt-6 text-sm text-blue-100">
            {t('landing.cta.noCreditCard')} • {t('landing.cta.setupMinutes')} • {t('landing.cta.cancelAnytime')}
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
            <div className="md:col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <Shield className="w-8 h-8 text-blue-400" />
                <span className="text-xl font-bold">Bootstrap Academy</span>
              </div>
              <p className="text-gray-400 mb-4">
                {t('landing.footer.companyDescription')}
              </p>
              <div className="flex space-x-4">
                <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z"/>
                  </svg>
                </a>
                <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"/>
                  </svg>
                </a>
                <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                </a>
              </div>
            </div>
            <div>
              <h3 className="font-semibold mb-4">{t('landing.footer.product')}</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" onClick={(e) => handleSmoothScroll(e, 'features')} className="hover:text-white transition-colors">{t('landing.footer.features')}</a></li>
                <li><a href="#pricing" onClick={(e) => handleSmoothScroll(e, 'pricing')} className="hover:text-white transition-colors">{t('landing.footer.pricing')}</a></li>
                <li><Link to="/demo" className="hover:text-white transition-colors">{t('landing.footer.demo')}</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">{t('landing.footer.resources')}</h3>
              <ul className="space-y-2 text-gray-400">
                <li><Link to="/blog" className="hover:text-white transition-colors">{t('landing.footer.blog')}</Link></li>
                <li><Link to="/case-studies" className="hover:text-white transition-colors">{t('landing.footer.caseStudies')}</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">{t('landing.footer.company')}</h3>
              <ul className="space-y-2 text-gray-400">
                <li><Link to="/about" className="hover:text-white transition-colors">{t('landing.footer.about')}</Link></li>
                <li><Link to="/contact" className="hover:text-white transition-colors">{t('landing.footer.contact')}</Link></li>
                <li><Link to="/careers" className="hover:text-white transition-colors">{t('landing.footer.careers')}</Link></li>
                <li><Link to="/partners" className="hover:text-white transition-colors">{t('landing.footer.partners')}</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <p className="text-gray-400 text-sm">
                &copy; 2024 Bootstrap Academy GmbH. {t('landing.footer.rights')}
              </p>
              <div className="flex space-x-6 mt-4 md:mt-0 text-sm">
                <Link to="/privacy" className="text-gray-400 hover:text-white transition-colors">{t('landing.footer.privacy')}</Link>
                <Link to="/terms" className="text-gray-400 hover:text-white transition-colors">{t('landing.footer.terms')}</Link>
                <Link to="/impressum" className="text-gray-400 hover:text-white transition-colors">{t('landing.footer.impressum')}</Link>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingEnhanced;