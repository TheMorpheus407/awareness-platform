import React from 'react';
import { clsx } from 'clsx';

interface SwitchProps {
  checked: boolean;
  onChange?: (checked: boolean) => void;
  onCheckedChange?: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export const Switch: React.FC<SwitchProps> = ({
  checked,
  onChange,
  onCheckedChange,
  label,
  disabled = false,
  className,
  id,
}) => {
  const handleChange = (newChecked: boolean) => {
    onChange?.(newChecked);
    onCheckedChange?.(newChecked);
  };
  return (
    <label className={clsx('flex items-center cursor-pointer', disabled && 'opacity-50 cursor-not-allowed', className)}>
      <div className="relative">
        <input
          type="checkbox"
          className="sr-only"
          id={id}
          checked={checked}
          onChange={(e) => handleChange(e.target.checked)}
          disabled={disabled}
        />
        <div className={clsx(
          'block w-14 h-8 rounded-full transition-colors',
          checked ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
        )}></div>
        <div className={clsx(
          'absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition-transform',
          checked && 'transform translate-x-6'
        )}></div>
      </div>
      {label && (
        <span className="ml-3 text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </span>
      )}
    </label>
  );
};