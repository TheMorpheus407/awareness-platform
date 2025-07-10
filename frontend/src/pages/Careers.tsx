import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, Briefcase, MapPin, Clock, Users, Heart, Trophy, Coffee } from 'lucide-react';

interface JobListing {
  id: number;
  title: string;
  department: string;
  location: string;
  type: string;
  description: string;
}

export const Careers: React.FC = () => {
  const { t } = useTranslation();

  const jobListings: JobListing[] = [
    {
      id: 1,
      title: t('careers.jobs.backend.title'),
      department: t('careers.jobs.backend.department'),
      location: 'Berlin, Germany',
      type: t('careers.jobs.fullTime'),
      description: t('careers.jobs.backend.description')
    },
    {
      id: 2,
      title: t('careers.jobs.security.title'),
      department: t('careers.jobs.security.department'),
      location: 'Remote',
      type: t('careers.jobs.fullTime'),
      description: t('careers.jobs.security.description')
    },
    {
      id: 3,
      title: t('careers.jobs.sales.title'),
      department: t('careers.jobs.sales.department'),
      location: 'Munich, Germany',
      type: t('careers.jobs.fullTime'),
      description: t('careers.jobs.sales.description')
    },
    {
      id: 4,
      title: t('careers.jobs.content.title'),
      department: t('careers.jobs.content.department'),
      location: 'Remote',
      type: t('careers.jobs.partTime'),
      description: t('careers.jobs.content.description')
    }
  ];

  const benefits = [
    { icon: Heart, title: t('careers.benefits.health'), description: t('careers.benefits.healthDesc') },
    { icon: Trophy, title: t('careers.benefits.growth'), description: t('careers.benefits.growthDesc') },
    { icon: Users, title: t('careers.benefits.team'), description: t('careers.benefits.teamDesc') },
    { icon: Coffee, title: t('careers.benefits.balance'), description: t('careers.benefits.balanceDesc') }
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
          <h1 className="text-4xl font-bold text-gray-900 mb-4">{t('careers.title')}</h1>
          <p className="text-xl text-gray-600">
            {t('careers.subtitle')}
          </p>
        </div>

        {/* Why Join Us */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('careers.whyJoin.title')}</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('careers.whyJoin.mission')}</h3>
              <p className="text-gray-700 mb-4">
                {t('careers.whyJoin.missionText')}
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('careers.whyJoin.culture')}</h3>
              <p className="text-gray-700 mb-4">
                {t('careers.whyJoin.cultureText')}
              </p>
            </div>
          </div>
        </div>

        {/* Benefits */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('careers.benefits.title')}</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {benefits.map((benefit, index) => (
              <div key={index} className="text-center">
                <benefit.icon className="w-12 h-12 text-blue-600 mx-auto mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">{benefit.title}</h3>
                <p className="text-gray-600 text-sm">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Open Positions */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('careers.openPositions')}</h2>
          <div className="space-y-6">
            {jobListings.map((job) => (
              <div key={job.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">{job.title}</h3>
                    <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-3">
                      <span className="flex items-center">
                        <Briefcase className="w-4 h-4 mr-1" />
                        {job.department}
                      </span>
                      <span className="flex items-center">
                        <MapPin className="w-4 h-4 mr-1" />
                        {job.location}
                      </span>
                      <span className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        {job.type}
                      </span>
                    </div>
                    <p className="text-gray-700">{job.description}</p>
                  </div>
                  <Link
                    to={`/careers/${job.id}`}
                    className="mt-4 md:mt-0 md:ml-4 inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
                  >
                    {t('careers.apply')}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Application Process */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('careers.process.title')}</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 font-bold">
                1
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('careers.process.step1')}</h3>
              <p className="text-gray-600 text-sm">{t('careers.process.step1Desc')}</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 font-bold">
                2
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('careers.process.step2')}</h3>
              <p className="text-gray-600 text-sm">{t('careers.process.step2Desc')}</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 font-bold">
                3
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('careers.process.step3')}</h3>
              <p className="text-gray-600 text-sm">{t('careers.process.step3Desc')}</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 font-bold">
                4
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('careers.process.step4')}</h3>
              <p className="text-gray-600 text-sm">{t('careers.process.step4Desc')}</p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="bg-blue-600 rounded-lg shadow-md p-8 text-white text-center">
          <h2 className="text-2xl font-bold mb-4">{t('careers.cta.title')}</h2>
          <p className="mb-6">{t('careers.cta.subtitle')}</p>
          <a
            href="mailto:careers@bootstrap-academy.com"
            className="inline-flex items-center px-6 py-3 bg-white text-blue-600 font-medium rounded-md hover:bg-gray-100 transition-colors"
          >
            {t('careers.cta.email')}
          </a>
        </div>
      </div>
    </div>
  );
};