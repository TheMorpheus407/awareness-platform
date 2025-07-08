import React, { useState } from 'react';
import { Tab } from '@headlessui/react';
import { BarChart3, TrendingUp, Users } from 'lucide-react';
import { MainLayout } from '../components/Layout';
import { 
  AnalyticsDashboard, 
  CourseAnalytics, 
  UserEngagementAnalytics 
} from '../components/Analytics';
import { useAuth } from '../hooks/useAuth';
import { useTranslation } from 'react-i18next';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

const Analytics: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [selectedIndex, setSelectedIndex] = useState(0);

  const tabs = [
    {
      name: t('analytics.dashboard.title'),
      icon: BarChart3,
      component: AnalyticsDashboard,
      allowedRoles: ['SUPER_ADMIN', 'ADMIN', 'MANAGER'],
    },
    {
      name: t('analytics.courseAnalytics.title'),
      icon: TrendingUp,
      component: CourseAnalytics,
      allowedRoles: ['SUPER_ADMIN', 'ADMIN', 'MANAGER'],
    },
    {
      name: t('analytics.userEngagement.title'),
      icon: Users,
      component: UserEngagementAnalytics,
      allowedRoles: ['SUPER_ADMIN', 'ADMIN', 'MANAGER', 'EMPLOYEE'],
    },
  ];

  // Filter tabs based on user role
  const availableTabs = tabs.filter(tab => 
    tab.allowedRoles.includes(user?.role || '')
  );

  return (
    <MainLayout>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <Tab.Group selectedIndex={selectedIndex} onChange={setSelectedIndex}>
            <div className="border-b border-gray-200 dark:border-gray-700">
              <Tab.List className="flex space-x-8" aria-label="Analytics tabs">
                {availableTabs.map((tab) => (
                  <Tab
                    key={tab.name}
                    className={({ selected }) =>
                      classNames(
                        'group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm',
                        selected
                          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                      )
                    }
                  >
                    {({ selected }) => (
                      <>
                        <tab.icon
                          className={classNames(
                            '-ml-0.5 mr-2 h-5 w-5',
                            selected
                              ? 'text-blue-500 dark:text-blue-400'
                              : 'text-gray-400 group-hover:text-gray-500 dark:text-gray-500 dark:group-hover:text-gray-400'
                          )}
                          aria-hidden="true"
                        />
                        <span>{tab.name}</span>
                      </>
                    )}
                  </Tab>
                ))}
              </Tab.List>
            </div>

            <Tab.Panels className="mt-6">
              {availableTabs.map((tab, idx) => (
                <Tab.Panel key={idx} className="focus:outline-none">
                  <tab.component />
                </Tab.Panel>
              ))}
            </Tab.Panels>
          </Tab.Group>
        </div>
      </div>
    </MainLayout>
  );
};

export default Analytics;