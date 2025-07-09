/**
 * Phishing template library component
 */

import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Search,
  Filter,
  Mail,
  Shield,
  AlertTriangle,
  Globe,
  Lock,
  Eye,
  Edit,
  Copy,
  Trash2,
  Plus
} from 'lucide-react';
import { phishingApi } from '../../services/phishingApi';
import type { PhishingTemplate, TemplateCategory, TemplateDifficulty } from '../../types/phishing';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import Modal from '../ui/Modal';

const TemplateLibrary: React.FC = () => {
  const { t } = useTranslation();
  const [templates, setTemplates] = useState<PhishingTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<TemplateCategory | 'all'>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<TemplateDifficulty | 'all'>('all');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [showPublicOnly, setShowPublicOnly] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState<PhishingTemplate | null>(null);

  useEffect(() => {
    loadTemplates();
  }, [selectedCategory, selectedDifficulty, selectedLanguage, showPublicOnly]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const params: any = {};
      
      if (selectedCategory !== 'all') {
        params.categories = [selectedCategory];
      }
      if (selectedDifficulty !== 'all') {
        params.difficulties = [selectedDifficulty];
      }
      if (selectedLanguage !== 'all') {
        params.languages = [selectedLanguage];
      }
      if (showPublicOnly) {
        params.is_public = true;
      }
      
      const data = await phishingApi.getTemplates(params);
      setTemplates(data);
    } catch (err) {
      setError(t('phishing.templates.loadError'));
      console.error('Failed to load templates:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTemplate = async (id: number) => {
    if (window.confirm(t('phishing.templates.confirmDelete'))) {
      try {
        await phishingApi.deleteTemplate(id);
        await loadTemplates();
      } catch (err) {
        console.error('Failed to delete template:', err);
      }
    }
  };

  const getDifficultyColor = (difficulty: TemplateDifficulty) => {
    switch (difficulty) {
      case TemplateDifficulty.EASY:
        return 'bg-green-100 text-green-800';
      case TemplateDifficulty.MEDIUM:
        return 'bg-yellow-100 text-yellow-800';
      case TemplateDifficulty.HARD:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryIcon = (category: TemplateCategory) => {
    switch (category) {
      case TemplateCategory.CREDENTIAL_HARVESTING:
        return Lock;
      case TemplateCategory.MALWARE:
        return AlertTriangle;
      case TemplateCategory.BUSINESS_EMAIL_COMPROMISE:
        return Mail;
      case TemplateCategory.SOCIAL_ENGINEERING:
        return Shield;
      default:
        return Mail;
    }
  };

  const filteredTemplates = templates.filter(template =>
    template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.subject.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-lg">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('phishing.templates.title')}</h1>
          <p className="mt-1 text-sm text-gray-500">{t('phishing.templates.subtitle')}</p>
        </div>
        <button className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
          <Plus className="h-4 w-4 mr-2" />
          {t('phishing.templates.create')}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {/* Search */}
          <div className="lg:col-span-2">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder={t('phishing.templates.search')}
              />
            </div>
          </div>

          {/* Category Filter */}
          <div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as TemplateCategory | 'all')}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              <option value="all">{t('phishing.templates.allCategories')}</option>
              {Object.values(TemplateCategory).map(category => (
                <option key={category} value={category}>
                  {t(`phishing.category.${category}`)}
                </option>
              ))}
            </select>
          </div>

          {/* Difficulty Filter */}
          <div>
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value as TemplateDifficulty | 'all')}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              <option value="all">{t('phishing.templates.allDifficulties')}</option>
              {Object.values(TemplateDifficulty).map(difficulty => (
                <option key={difficulty} value={difficulty}>
                  {t(`phishing.difficulty.${difficulty}`)}
                </option>
              ))}
            </select>
          </div>

          {/* Language Filter */}
          <div>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              <option value="all">{t('phishing.templates.allLanguages')}</option>
              <option value="en">English</option>
              <option value="de">Deutsch</option>
            </select>
          </div>
        </div>

        {/* Public Only Toggle */}
        <div className="mt-4 flex items-center">
          <input
            id="public-only"
            type="checkbox"
            checked={showPublicOnly}
            onChange={(e) => setShowPublicOnly(e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="public-only" className="ml-2 block text-sm text-gray-900">
            {t('phishing.templates.publicOnly')}
          </label>
        </div>
      </div>

      {/* Template Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredTemplates.map((template) => {
          const CategoryIcon = getCategoryIcon(template.category);
          
          return (
            <div
              key={template.id}
              className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <CategoryIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <span className="text-sm text-gray-500">
                      {t(`phishing.category.${template.category}`)}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDifficultyColor(
                        template.difficulty
                      )}`}
                    >
                      {t(`phishing.difficulty.${template.difficulty}`)}
                    </span>
                    {template.is_public && (
                      <Globe className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                </div>

                <h3 className="text-lg font-medium text-gray-900 mb-2">{template.name}</h3>
                <p className="text-sm text-gray-600 mb-2">
                  <strong>{t('phishing.templates.subject')}:</strong> {template.subject}
                </p>
                <p className="text-sm text-gray-600 mb-4">
                  <strong>{t('phishing.templates.sender')}:</strong> {template.sender_name} ({template.sender_email})
                </p>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    {t('phishing.templates.language')}: {template.language.toUpperCase()}
                  </span>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setPreviewTemplate(template)}
                      className="text-gray-400 hover:text-gray-500"
                      title={t('phishing.templates.preview')}
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <button
                      className="text-gray-400 hover:text-gray-500"
                      title={t('phishing.templates.duplicate')}
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                    {!template.is_public && (
                      <>
                        <button
                          className="text-gray-400 hover:text-gray-500"
                          title={t('phishing.templates.edit')}
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteTemplate(template.id)}
                          className="text-red-400 hover:text-red-500"
                          title={t('phishing.templates.delete')}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <Mail className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            {t('phishing.templates.noTemplates')}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {t('phishing.templates.noTemplatesDescription')}
          </p>
        </div>
      )}

      {/* Preview Modal */}
      {previewTemplate && (
        <Modal
          isOpen={true}
          onClose={() => setPreviewTemplate(null)}
          title={t('phishing.templates.previewTitle')}
        >
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-900">{t('phishing.templates.subject')}</h4>
              <p className="mt-1 text-sm text-gray-600">{previewTemplate.subject}</p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-900">{t('phishing.templates.from')}</h4>
              <p className="mt-1 text-sm text-gray-600">
                {previewTemplate.sender_name} &lt;{previewTemplate.sender_email}&gt;
              </p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-900">{t('phishing.templates.content')}</h4>
              <div
                className="mt-1 prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: previewTemplate.html_content }}
              />
            </div>
            {previewTemplate.landing_page_html && (
              <div>
                <h4 className="text-sm font-medium text-gray-900">{t('phishing.templates.landingPage')}</h4>
                <div
                  className="mt-1 prose prose-sm max-w-none border border-gray-200 rounded p-4"
                  dangerouslySetInnerHTML={{ __html: previewTemplate.landing_page_html }}
                />
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};

export default TemplateLibrary;