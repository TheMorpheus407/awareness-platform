#!/bin/bash

# Run all E2E tests in different configurations

echo "🧪 Running E2E Tests..."

# Frontend-only tests
echo "📱 Running Frontend-Only Tests..."
npx playwright test --config=playwright.config.frontend.ts e2e/tests/frontend-only.spec.ts

# Landing page tests  
echo "🏠 Running Landing Page Tests..."
npx playwright test --config=playwright.config.frontend.ts e2e/tests/landing-page.spec.ts

# Visual regression tests
echo "📸 Running Visual Regression Tests..."
npx playwright test --config=playwright.config.frontend.ts e2e/tests/visual-regression-frontend.spec.ts

# Accessibility tests
echo "♿ Running Accessibility Tests..."
npx playwright test --config=playwright.config.frontend.ts e2e/tests/accessibility.spec.ts

# Full test suite (requires backend)
if [ "$1" == "--with-backend" ]; then
  echo "🔗 Running Full Test Suite with Backend..."
  npx playwright test
fi

echo "✅ E2E Tests Complete!"
echo "📊 View report: npx playwright show-report"