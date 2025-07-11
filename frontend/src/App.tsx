import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { HelmetProvider } from 'react-helmet-async';
import { ProtectedRoute } from './components/Auth';
import { MainLayout } from './components/Layout';
import { ErrorBoundary } from './components/Common/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import { LazyLoader, createLazyComponent } from './components/LazyLoader';
import { Loader2 } from 'lucide-react';

// Eagerly loaded components (critical path)
import LandingEnhanced from './pages/LandingEnhanced';
import { Login, Register } from './pages';

// Lazy loaded components
const Dashboard = createLazyComponent(() => import('./pages').then(m => ({ default: m.Dashboard })), 'Dashboard');
const Users = createLazyComponent(() => import('./pages').then(m => ({ default: m.Users })), 'Users');
const Companies = createLazyComponent(() => import('./pages').then(m => ({ default: m.Companies })), 'Companies');
const Analytics = createLazyComponent(() => import('./pages').then(m => ({ default: m.Analytics })), 'Analytics');
const Phishing = createLazyComponent(() => import('./pages').then(m => ({ default: m.Phishing })), 'Phishing');
const DashboardEnhanced = createLazyComponent(() => import('./pages/DashboardEnhanced').then(m => ({ default: m.DashboardEnhanced })), 'DashboardEnhanced');

// Payment components
const PricingPage = createLazyComponent(() => import('./components/Payment').then(m => ({ default: m.PricingPage })), 'PricingPage');
const CheckoutForm = createLazyComponent(() => import('./components/Payment').then(m => ({ default: m.CheckoutForm })), 'CheckoutForm');
const BillingDashboard = createLazyComponent(() => import('./components/Payment').then(m => ({ default: m.BillingDashboard })), 'BillingDashboard');

// Legal pages
const Impressum = createLazyComponent(() => import('./pages/legal/Impressum').then(m => ({ default: m.Impressum })), 'Impressum');
const Privacy = createLazyComponent(() => import('./pages/legal/Privacy').then(m => ({ default: m.Privacy })), 'Privacy');
const Terms = createLazyComponent(() => import('./pages/legal/Terms').then(m => ({ default: m.Terms })), 'Terms');

// Company pages
const About = createLazyComponent(() => import('./pages/About').then(m => ({ default: m.About })), 'About');
const Contact = createLazyComponent(() => import('./pages/Contact').then(m => ({ default: m.Contact })), 'Contact');
const Demo = createLazyComponent(() => import('./pages/Demo').then(m => ({ default: m.default })), 'Demo');
const Careers = createLazyComponent(() => import('./pages/Careers').then(m => ({ default: m.Careers })), 'Careers');
const Partners = createLazyComponent(() => import('./pages/Partners').then(m => ({ default: m.Partners })), 'Partners');
const Blog = createLazyComponent(() => import('./pages/Blog').then(m => ({ default: m.Blog })), 'Blog');
const CaseStudies = createLazyComponent(() => import('./pages/CaseStudies').then(m => ({ default: m.CaseStudies })), 'CaseStudies');
const NotificationTest = createLazyComponent(() => import('./pages/NotificationTest').then(m => ({ default: m.NotificationTest })), 'NotificationTest');

// Loading component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <Loader2 className="animate-spin h-12 w-12 text-blue-600" />
  </div>
);

function App() {
  const { t } = useTranslation();
  
  // Initialize security and performance monitoring
  useEffect(() => {
    // Initialize security measures
    import('./utils/security').then(({ initializeSecurity }) => {
      initializeSecurity();
    });
    
    // Initialize performance monitoring
    import('./utils/performance').then(({ PerformanceMonitor }) => {
      const monitor = PerformanceMonitor.getInstance();
      
      // Report metrics after initial load
      if (document.readyState === 'complete') {
        setTimeout(() => monitor.reportToAnalytics(), 1000);
      } else {
        window.addEventListener('load', () => {
          setTimeout(() => monitor.reportToAnalytics(), 1000);
        });
      }
    });
  }, []);
  
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <HelmetProvider>
          <BrowserRouter>
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            style: {
              background: '#059669',
            },
          },
          error: {
            style: {
              background: '#dc2626',
            },
          },
        }}
      />
      
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingEnhanced />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/demo" element={<Demo />} />
          
          {/* Legal pages */}
          <Route path="/impressum" element={<Impressum />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/terms" element={<Terms />} />
          
          {/* Company pages */}
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/careers" element={<Careers />} />
          <Route path="/partners" element={<Partners />} />
          
          {/* Resources */}
          <Route path="/blog" element={<Blog />} />
          <Route path="/case-studies" element={<CaseStudies />} />
          
          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route path="/dashboard" element={<DashboardEnhanced />} />
              <Route path="/users" element={<Users />} />
              <Route path="/companies" element={<Companies />} />
              <Route path="/courses" element={<div className="text-2xl font-bold">{t('courses.comingSoon')}</div>} />
              <Route path="/phishing/*" element={<Phishing />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/reports" element={<div className="text-2xl font-bold">{t('reports.comingSoon')}</div>} />
              <Route path="/settings" element={<div className="text-2xl font-bold">{t('settings.comingSoon')}</div>} />
              <Route path="/checkout" element={<CheckoutForm />} />
              <Route path="/billing" element={<BillingDashboard />} />
              <Route path="/notification-test" element={<NotificationTest />} />
            </Route>
          </Route>
        </Routes>
      </Suspense>
          </BrowserRouter>
        </HelmetProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;