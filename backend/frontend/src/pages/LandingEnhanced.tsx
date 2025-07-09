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
      stats: "50+ Templates"
    },
    {
      icon: <Globe className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.training.title'),
      description: t('landing.features.training.description'),
      stats: "30+ Modules"
    },
    {
      icon: <BarChart3 className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.analytics.title'),
      description: t('landing.features.analytics.description'),
      stats: "Real-time"
    },
    {
      icon: <FileCheck className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.compliance.title'),
      description: t('landing.features.compliance.description'),
      stats: "Auto-Reports"
    }
  ];

  const industries = {
    finance: {
      icon: <Briefcase className="w-12 h-12" />,
      title: "Financial Services",
      challenges: ["Regulatory compliance (BAFIN, PCI-DSS)", "High-value targets for cybercriminals", "Complex IT infrastructure"],
      solutions: ["BAFIN-compliant training modules", "Financial fraud awareness", "PCI-DSS certification tracking"]
    },
    healthcare: {
      icon: <UserCheck className="w-12 h-12" />,
      title: "Healthcare",
      challenges: ["Patient data protection (GDPR)", "Medical device security", "Staff with varying IT skills"],
      solutions: ["HIPAA/GDPR focused training", "Medical phishing scenarios", "Simplified learning paths"]
    },
    manufacturing: {
      icon: <Building className="w-12 h-12" />,
      title: "Manufacturing",
      challenges: ["OT/IT convergence risks", "Supply chain attacks", "TISAX compliance"],
      solutions: ["Industrial security training", "Supply chain modules", "TISAX compliance tracking"]
    },
    government: {
      icon: <ShieldCheck className="w-12 h-12" />,
      title: "Government",
      challenges: ["Nation-state threats", "Critical infrastructure", "BSI compliance"],
      solutions: ["Advanced threat training", "BSI-aligned content", "Classified handling modules"]
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
    { name: "ISO 27001", icon: <Award className="w-16 h-16 text-blue-600" /> },
    { name: "SOC 2 Type II", icon: <ShieldCheck className="w-16 h-16 text-blue-600" /> },
    { name: "GDPR/DSGVO", icon: <FileCheck className="w-16 h-16 text-blue-600" /> },
    { name: "BSI Grundschutz", icon: <Shield className="w-16 h-16 text-blue-600" /> }
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
              <a href="#features" onClick={(e) => handleSmoothScroll(e, 'features')} className="text-gray-600 hover:text-gray-900">Features</a>
              <a href="#industries" onClick={(e) => handleSmoothScroll(e, 'industries')} className="text-gray-600 hover:text-gray-900">Industries</a>
              <a href="#pricing" onClick={(e) => handleSmoothScroll(e, 'pricing')} className="text-gray-600 hover:text-gray-900">Pricing</a>
              <a href="#resources" className="text-gray-600 hover:text-gray-900">Resources</a>
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
                Get Demo
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
                NIS-2 Directive Compliance Ready
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
                Transform Your Employees Into Your Strongest <span className="text-blue-600">Security Asset</span>
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                Enterprise-grade cybersecurity awareness platform trusted by 500+ organizations across Europe. 
                Reduce security incidents by 90% with automated training, phishing simulations, and compliance reporting.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <Link 
                  to="/register" 
                  className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Start 14-Day Free Trial
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Link>
                <button className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-blue-600 border-2 border-blue-600 rounded-lg hover:bg-blue-50 transition-colors">
                  <Play className="mr-2 w-5 h-5" />
                  Watch 2-Min Demo
                </button>
              </div>
              <div className="flex items-center space-x-6 text-sm text-gray-600">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-1" />
                  No credit card required
                </div>
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-1" />
                  GDPR compliant
                </div>
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-1" />
                  Setup in 15 minutes
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
                    <p className="text-sm text-gray-600">Incident Reduction</p>
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
            <p className="text-gray-600 font-medium">Trusted by 500+ security-conscious organizations</p>
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
              Enterprise-Ready Security Awareness Platform
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Everything you need to build a culture of security in your organization
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
                <h4 className="font-semibold text-gray-900">Multi-Tenant Architecture</h4>
                <p className="text-gray-600 text-sm">Manage multiple companies with isolated data</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Clock className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-gray-900">Automated Campaigns</h4>
                <p className="text-gray-600 text-sm">Schedule training and phishing tests automatically</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Target className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-gray-900">Role-Based Training</h4>
                <p className="text-gray-600 text-sm">Tailored content for different job functions</p>
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
              Industry-Specific Solutions
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Tailored cybersecurity training that addresses your industry's unique challenges and compliance requirements
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
                {industries[activeIndustry as keyof typeof industries].title} Security Challenges
              </h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Key Challenges:</h4>
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
                  <h4 className="font-semibold text-gray-900 mb-2">Our Solutions:</h4>
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
              <h2 className="text-3xl font-bold mb-4">Calculate Your Security ROI</h2>
              <p className="text-lg opacity-90">
                See how much you could save by preventing security breaches
              </p>
            </div>
            
            <div className="bg-white/10 rounded-lg p-6 backdrop-blur-sm">
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">Number of Employees</label>
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
                  <p className="text-sm opacity-90 mb-1">Platform Cost</p>
                  <p className="text-2xl font-bold">€{(roiUsers * 12).toLocaleString()}/mo</p>
                </div>
                <div className="bg-white/10 rounded-lg p-4">
                  <p className="text-sm opacity-90 mb-1">Potential Savings</p>
                  <p className="text-2xl font-bold">€{calculateROI().savings}</p>
                </div>
                <div className="bg-white/10 rounded-lg p-4">
                  <p className="text-sm opacity-90 mb-1">ROI</p>
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
              Compliance & Certifications
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Meet regulatory requirements with confidence. Our platform is built to help you achieve and maintain compliance.
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
                <h3 className="text-xl font-bold text-gray-900 mb-4">NIS-2 Directive Compliance</h3>
                <p className="text-gray-600 mb-4">
                  Stay ahead of the NIS-2 directive requirements with our comprehensive compliance features:
                </p>
                <ul className="space-y-2">
                  <li className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">Automated incident reporting</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">Supply chain security training</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">Risk assessment tools</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">Compliance dashboards</span>
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">Data Protection & Privacy</h3>
                <p className="text-gray-600 mb-4">
                  Your data security is our top priority. We ensure complete GDPR/DSGVO compliance:
                </p>
                <ul className="space-y-2">
                  <li className="flex items-start">
                    <Lock className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">Data hosted in German data centers</span>
                  </li>
                  <li className="flex items-start">
                    <Lock className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">End-to-end encryption</span>
                  </li>
                  <li className="flex items-start">
                    <Lock className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">Regular security audits</span>
                  </li>
                  <li className="flex items-start">
                    <Lock className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">Data processing agreements</span>
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
              Transparent Pricing for Every Organization
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Start with a 14-day free trial. No credit card required.
            </p>
          </div>
          
          {/* Pricing cards remain the same but with enhanced features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="pricing-card bg-white rounded-xl shadow-lg p-8">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Starter</h3>
                <div className="text-4xl font-bold text-gray-900 mb-2">€49<span className="text-lg text-gray-600">/user/year</span></div>
                <p className="text-gray-600">For small teams getting started</p>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">10-100 users</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Basic phishing simulations</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">10 training modules</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Monthly reports</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Email support</span>
                </li>
              </ul>
              <Link 
                to="/register" 
                className="block w-full text-center py-3 px-6 rounded-lg font-medium bg-gray-100 text-gray-900 hover:bg-gray-200 transition-colors"
              >
                Start Free Trial
              </Link>
            </div>
            
            <div className="pricing-card relative bg-white rounded-xl shadow-xl p-8 ring-2 ring-blue-600">
              <div className="absolute -top-5 left-1/2 transform -translate-x-1/2">
                <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Professional</h3>
                <div className="text-4xl font-bold text-blue-600 mb-2">€39<span className="text-lg text-gray-600">/user/year</span></div>
                <p className="text-gray-600">For growing organizations</p>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">100-1000 users</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Advanced phishing campaigns</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">30+ training modules</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Real-time analytics</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">API access</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Priority support</span>
                </li>
              </ul>
              <Link 
                to="/register" 
                className="block w-full text-center py-3 px-6 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                Start Free Trial
              </Link>
            </div>
            
            <div className="pricing-card bg-white rounded-xl shadow-lg p-8">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Enterprise</h3>
                <div className="text-4xl font-bold text-gray-900 mb-2">Custom</div>
                <p className="text-gray-600">For large organizations</p>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Unlimited users</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Custom phishing scenarios</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Custom training content</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">SSO & advanced security</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Dedicated success manager</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">SLA & 24/7 support</span>
                </li>
              </ul>
              <button className="block w-full text-center py-3 px-6 rounded-lg font-medium bg-gray-900 text-white hover:bg-gray-800 transition-colors">
                Contact Sales
              </button>
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
              Success Stories from Our Customers
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              See how organizations like yours have transformed their security culture
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
                "Bootstrap Academy helped us reduce phishing incidents by 94% in just 6 months. The automated training and realistic simulations have transformed our security culture."
              </p>
              <div className="border-t pt-4">
                <p className="font-semibold text-gray-900">Dr. Sarah Schmidt</p>
                <p className="text-sm text-gray-600">CISO, Deutsche Bank</p>
                <div className="mt-3 flex items-center space-x-4 text-sm">
                  <span className="text-green-600 font-semibold">94% ↓ Incidents</span>
                  <span className="text-blue-600 font-semibold">15,000 Users</span>
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
                "The platform's compliance reporting saved us hundreds of hours preparing for our ISO 27001 audit. It's been a game-changer for our security team."
              </p>
              <div className="border-t pt-4">
                <p className="font-semibold text-gray-900">Michael Werner</p>
                <p className="text-sm text-gray-600">IT Director, Siemens</p>
                <div className="mt-3 flex items-center space-x-4 text-sm">
                  <span className="text-green-600 font-semibold">300h Saved</span>
                  <span className="text-blue-600 font-semibold">ISO Certified</span>
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
                "Our employees actually enjoy the security training now. The gamification and real-world scenarios make it engaging and memorable."
              </p>
              <div className="border-t pt-4">
                <p className="font-semibold text-gray-900">Anna Müller</p>
                <p className="text-sm text-gray-600">HR Director, Volkswagen</p>
                <div className="mt-3 flex items-center space-x-4 text-sm">
                  <span className="text-green-600 font-semibold">98% Completion</span>
                  <span className="text-blue-600 font-semibold">4.8/5 Rating</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Case study CTA */}
          <div className="mt-12 text-center">
            <Link to="/case-studies" className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium">
              Read detailed case studies
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
              Seamless Integration with Your Tech Stack
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Connect Bootstrap Academy with your existing tools for a unified security ecosystem
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center">
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-2">
                <img src="/logos/placeholder.svg" alt="Microsoft" className="h-12 mx-auto" />
              </div>
              <p className="text-sm text-gray-600">Azure AD / Office 365</p>
            </div>
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-2">
                <img src="/logos/placeholder.svg" alt="Slack" className="h-12 mx-auto" />
              </div>
              <p className="text-sm text-gray-600">Slack</p>
            </div>
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-2">
                <img src="/logos/placeholder.svg" alt="Teams" className="h-12 mx-auto" />
              </div>
              <p className="text-sm text-gray-600">Microsoft Teams</p>
            </div>
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-2">
                <img src="/logos/placeholder.svg" alt="SAP" className="h-12 mx-auto" />
              </div>
              <p className="text-sm text-gray-600">SAP SuccessFactors</p>
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
            Ready to Build a Security-First Culture?
          </h2>
          <p className="text-lg text-blue-100 mb-8">
            Join 500+ organizations that have transformed their employees into their strongest defense
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/register" 
              className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-blue-600 bg-white rounded-lg hover:bg-gray-100 transition-colors"
            >
              Start 14-Day Free Trial
              <Zap className="ml-2 w-5 h-5" />
            </Link>
            <button className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white border-2 border-white rounded-lg hover:bg-white/10 transition-colors">
              Schedule Live Demo
              <Play className="ml-2 w-5 h-5" />
            </button>
          </div>
          <p className="mt-6 text-sm text-blue-100">
            No credit card required • Setup in 15 minutes • Cancel anytime
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
                Enterprise cybersecurity awareness training platform. Protecting organizations through education since 2020.
              </p>
              <div className="flex space-x-4">
                <a href="#" className="text-gray-400 hover:text-white">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z"/>
                  </svg>
                </a>
                <a href="#" className="text-gray-400 hover:text-white">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"/>
                  </svg>
                </a>
                <a href="#" className="text-gray-400 hover:text-white">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                </a>
              </div>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Integrations</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API Docs</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Resources</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Case Studies</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Webinars</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security Guide</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">About Us</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Partners</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <p className="text-gray-400 text-sm">
                &copy; 2024 Bootstrap Academy GmbH. All rights reserved.
              </p>
              <div className="flex space-x-6 mt-4 md:mt-0 text-sm">
                <a href="#" className="text-gray-400 hover:text-white transition-colors">Privacy Policy</a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">Terms of Service</a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">Impressum</a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">Cookie Settings</a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingEnhanced;