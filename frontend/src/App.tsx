import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { ProtectedRoute } from './components/Auth';
import { MainLayout } from './components/Layout';
import { Login, Register, Dashboard, Users, Companies, Analytics, Phishing } from './pages';
import LandingEnhanced from './pages/LandingEnhanced';
import { DashboardEnhanced } from './pages/DashboardEnhanced';
import { PricingPage, CheckoutForm, BillingDashboard } from './components/Payment';
import { ErrorBoundary } from './components/Common/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import { Impressum } from './pages/legal/Impressum';
import { Privacy } from './pages/legal/Privacy';
import { Terms } from './pages/legal/Terms';
import { About } from './pages/About';
import { Contact } from './pages/Contact';
import { Blog } from './pages/Blog';
import Demo from './pages/Demo';
import { Careers } from './pages/Careers';
import { Partners } from './pages/Partners';
import { CaseStudies } from './pages/CaseStudies';
import { NotificationTest } from './pages/NotificationTest';

function App() {
  const { t } = useTranslation();
  
  return (
    <ErrorBoundary>
      <ThemeProvider>
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
        </BrowserRouter>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;