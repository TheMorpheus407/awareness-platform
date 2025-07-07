# Internationalization (i18n) Implementation

## Overview
This project now supports multiple languages using `react-i18next`. Currently, English (en) and German (de) are supported.

## Structure
```
src/i18n/
├── i18n.ts              # Main i18n configuration
└── locales/
    ├── en/
    │   └── translation.json  # English translations
    └── de/
        └── translation.json  # German translations
```

## Features Implemented

### 1. Language Switching
- Language switcher component in the navbar
- Saves selected language to localStorage
- Automatically detects browser language on first visit

### 2. Translated Components
- Authentication (Login/Register)
- Dashboard
- Navigation menu
- User management
- Company management
- Common UI elements
- Error messages

### 3. Dynamic Page Titles
- Page titles update based on selected language
- Uses `useDocumentTitle` hook

## Adding New Translations

### 1. Add translation keys to both JSON files:
```json
// en/translation.json
{
  "newFeature": {
    "title": "New Feature",
    "description": "Description in English"
  }
}

// de/translation.json
{
  "newFeature": {
    "title": "Neue Funktion",
    "description": "Beschreibung auf Deutsch"
  }
}
```

### 2. Use in components:
```tsx
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  
  return (
    <div>
      <h1>{t('newFeature.title')}</h1>
      <p>{t('newFeature.description')}</p>
    </div>
  );
}
```

## Language Detection Order
1. localStorage (saved preference)
2. Browser language
3. HTML lang attribute
4. Fallback to English

## Branding Updates
- Page title: "Cybersecurity Awareness Platform"
- App name: "CyberAware"
- Custom logo created at `/public/logo.svg`
- Meta tags added for SEO