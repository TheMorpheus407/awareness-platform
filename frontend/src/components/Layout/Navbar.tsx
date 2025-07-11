import React from 'react';
import { Menu, LogOut } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LanguageSwitcher } from '../Common';
import { NotificationCenter } from '../Notifications';

interface NavbarProps {
  onMenuClick: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onMenuClick }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white border-b border-secondary-200 h-16 flex items-center justify-between px-4 lg:px-6" role="navigation" aria-label={t('navigation.mainNav')}>
      <button
        onClick={onMenuClick}
        className="lg:hidden p-2 rounded-md text-secondary-500 hover:text-secondary-700"
        aria-label={t('navigation.toggleMenu')}
        aria-expanded="false"
        aria-controls="main-menu"
      >
        <Menu className="w-6 h-6" aria-hidden="true" />
      </button>

      <div className="flex-1" />

      <div className="flex items-center space-x-4">
        <LanguageSwitcher />
        
        <NotificationCenter />

        <div className="h-8 w-px bg-secondary-200" role="separator" aria-orientation="vertical" />

        <button
          onClick={handleLogout}
          className="flex items-center px-3 py-2 text-sm font-medium text-secondary-700 hover:text-secondary-900 rounded-md hover:bg-secondary-100 transition-colors duration-200"
          aria-label={t('navigation.logoutAriaLabel')}
        >
          <LogOut className="w-4 h-4 mr-2" aria-hidden="true" />
          {t('common.logout')}
        </button>
      </div>
    </nav>
  );
};