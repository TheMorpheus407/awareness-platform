/**
 * Performance monitoring utilities for frontend optimization
 */

interface PerformanceMetrics {
  ttfb: number; // Time to First Byte
  fcp: number; // First Contentful Paint
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  tti: number; // Time to Interactive
}

export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: Partial<PerformanceMetrics> = {};
  private observers: Map<string, PerformanceObserver> = new Map();

  private constructor() {
    this.initializeObservers();
  }

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  private initializeObservers() {
    // Observe paint timing
    if ('PerformanceObserver' in window) {
      // First Contentful Paint
      try {
        const paintObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.name === 'first-contentful-paint') {
              this.metrics.fcp = entry.startTime;
            }
          }
        });
        paintObserver.observe({ entryTypes: ['paint'] });
        this.observers.set('paint', paintObserver);
      } catch (e) {
        console.warn('Paint observer not supported');
      }

      // Largest Contentful Paint
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          this.metrics.lcp = lastEntry.startTime;
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.set('lcp', lcpObserver);
      } catch (e) {
        console.warn('LCP observer not supported');
      }

      // First Input Delay
      try {
        const fidObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.metrics.fid = entry.processingStart - entry.startTime;
          }
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.set('fid', fidObserver);
      } catch (e) {
        console.warn('FID observer not supported');
      }

      // Layout Shift
      try {
        let clsValue = 0;
        let clsEntries: PerformanceEntry[] = [];

        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            // Only count layout shifts without recent user input
            if (!(entry as any).hadRecentInput) {
              clsEntries.push(entry);
              clsValue += (entry as any).value;
            }
          }
        });

        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.set('cls', clsObserver);

        // Update CLS periodically
        setInterval(() => {
          this.metrics.cls = clsValue;
        }, 5000);
      } catch (e) {
        console.warn('CLS observer not supported');
      }
    }

    // Navigation timing
    if ('performance' in window && 'timing' in performance) {
      window.addEventListener('load', () => {
        setTimeout(() => {
          const timing = performance.timing;
          this.metrics.ttfb = timing.responseStart - timing.navigationStart;
          this.metrics.tti = timing.loadEventEnd - timing.navigationStart;
        }, 0);
      });
    }
  }

  getMetrics(): Partial<PerformanceMetrics> {
    return { ...this.metrics };
  }

  reportToAnalytics() {
    const metrics = this.getMetrics();
    
    // Send to analytics service
    if (window.gtag) {
      // Google Analytics
      for (const [key, value] of Object.entries(metrics)) {
        if (value !== undefined) {
          window.gtag('event', 'timing_complete', {
            name: key,
            value: Math.round(value),
            event_category: 'Performance',
          });
        }
      }
    }

    // Custom analytics endpoint
    if (process.env.NODE_ENV === 'production') {
      fetch('/api/v1/analytics/performance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metrics,
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
        }),
      }).catch(() => {
        // Silently fail - don't impact user experience
      });
    }
  }

  destroy() {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers.clear();
  }
}

// Utility function to measure component render time
export function measureComponentPerformance(componentName: string) {
  return function <T extends { new(...args: any[]): any }>(constructor: T) {
    return class extends constructor {
      componentDidMount() {
        performance.mark(`${componentName}-mount-start`);
        if (super.componentDidMount) {
          super.componentDidMount();
        }
        performance.mark(`${componentName}-mount-end`);
        performance.measure(
          `${componentName}-mount`,
          `${componentName}-mount-start`,
          `${componentName}-mount-end`
        );
      }

      componentDidUpdate() {
        performance.mark(`${componentName}-update-start`);
        if (super.componentDidUpdate) {
          super.componentDidUpdate();
        }
        performance.mark(`${componentName}-update-end`);
        performance.measure(
          `${componentName}-update`,
          `${componentName}-update-start`,
          `${componentName}-update-end`
        );
      }
    };
  };
}

// React hook for performance monitoring
export function usePerformanceMonitor() {
  const monitor = PerformanceMonitor.getInstance();

  useEffect(() => {
    // Report metrics after page fully loads
    const timer = setTimeout(() => {
      monitor.reportToAnalytics();
    }, 5000);

    return () => {
      clearTimeout(timer);
    };
  }, []);

  return monitor;
}

// Resource loading optimization
export const preloadResource = (url: string, as: 'script' | 'style' | 'image' | 'font') => {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.href = url;
  link.as = as;
  
  if (as === 'font') {
    link.crossOrigin = 'anonymous';
  }
  
  document.head.appendChild(link);
};

// Prefetch route for faster navigation
export const prefetchRoute = (path: string) => {
  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.href = path;
  document.head.appendChild(link);
};

// Image loading optimization
export const optimizeImage = (src: string, options?: {
  width?: number;
  height?: number;
  quality?: number;
  format?: 'webp' | 'jpg' | 'png';
}) => {
  // If using a CDN that supports image optimization
  if (src.includes('cloudinary.com')) {
    const params = [];
    if (options?.width) params.push(`w_${options.width}`);
    if (options?.height) params.push(`h_${options.height}`);
    if (options?.quality) params.push(`q_${options.quality}`);
    if (options?.format) params.push(`f_${options.format}`);
    
    const transformation = params.join(',');
    return src.replace('/upload/', `/upload/${transformation}/`);
  }
  
  // Return original URL if no optimization available
  return src;
};

// Debounce utility for performance
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Throttle utility for performance
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Request idle callback polyfill
export const requestIdleCallback = 
  window.requestIdleCallback ||
  function (cb: IdleRequestCallback) {
    const start = Date.now();
    return setTimeout(function () {
      cb({
        didTimeout: false,
        timeRemaining: function () {
          return Math.max(0, 50 - (Date.now() - start));
        },
      });
    }, 1);
  };

// Cancel idle callback polyfill
export const cancelIdleCallback =
  window.cancelIdleCallback ||
  function (id: number) {
    clearTimeout(id);
  };

declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
  }
}

export default PerformanceMonitor;