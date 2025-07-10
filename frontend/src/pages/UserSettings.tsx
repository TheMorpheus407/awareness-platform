import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { User, Shield, Bell, Globe, Palette } from 'lucide-react';
import { TwoFactorSetup } from '../components/Auth/TwoFactorSetup';
import { TwoFactorManagement } from '../components/Auth/TwoFactorManagement';
import { useAuth } from '../hooks/useAuth';

export const UserSettings: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [user2FAEnabled, setUser2FAEnabled] = useState(user?.has_2fa_enabled || false);

  const tabs = [
    { id: 'profile', label: t('userSettings.tabs.profile'), icon: User },
    { id: 'security', label: t('userSettings.tabs.security'), icon: Shield },
    { id: 'notifications', label: t('userSettings.tabs.notifications'), icon: Bell },
    { id: 'language', label: t('userSettings.tabs.language'), icon: Globe },
    { id: 'appearance', label: t('userSettings.tabs.appearance'), icon: Palette },
  ];

  const handle2FAStatusChange = () => {
    setUser2FAEnabled(!user2FAEnabled);
    setShow2FASetup(false);
  };

  return (
    <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">{t('userSettings.title')}</h1>
        
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:w-64">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeTab === tab.id
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="mr-3 h-5 w-5" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content Area */}
          <div className="flex-1">
            {activeTab === 'profile' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">{t('userSettings.profile.title')}</h2>
                
                <form className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('userSettings.profile.firstName')}
                      </label>
                      <input
                        type="text"
                        id="firstName"
                        defaultValue={user?.first_name}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    
                    <div>
                      <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('userSettings.profile.lastName')}
                      </label>
                      <input
                        type="text"
                        id="lastName"
                        defaultValue={user?.last_name}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('userSettings.profile.email')}
                    </label>
                    <input
                      type="email"
                      id="email"
                      defaultValue={user?.email}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('userSettings.profile.phone')}
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      defaultValue={user?.phone}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      {t('common.saveChanges')}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-6">
                {/* Password Change */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">{t('userSettings.security.changePassword')}</h2>
                  
                  <form className="space-y-4">
                    <div>
                      <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('userSettings.security.currentPassword')}
                      </label>
                      <input
                        type="password"
                        id="currentPassword"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>

                    <div>
                      <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('userSettings.security.newPassword')}
                      </label>
                      <input
                        type="password"
                        id="newPassword"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>

                    <div>
                      <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                        {t('userSettings.security.confirmNewPassword')}
                      </label>
                      <input
                        type="password"
                        id="confirmPassword"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>

                    <div className="flex justify-end">
                      <button
                        type="submit"
                        className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                      >
                        {t('userSettings.security.updatePassword')}
                      </button>
                    </div>
                  </form>
                </div>

                {/* 2FA Section */}
                {!show2FASetup ? (
                  <div>
                    {user2FAEnabled ? (
                      <TwoFactorManagement
                        isEnabled={user2FAEnabled}
                        onStatusChange={handle2FAStatusChange}
                      />
                    ) : (
                      <div className="bg-white rounded-lg shadow p-6">
                        <TwoFactorManagement
                          isEnabled={user2FAEnabled}
                          onStatusChange={handle2FAStatusChange}
                        />
                        <button
                          onClick={() => setShow2FASetup(true)}
                          className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                        >
                          {t('userSettings.security.enableTwoFactor')}
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <TwoFactorSetup
                    onComplete={handle2FAStatusChange}
                    onCancel={() => setShow2FASetup(false)}
                  />
                )}

                {/* Active Sessions */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('userSettings.security.activeSessions')}</h2>
                  <p className="text-gray-600 mb-4">
                    {t('userSettings.security.activeSessionsDescription')}
                  </p>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">{t('userSettings.security.currentDevice')}</p>
                        <p className="text-sm text-gray-600">{t('userSettings.security.deviceInfo', { browser: 'Chrome', os: 'Windows', location: 'Germany' })}</p>
                        <p className="text-xs text-gray-500">{t('userSettings.security.activeNow')}</p>
                      </div>
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">{t('common.active')}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">{t('userSettings.notifications.title')}</h2>
                
                <div className="space-y-4">
                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{t('userSettings.notifications.emailNotifications')}</p>
                      <p className="text-sm text-gray-600">{t('userSettings.notifications.emailNotificationsDescription')}</p>
                    </div>
                    <input
                      type="checkbox"
                      defaultChecked
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                  </label>

                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{t('userSettings.notifications.securityAlerts')}</p>
                      <p className="text-sm text-gray-600">{t('userSettings.notifications.securityAlertsDescription')}</p>
                    </div>
                    <input
                      type="checkbox"
                      defaultChecked
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                  </label>

                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{t('userSettings.notifications.courseReminders')}</p>
                      <p className="text-sm text-gray-600">{t('userSettings.notifications.courseRemindersDescription')}</p>
                    </div>
                    <input
                      type="checkbox"
                      defaultChecked
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                  </label>
                </div>

                <div className="mt-6 flex justify-end">
                  <button className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                    {t('userSettings.notifications.savePreferences')}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'language' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">{t('userSettings.languageRegion.title')}</h2>
                
                <div className="space-y-4">
                  <div>
                    <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('userSettings.languageRegion.preferredLanguage')}
                    </label>
                    <select
                      id="language"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      defaultValue="en"
                    >
                      <option value="en">English</option>
                      <option value="de">Deutsch</option>
                      <option value="fr">Français</option>
                      <option value="es">Español</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="timezone" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('userSettings.languageRegion.timezone')}
                    </label>
                    <select
                      id="timezone"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      defaultValue="Europe/Berlin"
                    >
                      <option value="Europe/Berlin">Europe/Berlin (GMT+1)</option>
                      <option value="Europe/London">Europe/London (GMT)</option>
                      <option value="America/New_York">America/New York (GMT-5)</option>
                      <option value="Asia/Tokyo">Asia/Tokyo (GMT+9)</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="dateFormat" className="block text-sm font-medium text-gray-700 mb-2">
                      {t('userSettings.languageRegion.dateFormat')}
                    </label>
                    <select
                      id="dateFormat"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      defaultValue="DD/MM/YYYY"
                    >
                      <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                      <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                      <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                    </select>
                  </div>
                </div>

                <div className="mt-6 flex justify-end">
                  <button className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                    {t('common.saveChanges')}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'appearance' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">{t('userSettings.appearance.title')}</h2>
                
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-3">{t('userSettings.appearance.theme')}</h3>
                    <div className="grid grid-cols-3 gap-3">
                      <label className="cursor-pointer">
                        <input type="radio" name="theme" value="light" defaultChecked className="sr-only" />
                        <div className="p-4 border-2 border-indigo-500 rounded-lg text-center">
                          <div className="w-12 h-12 bg-white border border-gray-300 rounded mx-auto mb-2"></div>
                          <p className="text-sm font-medium">{t('userSettings.appearance.light')}</p>
                        </div>
                      </label>
                      
                      <label className="cursor-pointer">
                        <input type="radio" name="theme" value="dark" className="sr-only" />
                        <div className="p-4 border-2 border-gray-300 rounded-lg text-center hover:border-gray-400">
                          <div className="w-12 h-12 bg-gray-800 rounded mx-auto mb-2"></div>
                          <p className="text-sm font-medium">{t('userSettings.appearance.dark')}</p>
                        </div>
                      </label>
                      
                      <label className="cursor-pointer">
                        <input type="radio" name="theme" value="auto" className="sr-only" />
                        <div className="p-4 border-2 border-gray-300 rounded-lg text-center hover:border-gray-400">
                          <div className="w-12 h-12 bg-gradient-to-r from-white to-gray-800 rounded mx-auto mb-2"></div>
                          <p className="text-sm font-medium">{t('userSettings.appearance.auto')}</p>
                        </div>
                      </label>
                    </div>
                  </div>

                  <div>
                    <label className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{t('userSettings.appearance.compactMode')}</p>
                        <p className="text-sm text-gray-600">{t('userSettings.appearance.compactModeDescription')}</p>
                      </div>
                      <input
                        type="checkbox"
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                    </label>
                  </div>
                </div>

                <div className="mt-6 flex justify-end">
                  <button className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                    {t('userSettings.notifications.savePreferences')}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
  );
};