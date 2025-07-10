import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, Play, Monitor, Shield, Mail, BarChart, Users, ChevronRight, CheckCircle } from 'lucide-react';

interface DemoStep {
  id: number;
  title: string;
  description: string;
  icon: React.FC<any>;
  screenshot: string;
}

const Demo: React.FC = () => {
  const { t } = useTranslation();
  const [activeStep, setActiveStep] = useState(0);
  const [showVideo, setShowVideo] = useState(false);

  const demoSteps: DemoStep[] = [
    {
      id: 1,
      title: t('demo.steps.dashboard.title'),
      description: t('demo.steps.dashboard.description'),
      icon: Monitor,
      screenshot: '/demo/dashboard.png'
    },
    {
      id: 2,
      title: t('demo.steps.phishing.title'),
      description: t('demo.steps.phishing.description'),
      icon: Mail,
      screenshot: '/demo/phishing.png'
    },
    {
      id: 3,
      title: t('demo.steps.training.title'),
      description: t('demo.steps.training.description'),
      icon: Shield,
      screenshot: '/demo/training.png'
    },
    {
      id: 4,
      title: t('demo.steps.analytics.title'),
      description: t('demo.steps.analytics.description'),
      icon: BarChart,
      screenshot: '/demo/analytics.png'
    },
    {
      id: 5,
      title: t('demo.steps.management.title'),
      description: t('demo.steps.management.description'),
      icon: Users,
      screenshot: '/demo/management.png'
    }
  ];

  const features = [
    { title: t('demo.features.realtime'), description: t('demo.features.realtimeDesc') },
    { title: t('demo.features.customizable'), description: t('demo.features.customizableDesc') },
    { title: t('demo.features.multilingual'), description: t('demo.features.multilingualDesc') },
    { title: t('demo.features.compliance'), description: t('demo.features.complianceDesc') },
    { title: t('demo.features.reporting'), description: t('demo.features.reportingDesc') },
    { title: t('demo.features.integration'), description: t('demo.features.integrationDesc') }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('common.back')}
        </Link>

        {/* Hero Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">{t('demo.title')}</h1>
          <p className="text-xl text-gray-600 mb-6">
            {t('demo.subtitle')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => setShowVideo(true)}
              className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
            >
              <Play className="w-5 h-5 mr-2" />
              {t('demo.watchVideo')}
            </button>
            <Link
              to="/register"
              className="inline-flex items-center justify-center px-6 py-3 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 transition-colors"
            >
              {t('demo.startTrial')}
              <ChevronRight className="w-5 h-5 ml-2" />
            </Link>
          </div>
        </div>

        {/* Interactive Demo */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('demo.interactive.title')}</h2>
          
          {/* Steps Navigation */}
          <div className="flex justify-between mb-8 overflow-x-auto">
            {demoSteps.map((step, index) => (
              <button
                key={step.id}
                onClick={() => setActiveStep(index)}
                className={`flex flex-col items-center p-4 min-w-[120px] transition-colors ${
                  activeStep === index
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <step.icon className="w-8 h-8 mb-2" />
                <span className="text-sm font-medium text-center">{step.title}</span>
              </button>
            ))}
          </div>

          {/* Active Step Content */}
          <div className="grid lg:grid-cols-2 gap-8">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                {demoSteps[activeStep].title}
              </h3>
              <p className="text-gray-700 mb-6">
                {demoSteps[activeStep].description}
              </p>
              <div className="space-y-3">
                <div className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('demo.interactive.point1')}</span>
                </div>
                <div className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('demo.interactive.point2')}</span>
                </div>
                <div className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{t('demo.interactive.point3')}</span>
                </div>
              </div>
            </div>
            <div className="bg-gray-200 rounded-lg h-96 flex items-center justify-center">
              <Monitor className="w-24 h-24 text-gray-400" />
            </div>
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8">
            <button
              onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
              disabled={activeStep === 0}
              className={`px-4 py-2 rounded-md ${
                activeStep === 0
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-600 text-white hover:bg-gray-700'
              }`}
            >
              {t('demo.previous')}
            </button>
            <button
              onClick={() => setActiveStep(Math.min(demoSteps.length - 1, activeStep + 1))}
              disabled={activeStep === demoSteps.length - 1}
              className={`px-4 py-2 rounded-md ${
                activeStep === demoSteps.length - 1
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {t('demo.next')}
            </button>
          </div>
        </div>

        {/* Key Features */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('demo.features.title')}</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-700">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-blue-600 rounded-lg shadow-md p-8 text-white text-center">
          <h2 className="text-2xl font-bold mb-4">{t('demo.cta.title')}</h2>
          <p className="mb-6">{t('demo.cta.subtitle')}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="inline-flex items-center justify-center px-6 py-3 bg-white text-blue-600 font-medium rounded-md hover:bg-gray-100 transition-colors"
            >
              {t('demo.cta.trial')}
            </Link>
            <Link
              to="/contact"
              className="inline-flex items-center justify-center px-6 py-3 border-2 border-white text-white font-medium rounded-md hover:bg-white hover:text-blue-600 transition-colors"
            >
              {t('demo.cta.contact')}
            </Link>
          </div>
        </div>

        {/* Video Modal */}
        {showVideo && (
          <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full">
              <div className="p-4 border-b flex justify-between items-center">
                <h3 className="text-lg font-semibold">{t('demo.video.title')}</h3>
                <button
                  onClick={() => setShowVideo(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ×
                </button>
              </div>
              <div className="aspect-video bg-gray-200 flex items-center justify-center">
                <Play className="w-24 h-24 text-gray-400" />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Demo;