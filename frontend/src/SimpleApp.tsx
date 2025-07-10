import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SimpleLogin from './pages/SimpleLogin';
import SimpleDashboard from './pages/SimpleDashboard';

function SimpleApp() {
  const isAuthenticated = !!localStorage.getItem('access_token');

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<SimpleLogin />} />
        <Route
          path="/dashboard"
          element={
            isAuthenticated ? <SimpleDashboard /> : <Navigate to="/login" />
          }
        />
        <Route path="/" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} />
      </Routes>
    </Router>
  );
}

export default SimpleApp;