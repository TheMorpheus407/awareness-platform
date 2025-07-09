/**
 * Phishing campaign form component
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  Mail,
  Users,
  Calendar,
  Settings,
  AlertTriangle,
  ChevronRight,
  ChevronLeft,
  Plus,
  X
} from 'lucide-react';
import { phishingApi } from '../../services/phishingApi';
import { api } from '../../services';
import {
  PhishingTemplate,
  PhishingCampaignForm,
  CampaignTargetGroup,
  CampaignSettings,
  TemplateCategory
} from '../../types/phishing';
import LoadingSpinner from '../Common/LoadingSpinner';

interface Step {
  id: string;
  name: string;
  icon: React.ElementType;
}

const steps: Step[] = [
  { id: 'template', name: 'Select Template', icon: Mail },
  { id: 'recipients', name: 'Choose Recipients', icon: Users },
  { id: 'schedule', name: 'Schedule Campaign', icon: Calendar },
  { id: 'settings', name: 'Configure Settings', icon: Settings },
  { id: 'review', name: 'Review & Launch', icon: AlertTriangle }
];

const CampaignForm: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState<PhishingTemplate[]>([]);
  const [departments, setDepartments] = useState<string[]>([]);
  const [roles, setRoles] = useState<string[]>([]);

  const [formData, setFormData] = useState<PhishingCampaignForm>({
    name: '',
    description: '',
    template_id: 0,
    target_groups: [],
    scheduled_at: '',
    settings: {
      track_opens: true,
      track_clicks: true,
      capture_credentials: false,
      redirect_url: '',
      landing_page_url: '',
      training_url: '',
      send_rate_per_hour: 100,
      randomize_send_times: true
    }
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      // Load templates
      const templatesData = await phishingApi.getTemplates();
      setTemplates(templatesData);

      // Load departments and roles (mock data for now)
      setDepartments(['IT', 'HR', 'Finance', 'Sales', 'Marketing', 'Operations']);
      setRoles(['user', 'manager', 'admin']);
    } catch (err) {
      console.error('Failed to load initial data:', err);
      toast.error('Failed to load required data');
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    // Validate current step
    if (currentStep === 0 && !formData.template_id) {
      toast.error('Please select a template');
      return;
    }
    if (currentStep === 1 && formData.target_groups.length === 0) {
      toast.error('Please select at least one recipient group');
      return;
    }
    if (currentStep === 2 && !formData.name) {
      toast.error('Please enter a campaign name');
      return;
    }

    setCurrentStep((prev) => Math.min(prev + 1, steps.length - 1));
  };

  const handlePrevious = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const campaign = await phishingApi.createCampaign(formData);
      toast.success('Campaign created successfully!');
      navigate(`/phishing/campaigns/${campaign.id}`);
    } catch (err) {
      console.error('Failed to create campaign:', err);
      toast.error('Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  const addTargetGroup = (type: 'department' | 'role' | 'users', values: string[]) => {
    setFormData((prev) => ({
      ...prev,
      target_groups: [
        ...prev.target_groups,
        { type, value: values }
      ]
    }));
  };

  const removeTargetGroup = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      target_groups: prev.target_groups.filter((_, i) => i !== index)
    }));
  };

  const selectedTemplate = templates.find((t) => t.id === formData.template_id);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Create Phishing Campaign</h1>
        <p className="mt-1 text-sm text-gray-500">
          Set up a new phishing simulation to test your organization's security awareness
        </p>
      </div>

      {/* Progress Steps */}
      <nav aria-label="Progress" className="mb-8">
        <ol className="flex items-center justify-between">
          {steps.map((step, stepIdx) => {
            const StepIcon = step.icon;
            return (
              <li key={step.id} className="relative flex-1">
                {stepIdx !== steps.length - 1 && (
                  <div
                    className="absolute top-5 left-0 -ml-px mt-0.5 h-0.5 w-full bg-gray-300"
                    aria-hidden="true"
                  />
                )}
                <button
                  className={`group relative flex items-center justify-center ${
                    stepIdx <= currentStep ? 'cursor-pointer' : 'cursor-default'
                  }`}
                  onClick={() => stepIdx <= currentStep && setCurrentStep(stepIdx)}
                  disabled={stepIdx > currentStep}
                >
                  <span className="flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                    stepIdx < currentStep
                      ? 'border-blue-600 bg-blue-600'
                      : stepIdx === currentStep
                      ? 'border-blue-600 bg-white'
                      : 'border-gray-300 bg-white'
                  }">
                    <StepIcon
                      className={`h-5 w-5 ${
                        stepIdx < currentStep
                          ? 'text-white'
                          : stepIdx === currentStep
                          ? 'text-blue-600'
                          : 'text-gray-400'
                      }`}
                    />
                  </span>
                  <span className="absolute top-12 text-xs font-medium text-gray-500">
                    {step.name}
                  </span>
                </button>
              </li>
            );
          })}
        </ol>
      </nav>

      {/* Step Content */}
      <div className="bg-white shadow rounded-lg p-6">
        {currentStep === 0 && (
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">Select a Phishing Template</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className={`relative rounded-lg border p-4 cursor-pointer hover:border-blue-500 ${
                    formData.template_id === template.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300'
                  }`}
                  onClick={() => setFormData({ ...formData, template_id: template.id })}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-gray-900">{template.name}</h3>
                      <p className="mt-1 text-sm text-gray-500">{template.subject}</p>
                      <div className="mt-2 flex items-center space-x-2">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          {t(`phishing.category.${template.category}`)}
                        </span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          template.difficulty === 'easy'
                            ? 'bg-green-100 text-green-800'
                            : template.difficulty === 'medium'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {t(`phishing.difficulty.${template.difficulty}`)}
                        </span>
                      </div>
                    </div>
                    {formData.template_id === template.id && (
                      <div className="ml-2">
                        <div className="h-5 w-5 rounded-full bg-blue-600 flex items-center justify-center">
                          <svg className="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {currentStep === 1 && (
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">Choose Recipients</h2>
            
            {/* Target Groups */}
            <div className="space-y-4">
              {/* Add by Department */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">By Department</h3>
                <div className="flex flex-wrap gap-2">
                  {departments.map((dept) => {
                    const isSelected = formData.target_groups.some(
                      (group) => group.type === 'department' && group.value.includes(dept)
                    );
                    return (
                      <button
                        key={dept}
                        type="button"
                        onClick={() => {
                          if (!isSelected) {
                            addTargetGroup('department', [dept]);
                          }
                        }}
                        className={`inline-flex items-center px-3 py-1.5 border rounded-full text-sm font-medium ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                            : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                        disabled={isSelected}
                      >
                        {dept}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Add by Role */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">By Role</h3>
                <div className="flex flex-wrap gap-2">
                  {roles.map((role) => {
                    const isSelected = formData.target_groups.some(
                      (group) => group.type === 'role' && group.value.includes(role)
                    );
                    return (
                      <button
                        key={role}
                        type="button"
                        onClick={() => {
                          if (!isSelected) {
                            addTargetGroup('role', [role]);
                          }
                        }}
                        className={`inline-flex items-center px-3 py-1.5 border rounded-full text-sm font-medium ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                            : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                        disabled={isSelected}
                      >
                        {role}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Selected Groups */}
              {formData.target_groups.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Selected Groups</h3>
                  <div className="space-y-2">
                    {formData.target_groups.map((group, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div>
                          <span className="font-medium capitalize">{group.type}:</span>{' '}
                          {group.value.join(', ')}
                        </div>
                        <button
                          type="button"
                          onClick={() => removeTargetGroup(index)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Campaign Details</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Campaign Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Q1 2024 Security Awareness Test"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Description (Optional)
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Quarterly phishing awareness test for all departments..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Schedule Campaign (Optional)
              </label>
              <input
                type="datetime-local"
                value={formData.scheduled_at || ''}
                onChange={(e) => setFormData({ ...formData, scheduled_at: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
              <p className="mt-1 text-sm text-gray-500">
                Leave empty to save as draft and start manually later
              </p>
            </div>
          </div>
        )}

        {currentStep === 3 && (
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Campaign Settings</h2>
            
            {/* Tracking Options */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Tracking Options</h3>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.settings.track_opens}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        settings: { ...formData.settings, track_opens: e.target.checked }
                      })
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">Track email opens</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.settings.track_clicks}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        settings: { ...formData.settings, track_clicks: e.target.checked }
                      })
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">Track link clicks</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.settings.capture_credentials}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        settings: { ...formData.settings, capture_credentials: e.target.checked }
                      })
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Capture submitted credentials (not stored)
                  </span>
                </label>
              </div>
            </div>

            {/* Training URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Training URL (Optional)
              </label>
              <input
                type="url"
                value={formData.settings.training_url || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    settings: { ...formData.settings, training_url: e.target.value }
                  })
                }
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="https://training.example.com/phishing-awareness"
              />
              <p className="mt-1 text-sm text-gray-500">
                Users who click the phishing link will be redirected here
              </p>
            </div>

            {/* Send Rate */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Send Rate (emails per hour)
              </label>
              <input
                type="number"
                value={formData.settings.send_rate_per_hour || 100}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    settings: {
                      ...formData.settings,
                      send_rate_per_hour: parseInt(e.target.value) || 100
                    }
                  })
                }
                min="1"
                max="1000"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>

            {/* Randomize Send Times */}
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.settings.randomize_send_times}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    settings: { ...formData.settings, randomize_send_times: e.target.checked }
                  })
                }
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">
                Randomize send times to avoid detection
              </span>
            </label>
          </div>
        )}

        {currentStep === 4 && (
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">Review & Launch</h2>
            
            {/* Campaign Summary */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div>
                <span className="font-medium">Campaign Name:</span> {formData.name || 'Not set'}
              </div>
              {selectedTemplate && (
                <div>
                  <span className="font-medium">Template:</span> {selectedTemplate.name}
                </div>
              )}
              <div>
                <span className="font-medium">Target Groups:</span>{' '}
                {formData.target_groups.length} selected
              </div>
              <div>
                <span className="font-medium">Schedule:</span>{' '}
                {formData.scheduled_at
                  ? new Date(formData.scheduled_at).toLocaleString()
                  : 'Manual start (draft)'}
              </div>
              <div>
                <span className="font-medium">Tracking:</span>
                <ul className="mt-1 ml-4 text-sm text-gray-600">
                  {formData.settings.track_opens && <li>• Email opens</li>}
                  {formData.settings.track_clicks && <li>• Link clicks</li>}
                  {formData.settings.capture_credentials && <li>• Credential submissions</li>}
                </ul>
              </div>
            </div>

            <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">Important Notice</h3>
                  <p className="mt-1 text-sm text-yellow-700">
                    This campaign will send simulated phishing emails to the selected recipients.
                    Make sure you have proper authorization and have informed relevant stakeholders.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="mt-8 flex justify-between">
        <button
          type="button"
          onClick={handlePrevious}
          disabled={currentStep === 0}
          className={`inline-flex items-center px-4 py-2 border rounded-md shadow-sm text-sm font-medium ${
            currentStep === 0
              ? 'border-gray-300 text-gray-300 bg-gray-50 cursor-not-allowed'
              : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
          }`}
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Previous
        </button>

        {currentStep < steps.length - 1 ? (
          <button
            type="button"
            onClick={handleNext}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            Next
            <ChevronRight className="h-4 w-4 ml-2" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Campaign'}
          </button>
        )}
      </div>
    </div>
  );
};

export default CampaignForm;