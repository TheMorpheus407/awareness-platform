import React from 'react';
import { Menu, Bell, LogOut } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

interface NavbarProps {
  onMenuClick: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onMenuClick }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white border-b border-secondary-200 h-16 flex items-center justify-between px-4 lg:px-6">
      <button
        onClick={onMenuClick}
        className="lg:hidden p-2 rounded-md text-secondary-500 hover:text-secondary-700"
      >
        <Menu className="w-6 h-6" />
      </button>

      <div className="flex-1" />

      <div className="flex items-center space-x-4">
        <button className="p-2 rounded-md text-secondary-500 hover:text-secondary-700 relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        <div className="h-8 w-px bg-secondary-200" />

        <button
          onClick={handleLogout}
          className="flex items-center px-3 py-2 text-sm font-medium text-secondary-700 hover:text-secondary-900 rounded-md hover:bg-secondary-100 transition-colors duration-200"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Logout
        </button>
      </div>
    </nav>
  );
};