import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, Users, Target, Award, Shield, CheckCircle, Globe, Heart } from 'lucide-react';

export const About: React.FC = () => {
  const { t } = useTranslation();

  const values = [
    { icon: Shield, title: t('about.values.security'), description: t('about.values.securityDesc') },
    { icon: Users, title: t('about.values.people'), description: t('about.values.peopleDesc') },
    { icon: Target, title: t('about.values.innovation'), description: t('about.values.innovationDesc') },
    { icon: Heart, title: t('about.values.trust'), description: t('about.values.trustDesc') },
  ];

  const team = [
    { name: 'Dr. Max Mustermann', role: t('about.team.ceo'), image: '/team/ceo.jpg' },
    { name: 'Sarah Schmidt', role: t('about.team.cto'), image: '/team/cto.jpg' },
    { name: 'Michael Weber', role: t('about.team.cso'), image: '/team/cso.jpg' },
    { name: 'Lisa Müller', role: t('about.team.cmo'), image: '/team/cmo.jpg' },
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
          <h1 className="text-4xl font-bold text-gray-900 mb-4">{t('about.title')}</h1>
          <p className="text-xl text-gray-600 leading-relaxed">
            {t('about.subtitle')}
          </p>
        </div>

        {/* Mission Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Target className="w-8 h-8 mr-3 text-blue-600" />
            {t('about.mission.title')}
          </h2>
          <p className="text-lg text-gray-700 leading-relaxed mb-6">
            {t('about.mission.description')}
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">50K+</div>
              <p className="text-gray-600">{t('about.stats.usersProtected')}</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">500+</div>
              <p className="text-gray-600">{t('about.stats.companiesServed')}</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">98%</div>
              <p className="text-gray-600">{t('about.stats.satisfaction')}</p>
            </div>
          </div>
        </div>

        {/* Values Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('about.values.title')}</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {values.map((value, index) => (
              <div key={index} className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <value.icon className="w-12 h-12 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{value.title}</h3>
                  <p className="text-gray-700">{value.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Team Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('about.team.title')}</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {team.map((member, index) => (
              <div key={index} className="text-center">
                <div className="w-32 h-32 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <Users className="w-16 h-16 text-gray-400" />
                </div>
                <h3 className="font-semibold text-gray-900">{member.name}</h3>
                <p className="text-gray-600">{member.role}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Awards Section */}
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Award className="w-8 h-8 mr-3 text-blue-600" />
            {t('about.awards.title')}
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center p-6 border border-gray-200 rounded-lg">
              <Award className="w-12 h-12 text-yellow-500 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">{t('about.awards.security')}</h3>
              <p className="text-gray-600">2024</p>
            </div>
            <div className="text-center p-6 border border-gray-200 rounded-lg">
              <Globe className="w-12 h-12 text-blue-500 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">{t('about.awards.innovation')}</h3>
              <p className="text-gray-600">2023</p>
            </div>
            <div className="text-center p-6 border border-gray-200 rounded-lg">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">{t('about.awards.compliance')}</h3>
              <p className="text-gray-600">ISO 27001</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};