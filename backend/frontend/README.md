# Bootstrap Academy - Cybersecurity Awareness Platform Frontend

## Overview
This is the frontend application for the Bootstrap Academy Cybersecurity Awareness Platform, built with React, TypeScript, and Vite.

## Current Status
- ✅ Landing page implemented with full features
- ✅ Authentication system with 2FA support
- ✅ User and Company management interfaces
- ✅ Internationalization (German/English)
- ⚠️ Tests configured but not running properly
- ❌ E2E tests documented but not implemented

## Tech Stack
- **React 18.2** - UI Framework
- **TypeScript** - Type Safety
- **Vite** - Build Tool
- **Tailwind CSS** - Styling
- **React Router v6** - Routing
- **Zustand** - State Management
- **React Hook Form** - Form Handling
- **i18next** - Internationalization
- **Axios** - API Client
- **Lucide React** - Icons

## Getting Started

### Prerequisites
- Node.js v20.7.0 or higher
- npm v10.1.0 or higher

### Installation
```bash
npm install
```

### Development
```bash
npm run dev
```
The application will run on http://localhost:5173

### Building for Production
```bash
npm run build
```

### Running Tests
```bash
# Unit tests (currently not working - runner hangs)
npm run test

# E2E tests (not implemented - only documentation exists)
npm run e2e
```

## Project Structure
```
src/
├── components/      # Reusable UI components
│   ├── Auth/       # Authentication components
│   ├── Common/     # Shared components
│   ├── Company/    # Company management
│   └── User/       # User management
├── hooks/          # Custom React hooks
├── i18n/           # Internationalization files
├── pages/          # Route pages
├── services/       # API services
├── store/          # Zustand state management
├── types/          # TypeScript type definitions
└── utils/          # Utility functions
```

## Features

### Authentication
- Email/Password login
- Two-Factor Authentication (2FA) with TOTP
- Password reset flow
- Session management with JWT tokens
- Auto-refresh token mechanism

### User Management
- CRUD operations for users
- Role assignment (Admin, Manager, User)
- Bulk operations
- Search and filtering
- Pagination

### Company Management
- Company creation and editing
- Domain validation
- Industry categorization
- Employee management

### Internationalization
- German and English support
- Language persistence
- Automatic browser language detection
- All UI elements translated

### Landing Page
- Hero section with call-to-action
- Feature showcase
- Pricing tiers
- Customer testimonials
- Security badges
- Smooth scroll navigation
- Responsive design

## Environment Variables
Create a `.env` file based on `.env.example`:
```
VITE_API_URL=http://localhost:8000/api/v1
```

## Known Issues
1. **Test Runner Hangs**: Vitest test runner times out when running tests
2. **No E2E Tests**: E2E test documentation exists but no actual test files
3. **Mock Conflicts**: Test setup has conflicting global mocks
4. **WSL Performance**: Poor performance in WSL2 environment

## API Integration
The frontend communicates with the FastAPI backend through:
- RESTful API endpoints
- JWT authentication
- Automatic token refresh
- Error handling with toast notifications
- Request/response interceptors

## Deployment
The frontend is containerized using Docker:
- Multi-stage build for optimization
- Nginx for serving static files
- Environment variable injection
- Health check endpoint

## Contributing
Please see the main project CONTRIBUTING.md for guidelines.

## License
Proprietary - Bootstrap Academy