import React from 'react';
import { Calendar } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface DateRangePickerProps {
  value: string;
  onChange: (value: string) => void;
}

const DateRangePicker: React.FC<DateRangePickerProps> = ({ value, onChange }) => {
  const { t } = useTranslation();

  const options = [
    { value: 'today', label: t('analytics.dateRange.today') },
    { value: 'last_7_days', label: t('analytics.dateRange.last7Days') },
    { value: 'last_30_days', label: t('analytics.dateRange.last30Days') },
    { value: 'last_90_days', label: t('analytics.dateRange.last90Days') },
    { value: 'last_year', label: t('analytics.dateRange.lastYear') },
  ];

  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                   focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
    </div>
  );
};

export default DateRangePicker;