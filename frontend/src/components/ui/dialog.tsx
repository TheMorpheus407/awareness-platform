import React, { Fragment } from 'react';
import { Dialog as HeadlessDialog, Transition } from '@headlessui/react';
import { X } from 'lucide-react';
import { clsx } from 'clsx';

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

export const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
  return (
    <Transition.Root show={open} as={Fragment}>
      <HeadlessDialog as="div" className="relative z-50" onClose={onOpenChange}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <HeadlessDialog.Panel className="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                {children}
              </HeadlessDialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </HeadlessDialog>
    </Transition.Root>
  );
};

interface DialogContentProps {
  children: React.ReactNode;
  className?: string;
}

export const DialogContent: React.FC<DialogContentProps> = ({ children, className }) => {
  return <div className={clsx('p-6', className)}>{children}</div>;
};

interface DialogHeaderProps {
  children: React.ReactNode;
  className?: string;
  onClose?: () => void;
}

export const DialogHeader: React.FC<DialogHeaderProps> = ({ children, className, onClose }) => {
  return (
    <div className={clsx('flex items-center justify-between p-6 pb-0', className)}>
      {children}
      {onClose && (
        <button
          onClick={onClose}
          className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <X className="h-5 w-5" />
        </button>
      )}
    </div>
  );
};

interface DialogTitleProps {
  children: React.ReactNode;
  className?: string;
}

export const DialogTitle: React.FC<DialogTitleProps> = ({ children, className }) => {
  return (
    <HeadlessDialog.Title className={clsx('text-lg font-semibold leading-6 text-gray-900 dark:text-gray-100', className)}>
      {children}
    </HeadlessDialog.Title>
  );
};

interface DialogDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export const DialogDescription: React.FC<DialogDescriptionProps> = ({ children, className }) => {
  return (
    <HeadlessDialog.Description className={clsx('mt-2 text-sm text-gray-500 dark:text-gray-400', className)}>
      {children}
    </HeadlessDialog.Description>
  );
};

interface DialogFooterProps {
  children: React.ReactNode;
  className?: string;
}

export const DialogFooter: React.FC<DialogFooterProps> = ({ children, className }) => {
  return (
    <div className={clsx('bg-gray-50 dark:bg-gray-900 px-6 py-3 sm:flex sm:flex-row-reverse', className)}>
      {children}
    </div>
  );
};

export const DialogTrigger: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};