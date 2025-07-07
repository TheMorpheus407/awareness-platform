import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Building,
  GraduationCap,
  Mail,
  FileBarChart,
  Settings,
  Shield,
  X,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const { t } = useTranslation();

  const navigation = [
    { nameKey: 'navigation.dashboard', href: '/dashboard', icon: LayoutDashboard },
    { nameKey: 'navigation.users', href: '/users', icon: Users, adminOnly: true },
    { nameKey: 'navigation.companies', href: '/companies', icon: Building, adminOnly: true },
    { nameKey: 'navigation.courses', href: '/courses', icon: GraduationCap },
    { nameKey: 'navigation.phishing', href: '/phishing', icon: Mail },
    { nameKey: 'navigation.reports', href: '/reports', icon: FileBarChart },
    { nameKey: 'navigation.settings', href: '/settings', icon: Settings },
  ];

  const filteredNavigation = navigation.filter(
    (item) => !item.adminOnly || user?.role === 'admin'
  );

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-secondary-200 transform transition-transform duration-300 ease-in-out lg:transform-none lg:static lg:inset-0',
          {
            'translate-x-0': isOpen,
            '-translate-x-full lg:translate-x-0': !isOpen,
          }
        )}
      >
        <div className="flex items-center justify-between h-16 px-6 border-b border-secondary-200">
          <div className="flex items-center">
            <Shield className="w-8 h-8 text-primary-600 mr-2" />
            <span className="text-xl font-bold text-secondary-900">{t('branding.appName')}</span>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-2 rounded-md text-secondary-500 hover:text-secondary-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="mt-6 px-3">
          {filteredNavigation.map((item) => (
            <NavLink
              key={item.nameKey}
              to={item.href}
              className={({ isActive }) =>
                clsx(
                  'flex items-center px-3 py-2 mb-1 text-sm font-medium rounded-lg transition-colors duration-200',
                  {
                    'bg-primary-100 text-primary-900': isActive,
                    'text-secondary-600 hover:bg-secondary-100 hover:text-secondary-900': !isActive,
                  }
                )
              }
              onClick={() => window.innerWidth < 1024 && onClose()}
            >
              <item.icon className="w-5 h-5 mr-3" />
              {t(item.nameKey)}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-secondary-200">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center text-white font-semibold">
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-secondary-900">{user?.full_name}</p>
              <p className="text-xs text-secondary-500">{user?.email}</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};