import React from 'react';
import { clsx } from 'clsx';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'value' | 'onChange'> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, helperText, options, value, onChange, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {label}
          </label>
        )}
        <select
          ref={ref}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={clsx(
            'block w-full rounded-md shadow-sm',
            'border-gray-300 dark:border-gray-600',
            'focus:border-blue-500 focus:ring-blue-500',
            'dark:bg-gray-700 dark:text-white',
            'sm:text-sm',
            error && 'border-red-300 focus:border-red-500 focus:ring-red-500',
            className
          )}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
        {helperText && !error && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{helperText}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

export const SelectContent: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

export const SelectItem: React.FC<SelectOption> = ({ value, label }) => {
  return <option value={value}>{label}</option>;
};

export const SelectTrigger: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => {
  return <div className={className}>{children}</div>;
};

export const SelectValue: React.FC<{ placeholder?: string }> = ({ placeholder }) => {
  return <span>{placeholder}</span>;
};