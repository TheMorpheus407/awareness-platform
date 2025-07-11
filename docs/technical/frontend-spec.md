# Frontend Spezifikation - Cybersecurity Awareness Platform
**Version 1.0 | React Single Page Application**

## 1. Technologie-Stack

### 1.1 Core Dependencies
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.20.0",
  "axios": "^1.6.0",
  "react-hook-form": "^7.48.0",
  "react-query": "^3.39.0",
  "zustand": "^4.4.0",
  "i18next": "^23.7.0",
  "react-i18next": "^13.5.0",
  "chart.js": "^4.4.0",
  "react-chartjs-2": "^5.2.0",
  "date-fns": "^2.30.0",
  "react-hot-toast": "^2.4.0"
}
```

### 1.2 Development Dependencies
```json
{
  "vite": "^5.0.0",
  "typescript": "^5.3.0",
  "@vitejs/plugin-react": "^4.2.0",
  "eslint": "^8.55.0",
  "prettier": "^3.1.0",
  "tailwindcss": "^3.3.0",
  "vitest": "^1.0.0",
  "@testing-library/react": "^14.1.0"
}
```

## 2. Projektstruktur

```
src/
├── api/
│   ├── client.ts              # Axios instance configuration
│   ├── endpoints/
│   │   ├── auth.ts
│   │   ├── users.ts
│   │   ├── courses.ts
│   │   ├── phishing.ts
│   │   └── reports.ts
│   └── types.ts               # API response types
│
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   ├── ForgotPassword.tsx
│   │   └── TwoFactorAuth.tsx
│   │
│   ├── layout/
│   │   ├── AppLayout.tsx
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   │
│   ├── dashboard/
│   │   ├── DashboardStats.tsx
│   │   ├── ComplianceWidget.tsx
│   │   ├── RiskScoreChart.tsx
│   │   └── UpcomingCourses.tsx
│   │
│   ├── courses/
│   │   ├── CourseList.tsx
│   │   ├── CourseCard.tsx
│   │   ├── CoursePlayer.tsx
│   │   ├── CourseQuiz.tsx
│   │   └── Certificate.tsx
│   │
│   ├── phishing/
│   │   ├── CampaignList.tsx
│   │   ├── CampaignForm.tsx
│   │   ├── TemplateSelector.tsx
│   │   └── ResultsView.tsx
│   │
│   ├── reporting/
│   │   ├── ReportDashboard.tsx
│   │   ├── ComplianceReport.tsx
│   │   ├── ExportDialog.tsx
│   │   └── ChartComponents.tsx
│   │
│   └── common/
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Modal.tsx
│       ├── Table.tsx
│       ├── Loader.tsx
│       └── ErrorBoundary.tsx
│
├── hooks/
│   ├── useAuth.ts
│   ├── useApi.ts
│   ├── useDebounce.ts
│   ├── usePagination.ts
│   └── useLocalStorage.ts
│
├── pages/
│   ├── Login.tsx
│   ├── Dashboard.tsx
│   ├── Courses.tsx
│   ├── PhishingSimulation.tsx
│   ├── Reports.tsx
│   ├── UserManagement.tsx
│   └── Settings.tsx
│
├── services/
│   ├── auth.service.ts
│   ├── notification.service.ts
│   ├── export.service.ts
│   └── validation.service.ts
│
├── store/
│   ├── authStore.ts
│   ├── userStore.ts
│   ├── courseStore.ts
│   └── notificationStore.ts
│
├── styles/
│   ├── globals.css
│   ├── components.css
│   └── utilities.css
│
├── utils/
│   ├── constants.ts
│   ├── helpers.ts
│   ├── formatters.ts
│   └── validators.ts
│
├── locales/
│   ├── de/
│   ├── en/
│   ├── fr/
│   └── it/
│
├── App.tsx
├── main.tsx
└── vite-env.d.ts
```

## 3. Routing Struktur

```typescript
// App.tsx
const routes = [
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" /> },
      { path: "dashboard", element: <Dashboard /> },
      { path: "courses", element: <Courses /> },
      { path: "courses/:id", element: <CoursePlayer /> },
      { path: "phishing", element: <PhishingSimulation /> },
      { path: "reports", element: <Reports /> },
      { path: "users", element: <UserManagement /> },
      { path: "settings", element: <Settings /> }
    ]
  },
  {
    path: "/auth",
    element: <AuthLayout />,
    children: [
      { path: "login", element: <Login /> },
      { path: "register", element: <Register /> },
      { path: "forgot-password", element: <ForgotPassword /> }
    ]
  }
];
```

## 4. State Management (Zustand)

### 4.1 Auth Store
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}
```

### 4.2 Course Store
```typescript
interface CourseState {
  courses: Course[];
  userProgress: Progress[];
  currentCourse: Course | null;
  loadCourses: () => Promise<void>;
  startCourse: (courseId: string) => Promise<void>;
  submitQuiz: (answers: Answer[]) => Promise<QuizResult>;
}
```

