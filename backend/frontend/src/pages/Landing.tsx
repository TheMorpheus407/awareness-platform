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
  FileCheck
} from 'lucide-react';
import { LanguageSwitcher } from '../components/Common';
import { useScrollAnimation } from '../hooks/useScrollAnimation';

const Landing = () => {
  const { t } = useTranslation();
  
  // Animation hooks for different sections
  const heroAnimation = useScrollAnimation();
  const featuresAnimation = useScrollAnimation();
  const benefitsAnimation = useScrollAnimation();
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

  const features = [
    {
      icon: <Mail className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.phishing.title'),
      description: t('landing.features.phishing.description')
    },
    {
      icon: <Globe className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.training.title'),
      description: t('landing.features.training.description')
    },
    {
      icon: <BarChart3 className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.analytics.title'),
      description: t('landing.features.analytics.description')
    },
    {
      icon: <FileCheck className="w-8 h-8 text-blue-600" />,
      title: t('landing.features.compliance.title'),
      description: t('landing.features.compliance.description')
    }
  ];

  const benefits = [
    {
      title: t('landing.benefits.reduce.title'),
      description: t('landing.benefits.reduce.description'),
      stat: '90%'
    },
    {
      title: t('landing.benefits.improve.title'),
      description: t('landing.benefits.improve.description'),
      stat: '73%'
    },
    {
      title: t('landing.benefits.save.title'),
      description: t('landing.benefits.save.description'),
      stat: '€4.5M'
    }
  ];

  const pricingTiers = [
    {
      name: t('landing.pricing.starter.name'),
      price: t('landing.pricing.starter.price'),
      description: t('landing.pricing.starter.description'),
      features: [
        t('landing.pricing.starter.feature1'),
        t('landing.pricing.starter.feature2'),
        t('landing.pricing.starter.feature3'),
        t('landing.pricing.starter.feature4')
      ],
      cta: t('landing.pricing.starter.cta'),
      popular: false
    },
    {
      name: t('landing.pricing.professional.name'),
      price: t('landing.pricing.professional.price'),
      description: t('landing.pricing.professional.description'),
      features: [
        t('landing.pricing.professional.feature1'),
        t('landing.pricing.professional.feature2'),
        t('landing.pricing.professional.feature3'),
        t('landing.pricing.professional.feature4'),
        t('landing.pricing.professional.feature5')
      ],
      cta: t('landing.pricing.professional.cta'),
      popular: true
    },
    {
      name: t('landing.pricing.enterprise.name'),
      price: t('landing.pricing.enterprise.price'),
      description: t('landing.pricing.enterprise.description'),
      features: [
        t('landing.pricing.enterprise.feature1'),
        t('landing.pricing.enterprise.feature2'),
        t('landing.pricing.enterprise.feature3'),
        t('landing.pricing.enterprise.feature4'),
        t('landing.pricing.enterprise.feature5')
      ],
      cta: t('landing.pricing.enterprise.cta'),
      popular: false
    }
  ];

  const testimonials = [
    {
      content: t('landing.testimonials.testimonial1.content'),
      author: t('landing.testimonials.testimonial1.author'),
      role: t('landing.testimonials.testimonial1.role'),
      company: t('landing.testimonials.testimonial1.company'),
      rating: 5
    },
    {
      content: t('landing.testimonials.testimonial2.content'),
      author: t('landing.testimonials.testimonial2.author'),
      role: t('landing.testimonials.testimonial2.role'),
      company: t('landing.testimonials.testimonial2.company'),
      rating: 5
    },
    {
      content: t('landing.testimonials.testimonial3.content'),
      author: t('landing.testimonials.testimonial3.author'),
      role: t('landing.testimonials.testimonial3.role'),
      company: t('landing.testimonials.testimonial3.company'),
      rating: 5
    }
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
            <div className="flex items-center space-x-6">
              <LanguageSwitcher />
              <Link to="/login" className="text-gray-600 hover:text-gray-900 transition-colors">
                {t('auth.login.signIn')}
              </Link>
              <Link 
                to="/register" 
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                {t('landing.nav.startFree')}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section 
        ref={heroAnimation.ref as React.RefObject<HTMLElement>}
        className={`pt-24 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-white transition-all duration-1000 ${
          heroAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
              {t('landing.hero.title')}
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              {t('landing.hero.subtitle')}
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link 
                to="/register" 
                className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                {t('landing.hero.cta.primary')}
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
              <a 
                href="#features" 
                onClick={(e) => handleSmoothScroll(e, 'features')}
                className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-blue-600 border-2 border-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
              >
                {t('landing.hero.cta.secondary')}
              </a>
            </div>
            <div className="mt-12 flex items-center justify-center space-x-8">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-gray-600">{t('landing.hero.badge1')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-gray-600">{t('landing.hero.badge2')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-gray-600">{t('landing.hero.badge3')}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section 
        ref={featuresAnimation.ref as React.RefObject<HTMLElement>}
        id="features" 
        className={`py-16 px-4 sm:px-6 lg:px-8 transition-all duration-1000 delay-200 ${
          featuresAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.features.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('landing.features.subtitle')}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index} 
                className="feature-card bg-white p-6 rounded-xl shadow-lg hover:shadow-xl"
              >
                <div className="mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section 
        ref={benefitsAnimation.ref as React.RefObject<HTMLElement>}
        className={`py-16 px-4 sm:px-6 lg:px-8 bg-gray-50 transition-all duration-1000 delay-300 ${
          benefitsAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.benefits.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('landing.benefits.subtitle')}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {benefits.map((benefit, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl font-bold text-blue-600 mb-2">{benefit.stat}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{benefit.title}</h3>
                <p className="text-gray-600">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section 
        ref={pricingAnimation.ref as React.RefObject<HTMLElement>}
        id="pricing" 
        className={`py-16 px-4 sm:px-6 lg:px-8 transition-all duration-1000 delay-400 ${
          pricingAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.pricing.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('landing.pricing.subtitle')}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {pricingTiers.map((tier, index) => (
              <div 
                key={index} 
                className={`pricing-card relative bg-white rounded-xl shadow-lg p-8 ${
                  tier.popular ? 'ring-2 ring-blue-600' : ''
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-5 left-1/2 transform -translate-x-1/2">
                    <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                      {t('landing.pricing.popular')}
                    </span>
                  </div>
                )}
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{tier.name}</h3>
                  <div className="text-4xl font-bold text-blue-600 mb-2">{tier.price}</div>
                  <p className="text-gray-600">{tier.description}</p>
                </div>
                <ul className="space-y-4 mb-8">
                  {tier.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start">
                      <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Link 
                  to="/register" 
                  className={`block w-full text-center py-3 px-6 rounded-lg font-medium transition-colors ${
                    tier.popular 
                      ? 'bg-blue-600 text-white hover:bg-blue-700' 
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section 
        ref={testimonialsAnimation.ref as React.RefObject<HTMLElement>}
        className={`py-16 px-4 sm:px-6 lg:px-8 bg-gray-50 transition-all duration-1000 delay-500 ${
          testimonialsAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.testimonials.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('landing.testimonials.subtitle')}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-gray-700 mb-4 italic">"{testimonial.content}"</p>
                <div className="border-t pt-4">
                  <p className="font-semibold text-gray-900">{testimonial.author}</p>
                  <p className="text-sm text-gray-600">{testimonial.role}</p>
                  <p className="text-sm text-gray-600">{testimonial.company}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security Section */}
      <section 
        ref={securityAnimation.ref as React.RefObject<HTMLElement>}
        className={`py-16 px-4 sm:px-6 lg:px-8 transition-all duration-1000 delay-600 ${
          securityAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="bg-blue-600 rounded-2xl p-8 md:p-12 text-white">
            <div className="text-center">
              <Lock className="w-16 h-16 mx-auto mb-4" />
              <h2 className="text-3xl font-bold mb-4">{t('landing.security.title')}</h2>
              <p className="text-lg mb-8 max-w-2xl mx-auto">
                {t('landing.security.subtitle')}
              </p>
              <div className="flex flex-wrap justify-center gap-8">
                <div className="flex items-center space-x-2">
                  <Award className="w-8 h-8" />
                  <span className="font-medium">ISO 27001</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Award className="w-8 h-8" />
                  <span className="font-medium">GDPR Compliant</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Award className="w-8 h-8" />
                  <span className="font-medium">SOC 2 Type II</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section 
        ref={ctaAnimation.ref as React.RefObject<HTMLElement>}
        className={`py-16 px-4 sm:px-6 lg:px-8 bg-gray-50 transition-all duration-1000 delay-700 ${
          ctaAnimation.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            {t('landing.cta.title')}
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            {t('landing.cta.subtitle')}
          </p>
          <Link 
            to="/register" 
            className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            {t('landing.cta.button')}
            <Zap className="ml-2 w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Shield className="w-8 h-8 text-blue-400" />
                <span className="text-xl font-bold">Bootstrap Academy</span>
              </div>
              <p className="text-gray-400">
                {t('landing.footer.description')}
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-4">{t('landing.footer.product')}</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" onClick={(e) => handleSmoothScroll(e, 'features')} className="hover:text-white transition-colors">{t('landing.footer.features')}</a></li>
                <li><a href="#pricing" onClick={(e) => handleSmoothScroll(e, 'pricing')} className="hover:text-white transition-colors">{t('landing.footer.pricing')}</a></li>
                <li><Link to="/login" className="hover:text-white transition-colors">{t('landing.footer.login')}</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">{t('landing.footer.company')}</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">{t('landing.footer.about')}</a></li>
                <li><a href="#" className="hover:text-white transition-colors">{t('landing.footer.contact')}</a></li>
                <li><a href="#" className="hover:text-white transition-colors">{t('landing.footer.careers')}</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">{t('landing.footer.legal')}</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">{t('landing.footer.privacy')}</a></li>
                <li><a href="#" className="hover:text-white transition-colors">{t('landing.footer.terms')}</a></li>
                <li><a href="#" className="hover:text-white transition-colors">{t('landing.footer.impressum')}</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Bootstrap Academy. {t('landing.footer.rights')}</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;