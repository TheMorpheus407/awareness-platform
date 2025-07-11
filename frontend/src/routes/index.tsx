import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';
import { createLazyComponent } from '@/components/LazyLoader';
import Layout from '@/components/Layout/Layout';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';

// Lazy load all route components for code splitting
const Dashboard = createLazyComponent(
  () => import('@/pages/Dashboard'),
  'Dashboard'
);

const Courses = createLazyComponent(
  () => import('@/pages/Courses'),
  'Courses'
);

const CourseDetail = createLazyComponent(
  () => import('@/pages/CourseDetail'),
  'CourseDetail'
);

const PhishingSimulation = createLazyComponent(
  () => import('@/pages/PhishingSimulation'),
  'PhishingSimulation'
);

const Analytics = createLazyComponent(
  () => import('@/pages/Analytics'),
  'Analytics'
);

const Profile = createLazyComponent(
  () => import('@/pages/Profile'),
  'Profile'
);

const Settings = createLazyComponent(
  () => import('@/pages/Settings'),
  'Settings'
);

const Users = createLazyComponent(
  () => import('@/pages/Users'),
  'Users'
);

const Companies = createLazyComponent(
  () => import('@/pages/Companies'),
  'Companies'
);

const Login = createLazyComponent(
  () => import('@/pages/Login'),
  'Login'
);

const Register = createLazyComponent(
  () => import('@/pages/Register'),
  'Register'
);

const Landing = createLazyComponent(
  () => import('@/pages/Landing'),
  'Landing'
);

const NotFound = createLazyComponent(
  () => import('@/pages/NotFound'),
  'NotFound'
);

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Landing />,
      },
      {
        path: 'login',
        element: <Login />,
      },
      {
        path: 'register',
        element: <Register />,
      },
      {
        path: 'dashboard',
        element: (
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'courses',
        children: [
          {
            index: true,
            element: (
              <ProtectedRoute>
                <Courses />
              </ProtectedRoute>
            ),
          },
          {
            path: ':courseId',
            element: (
              <ProtectedRoute>
                <CourseDetail />
              </ProtectedRoute>
            ),
          },
        ],
      },
      {
        path: 'phishing',
        element: (
          <ProtectedRoute>
            <PhishingSimulation />
          </ProtectedRoute>
        ),
      },
      {
        path: 'analytics',
        element: (
          <ProtectedRoute>
            <Analytics />
          </ProtectedRoute>
        ),
      },
      {
        path: 'profile',
        element: (
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        ),
      },
      {
        path: 'settings',
        element: (
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        ),
      },
      {
        path: 'users',
        element: (
          <ProtectedRoute requiredRole="admin">
            <Users />
          </ProtectedRoute>
        ),
      },
      {
        path: 'companies',
        element: (
          <ProtectedRoute requiredRole="admin">
            <Companies />
          </ProtectedRoute>
        ),
      },
      {
        path: '*',
        element: <NotFound />,
      },
    ],
  },
];

// Preload critical routes
export const preloadCriticalRoutes = () => {
  // Preload dashboard and courses as they're likely to be accessed
  import('@/pages/Dashboard');
  import('@/pages/Courses');
};