## 5. API Integration

### 5.1 Axios Configuration
```typescript
// api/client.ts
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request Interceptor
apiClient.interceptors.request.use((config) => {
  const token = authStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await authStore.getState().refreshToken();
    }
    return Promise.reject(error);
  }
);
```

### 5.2 API Endpoints
```typescript
// api/endpoints/courses.ts
export const coursesApi = {
  getAll: () => apiClient.get<Course[]>('/courses'),
  getById: (id: string) => apiClient.get<Course>(`/courses/${id}`),
  getUserProgress: () => apiClient.get<Progress[]>('/courses/progress'),
  startCourse: (id: string) => apiClient.post(`/courses/${id}/start`),
  submitQuiz: (id: string, answers: Answer[]) => 
    apiClient.post(`/courses/${id}/quiz`, { answers })
};
```

## 6. Komponenten-Spezifikationen

### 6.1 CoursePlayer Component
```typescript
interface CoursePlayerProps {
  courseId: string;
}

const CoursePlayer: React.FC<CoursePlayerProps> = ({ courseId }) => {
  // YouTube Player Integration
  // Progress Tracking
  // Quiz Integration
  // Certificate Generation
};
```

**Features:**
- YouTube iframe API integration
- Automatisches Progress-Tracking
- Pause-Prevention (User muss Video schauen)
- Quiz nach Video-Ende
- PDF-Zertifikat Download

### 6.2 PhishingCampaign Component
```typescript
interface CampaignFormData {
  name: string;
  templateId: string;
  targetGroups: string[];
  scheduledDate: Date;
  frequency: 'once' | 'weekly' | 'monthly';
}
```

**Features:**
- Template-Vorschau
- Zielgruppen-Selektor
- Zeitplanung mit Kalender
- E-Mail Personalisierung
- Whitelisting-Optionen

### 6.3 ComplianceReport Component
```typescript
interface ReportConfig {
  type: 'nis2' | 'dsgvo' | 'iso27001' | 'custom';
  dateRange: DateRange;
  includeDetails: boolean;
  format: 'pdf' | 'csv' | 'json';
}
```

**Features:**
- Dynamische Report-Generierung
- Chart.js Visualisierungen
- PDF Export mit jsPDF
- Digitale Signatur Integration

## 7. Styling Guidelines

### 7.1 Tailwind Configuration
```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a'
        },
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444'
      }
    }
  }
};
```

### 7.2 Component Styling Pattern
```typescript
// Konsistente Styling-Klassen
const buttonVariants = {
  primary: 'bg-primary-500 hover:bg-primary-600 text-white',
  secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
  danger: 'bg-danger hover:bg-red-600 text-white'
};
```

## 8. Lokalisierung

### 8.1 i18n Setup
```typescript
// i18n.ts
i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'de',
    supportedLngs: ['de', 'en', 'fr', 'it'],
    interpolation: {
      escapeValue: false
    }
  });
```

### 8.2 Translation Keys
```json
// locales/de/common.json
{
  "navigation": {
    "dashboard": "Dashboard",
    "courses": "Schulungen",
    "phishing": "Phishing-Tests",
    "reports": "Berichte"
  },
  "actions": {
    "save": "Speichern",
    "cancel": "Abbrechen",
    "export": "Exportieren"
  }
}
```

## 9. Security Guidelines

### 9.1 XSS Prevention
- Keine direkte HTML-Injection
- DOMPurify für User-Content
- Content Security Policy Headers

### 9.2 Authentication Security
- JWT Token im Memory (nicht localStorage)
- Refresh Token als httpOnly Cookie
- CSRF Protection
- Session Timeout nach 30 Minuten

## 10. Performance Optimierung

### 10.1 Code Splitting
```typescript
// Lazy Loading für Routen
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Reports = lazy(() => import('./pages/Reports'));
```

### 10.2 Caching Strategy
- React Query für API Caching
- Service Worker für Asset Caching
- Optimistic Updates
- Debouncing für Search/Filter

## 11. Testing

### 11.1 Unit Tests
```typescript
// Button.test.tsx
describe('Button Component', () => {
  it('renders with correct variant', () => {
    render(<Button variant="primary">Click me</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary-500');
  });
});
```

### 11.2 Integration Tests
- API Mocking mit MSW
- User Flow Tests
- Accessibility Tests (react-axe)

## 12. Build & Deployment

### 12.1 Environment Variables
```env
VITE_API_URL=https://api.cybersec-platform.de
VITE_SENTRY_DSN=your-sentry-dsn
```

### 12.2 Build Configuration
```json
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts: ['chart.js', 'react-chartjs-2']
        }
      }
    }
  }
});
```

## 13. Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile: iOS Safari, Chrome Android

## 14. Accessibility (WCAG 2.1 AA)

- Semantic HTML
- ARIA Labels
- Keyboard Navigation
- Screen Reader Support
- Color Contrast Ratios
- Focus Indicators