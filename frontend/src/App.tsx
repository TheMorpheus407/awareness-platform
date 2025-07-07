import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ProtectedRoute } from './components/Auth';
import { MainLayout } from './components/Layout';
import { Login, Register, Dashboard, Users, Companies } from './pages';

function App() {
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
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/users" element={<Users />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/courses" element={<div className="text-2xl font-bold">Courses (Coming Soon)</div>} />
            <Route path="/phishing" element={<div className="text-2xl font-bold">Phishing Simulation (Coming Soon)</div>} />
            <Route path="/reports" element={<div className="text-2xl font-bold">Reports (Coming Soon)</div>} />
            <Route path="/settings" element={<div className="text-2xl font-bold">Settings (Coming Soon)</div>} />
          </Route>
        </Route>
        
        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;