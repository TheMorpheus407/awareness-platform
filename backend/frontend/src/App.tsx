import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { ProtectedRoute } from './components/Auth';
import { MainLayout } from './components/Layout';
import { Login, Register, Dashboard, Users, Companies, Analytics, Phishing } from './pages';
import LandingEnhanced from './pages/LandingEnhanced';
import { PricingPage, CheckoutForm, BillingDashboard } from './components/Payment';

function App() {
  const { t } = useTranslation();
  
  return (
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
        
        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/users" element={<Users />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/courses" element={<div className="text-2xl font-bold">{t('courses.comingSoon')}</div>} />
            <Route path="/phishing/*" element={<Phishing />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/reports" element={<div className="text-2xl font-bold">{t('reports.comingSoon')}</div>} />
            <Route path="/settings" element={<div className="text-2xl font-bold">{t('settings.comingSoon')}</div>} />
            <Route path="/checkout" element={<CheckoutForm />} />
            <Route path="/billing" element={<BillingDashboard />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;