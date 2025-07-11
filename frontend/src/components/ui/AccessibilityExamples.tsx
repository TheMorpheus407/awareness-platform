import React, { useState } from 'react';
import { Mail, Lock, User, Calendar } from 'lucide-react';
import { AccessibleInput } from './AccessibleInput';
import { AccessibleForm } from './AccessibleForm';
import { Button } from './button';

/**
 * This file demonstrates proper ARIA implementation patterns
 * for common UI components in the application.
 */

export const AccessibilityExamples: React.FC = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: '',
    birthdate: ''
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Validation logic here
  };

  return (
    <div className="space-y-8 p-6">
      <h1 className="text-2xl font-bold">Accessibility Implementation Examples</h1>
      
      {/* Example 1: Accessible Form with Error Summary */}
      <section>
        <h2 className="text-xl font-semibold mb-4">1. Accessible Form with Validation</h2>
        
        <AccessibleForm
          onSubmit={handleSubmit}
          formTitle="User Registration Form"
          formDescription="Please fill in all required fields to create your account."
          errorSummary={Object.values(errors).filter(Boolean)}
        >
          <div className="space-y-4 max-w-md">
            <AccessibleInput
              label="Email Address"
              type="email"
              required
              icon={<Mail className="w-5 h-5 text-gray-400" />}
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              error={errors.email}
              hint="We'll never share your email with anyone else."
              placeholder="you@example.com"
            />
            
            <AccessibleInput
              label="Username"
              type="text"
              required
              icon={<User className="w-5 h-5 text-gray-400" />}
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              error={errors.username}
              hint="Choose a unique username (3-20 characters)"
              autoComplete="username"
            />
            
            <AccessibleInput
              label="Password"
              type="password"
              required
              icon={<Lock className="w-5 h-5 text-gray-400" />}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              error={errors.password}
              hint="Must be at least 8 characters with one uppercase letter"
              autoComplete="new-password"
            />
            
            <AccessibleInput
              label="Date of Birth"
              type="date"
              icon={<Calendar className="w-5 h-5 text-gray-400" />}
              value={formData.birthdate}
              onChange={(e) => setFormData({ ...formData, birthdate: e.target.value })}
              hint="Must be 18 years or older"
            />
            
            <Button
              type="submit"
              loading={loading}
              ariaLabel="Submit registration form"
              className="w-full"
            >
              Create Account
            </Button>
          </div>
        </AccessibleForm>
      </section>

      {/* Example 2: Icon Buttons with ARIA Labels */}
      <section>
        <h2 className="text-xl font-semibold mb-4">2. Accessible Icon Buttons</h2>
        
        <div className="flex gap-4">
          <Button
            variant="outline"
            size="sm"
            ariaLabel="Edit user profile"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </Button>
          
          <Button
            variant="danger"
            size="sm"
            ariaLabel="Delete item"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </Button>
          
          <Button
            variant="ghost"
            size="sm"
            ariaLabel="View more options"
            ariaExpanded={false}
            ariaControls="options-menu"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
            </svg>
          </Button>
        </div>
      </section>

      {/* Example 3: Toggle Buttons */}
      <section>
        <h2 className="text-xl font-semibold mb-4">3. Accessible Toggle Buttons</h2>
        
        <div className="flex gap-4">
          <Button
            variant="outline"
            ariaPressed={false}
            ariaLabel="Toggle notifications"
          >
            Notifications Off
          </Button>
          
          <Button
            variant="primary"
            ariaPressed={true}
            ariaLabel="Toggle dark mode"
          >
            Dark Mode On
          </Button>
        </div>
      </section>

      {/* Example 4: Loading States */}
      <section>
        <h2 className="text-xl font-semibold mb-4">4. Accessible Loading States</h2>
        
        <div className="space-y-4">
          <Button
            loading={true}
            ariaLabel="Processing payment"
          >
            Processing Payment...
          </Button>
          
          <div 
            className="p-4 border rounded-md"
            aria-busy="true"
            aria-live="polite"
            aria-label="Loading user data"
          >
            <p className="text-gray-600">Fetching your information...</p>
          </div>
        </div>
      </section>

      {/* Example 5: Live Regions for Dynamic Content */}
      <section>
        <h2 className="text-xl font-semibold mb-4">5. Live Regions for Updates</h2>
        
        <div className="space-y-4">
          {/* Status Updates */}
          <div 
            role="status" 
            aria-live="polite" 
            aria-atomic="true"
            className="p-3 bg-blue-50 border border-blue-200 rounded"
          >
            <p>3 new messages received</p>
          </div>
          
          {/* Error Alerts */}
          <div 
            role="alert" 
            aria-live="assertive" 
            aria-atomic="true"
            className="p-3 bg-red-50 border border-red-200 rounded"
          >
            <p>Failed to save changes. Please try again.</p>
          </div>
          
          {/* Progress Updates */}
          <div 
            role="progressbar" 
            aria-valuenow={75} 
            aria-valuemin={0} 
            aria-valuemax={100}
            aria-label="Upload progress"
            className="w-full bg-gray-200 rounded-full h-2.5"
          >
            <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: '75%' }}></div>
          </div>
        </div>
      </section>

      {/* Example 6: Keyboard Navigation Hints */}
      <section>
        <h2 className="text-xl font-semibold mb-4">6. Keyboard Navigation</h2>
        
        <div className="p-4 bg-gray-50 rounded-md">
          <h3 className="font-medium mb-2">Keyboard Shortcuts</h3>
          <dl className="space-y-1 text-sm">
            <div className="flex">
              <dt className="font-medium w-32">Tab:</dt>
              <dd>Navigate between interactive elements</dd>
            </div>
            <div className="flex">
              <dt className="font-medium w-32">Shift + Tab:</dt>
              <dd>Navigate backwards</dd>
            </div>
            <div className="flex">
              <dt className="font-medium w-32">Enter/Space:</dt>
              <dd>Activate buttons and links</dd>
            </div>
            <div className="flex">
              <dt className="font-medium w-32">Escape:</dt>
              <dd>Close modals and dropdowns</dd>
            </div>
            <div className="flex">
              <dt className="font-medium w-32">Arrow Keys:</dt>
              <dd>Navigate within menus and lists</dd>
            </div>
          </dl>
        </div>
      </section>
    </div>
  );
};