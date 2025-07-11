import React from 'react';

interface AccessibleFormProps extends React.FormHTMLAttributes<HTMLFormElement> {
  children: React.ReactNode;
  formTitle?: string;
  formDescription?: string;
  errorSummary?: string[];
}

export const AccessibleForm: React.FC<AccessibleFormProps> = ({
  children,
  formTitle,
  formDescription,
  errorSummary,
  ...props
}) => {
  const formId = props.id || 'form';
  const errorSummaryId = `${formId}-error-summary`;
  
  return (
    <form
      {...props}
      aria-label={formTitle}
      aria-describedby={errorSummary?.length ? errorSummaryId : undefined}
    >
      {formTitle && (
        <h2 className="text-xl font-semibold mb-2">{formTitle}</h2>
      )}
      
      {formDescription && (
        <p className="text-gray-600 mb-4">{formDescription}</p>
      )}
      
      {errorSummary && errorSummary.length > 0 && (
        <div
          id={errorSummaryId}
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
          className="bg-red-50 border border-red-200 rounded-md p-4 mb-6"
        >
          <h3 className="text-sm font-medium text-red-800 mb-2">
            There were errors with your submission
          </h3>
          <ul className="list-disc list-inside text-sm text-red-700">
            {errorSummary.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}
      
      {children}
    </form>
  );
};