import React, { Suspense, lazy, ComponentType } from 'react';
import { Loader2 } from 'lucide-react';

interface LazyLoaderProps {
  loader: () => Promise<{ default: ComponentType<any> }>;
  fallback?: React.ReactNode;
}

/**
 * Enhanced lazy loading wrapper with better error handling and loading states
 */
export const LazyLoader: React.FC<LazyLoaderProps> = ({ loader, fallback }) => {
  const LazyComponent = lazy(loader);

  const defaultFallback = (
    <div className="flex items-center justify-center min-h-[200px]">
      <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
    </div>
  );

  return (
    <Suspense fallback={fallback || defaultFallback}>
      <LazyComponent />
    </Suspense>
  );
};

/**
 * Create a lazy-loaded component with retry logic
 */
export const createLazyComponent = (
  importFunc: () => Promise<{ default: ComponentType<any> }>,
  componentName?: string
) => {
  return lazy(() =>
    importFunc().catch((error) => {
      console.error(`Failed to load ${componentName || 'component'}:`, error);
      // Retry once after a delay
      return new Promise((resolve) => {
        setTimeout(() => {
          importFunc()
            .then(resolve)
            .catch(() => {
              // If retry fails, show error component
              resolve({
                default: () => (
                  <div className="text-center p-8">
                    <p className="text-red-600">Failed to load component</p>
                    <button
                      onClick={() => window.location.reload()}
                      className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Reload Page
                    </button>
                  </div>
                ),
              });
            });
        }, 1000);
      });
    })
  );
};

/**
 * Preload a lazy component
 */
export const preloadComponent = (
  loader: () => Promise<{ default: ComponentType<any> }>
) => {
  loader();
};