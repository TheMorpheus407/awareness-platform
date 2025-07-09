import React, { useState } from 'react';
import { Download, FileText, FileSpreadsheet, FilePlus } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface ExportButtonProps {
  onExport: (format: string) => void;
}

const ExportButton: React.FC<ExportButtonProps> = ({ onExport }) => {
  const { t } = useTranslation();
  const [showMenu, setShowMenu] = useState(false);

  const exportFormats = [
    { value: 'csv', label: 'CSV', icon: FileText },
    { value: 'excel', label: 'Excel', icon: FileSpreadsheet },
    { value: 'pdf', label: 'PDF', icon: FilePlus },
  ];

  const handleExport = (format: string) => {
    onExport(format);
    setShowMenu(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                   bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300
                   hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center space-x-2"
      >
        <Download className="h-4 w-4" />
        <span>{t('analytics.actions.export')}</span>
      </button>

      {showMenu && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg 
                        border border-gray-200 dark:border-gray-700 z-10">
          {exportFormats.map((format) => {
            const Icon = format.icon;
            return (
              <button
                key={format.value}
                onClick={() => handleExport(format.value)}
                className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300
                         hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2
                         first:rounded-t-lg last:rounded-b-lg"
              >
                <Icon className="h-4 w-4" />
                <span>{t(`analytics.export.${format.value}`)}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ExportButton;