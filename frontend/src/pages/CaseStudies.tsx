import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, Building, Users, Shield, TrendingUp, Download, Filter, ChevronRight } from 'lucide-react';

interface CaseStudy {
  id: number;
  title: string;
  company: string;
  industry: string;
  size: string;
  challenge: string;
  solution: string;
  results: string[];
  logo: string;
}

export const CaseStudies: React.FC = () => {
  const { t } = useTranslation();
  const [selectedIndustry, setSelectedIndustry] = useState('all');

  const caseStudies: CaseStudy[] = [
    {
      id: 1,
      title: t('caseStudies.studies.finance.title'),
      company: 'Global Finance Corp',
      industry: 'finance',
      size: '5000+',
      challenge: t('caseStudies.studies.finance.challenge'),
      solution: t('caseStudies.studies.finance.solution'),
      results: [
        t('caseStudies.studies.finance.result1'),
        t('caseStudies.studies.finance.result2'),
        t('caseStudies.studies.finance.result3')
      ],
      logo: '/case-studies/finance.png'
    },
    {
      id: 2,
      title: t('caseStudies.studies.healthcare.title'),
      company: 'MediCare Plus',
      industry: 'healthcare',
      size: '2500+',
      challenge: t('caseStudies.studies.healthcare.challenge'),
      solution: t('caseStudies.studies.healthcare.solution'),
      results: [
        t('caseStudies.studies.healthcare.result1'),
        t('caseStudies.studies.healthcare.result2'),
        t('caseStudies.studies.healthcare.result3')
      ],
      logo: '/case-studies/healthcare.png'
    },
    {
      id: 3,
      title: t('caseStudies.studies.tech.title'),
      company: 'TechInnovate GmbH',
      industry: 'technology',
      size: '1000+',
      challenge: t('caseStudies.studies.tech.challenge'),
      solution: t('caseStudies.studies.tech.solution'),
      results: [
        t('caseStudies.studies.tech.result1'),
        t('caseStudies.studies.tech.result2'),
        t('caseStudies.studies.tech.result3')
      ],
      logo: '/case-studies/tech.png'
    },
    {
      id: 4,
      title: t('caseStudies.studies.retail.title'),
      company: 'RetailChain International',
      industry: 'retail',
      size: '10000+',
      challenge: t('caseStudies.studies.retail.challenge'),
      solution: t('caseStudies.studies.retail.solution'),
      results: [
        t('caseStudies.studies.retail.result1'),
        t('caseStudies.studies.retail.result2'),
        t('caseStudies.studies.retail.result3')
      ],
      logo: '/case-studies/retail.png'
    }
  ];

  const industries = [
    { value: 'all', label: t('caseStudies.industries.all') },
    { value: 'finance', label: t('caseStudies.industries.finance') },
    { value: 'healthcare', label: t('caseStudies.industries.healthcare') },
    { value: 'technology', label: t('caseStudies.industries.technology') },
    { value: 'retail', label: t('caseStudies.industries.retail') }
  ];

  const filteredStudies = selectedIndustry === 'all' 
    ? caseStudies 
    : caseStudies.filter(study => study.industry === selectedIndustry);

  const stats = [
    { value: '95%', label: t('caseStudies.stats.reduction') },
    { value: '500+', label: t('caseStudies.stats.companies') },
    { value: '2M+', label: t('caseStudies.stats.users') },
    { value: '98%', label: t('caseStudies.stats.satisfaction') }
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
          <h1 className="text-4xl font-bold text-gray-900 mb-4">{t('caseStudies.title')}</h1>
          <p className="text-xl text-gray-600">
            {t('caseStudies.subtitle')}
          </p>
        </div>

        {/* Stats Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">{stat.value}</div>
                <p className="text-gray-600">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Filter Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Filter className="w-5 h-5 mr-2" />
              {t('caseStudies.filter')}
            </h2>
            <div className="flex gap-2">
              {industries.map((industry) => (
                <button
                  key={industry.value}
                  onClick={() => setSelectedIndustry(industry.value)}
                  className={`px-4 py-2 rounded-md transition-colors ${
                    selectedIndustry === industry.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {industry.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Case Studies Grid */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {filteredStudies.map((study) => (
            <div key={study.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">{study.title}</h3>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center">
                        <Building className="w-4 h-4 mr-1" />
                        {study.company}
                      </span>
                      <span className="flex items-center">
                        <Users className="w-4 h-4 mr-1" />
                        {study.size} {t('caseStudies.employees')}
                      </span>
                    </div>
                  </div>
                  <div className="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                    <Building className="w-8 h-8 text-gray-400" />
                  </div>
                </div>

                <div className="space-y-4 mb-4">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">{t('caseStudies.challenge')}</h4>
                    <p className="text-gray-700">{study.challenge}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">{t('caseStudies.solution')}</h4>
                    <p className="text-gray-700">{study.solution}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">{t('caseStudies.results')}</h4>
                    <ul className="space-y-1">
                      {study.results.map((result, index) => (
                        <li key={index} className="flex items-start">
                          <TrendingUp className="w-4 h-4 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                          <span className="text-gray-700">{result}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t">
                  <Link
                    to={`/case-studies/${study.id}`}
                    className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium"
                  >
                    {t('caseStudies.readMore')}
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Link>
                  <button className="inline-flex items-center text-gray-600 hover:text-gray-700">
                    <Download className="w-4 h-4 mr-1" />
                    {t('caseStudies.download')}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Success Factors */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('caseStudies.successFactors.title')}</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <Shield className="w-12 h-12 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">{t('caseStudies.successFactors.factor1')}</h3>
              <p className="text-gray-600">{t('caseStudies.successFactors.factor1Desc')}</p>
            </div>
            <div className="text-center">
              <Users className="w-12 h-12 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">{t('caseStudies.successFactors.factor2')}</h3>
              <p className="text-gray-600">{t('caseStudies.successFactors.factor2Desc')}</p>
            </div>
            <div className="text-center">
              <TrendingUp className="w-12 h-12 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">{t('caseStudies.successFactors.factor3')}</h3>
              <p className="text-gray-600">{t('caseStudies.successFactors.factor3Desc')}</p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="bg-blue-600 rounded-lg shadow-md p-8 text-white text-center">
          <h2 className="text-2xl font-bold mb-4">{t('caseStudies.cta.title')}</h2>
          <p className="mb-6">{t('caseStudies.cta.subtitle')}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/demo"
              className="inline-flex items-center justify-center px-6 py-3 bg-white text-blue-600 font-medium rounded-md hover:bg-gray-100 transition-colors"
            >
              {t('caseStudies.cta.demo')}
            </Link>
            <Link
              to="/contact"
              className="inline-flex items-center justify-center px-6 py-3 border-2 border-white text-white font-medium rounded-md hover:bg-white hover:text-blue-600 transition-colors"
            >
              {t('caseStudies.cta.contact')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};