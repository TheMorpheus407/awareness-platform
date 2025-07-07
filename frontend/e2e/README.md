# E2E Testing with Playwright

This directory contains end-to-end tests for the Cybersecurity Awareness Platform using Playwright.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Install Playwright browsers:
   ```bash
   npx playwright install
   ```

3. Set up test data:
   - Ensure the backend is running with a test database
   - Run seed scripts to create test users and data

## Running Tests

### Run all tests
```bash
npm run e2e
```

### Run tests in UI mode (recommended for development)
```bash
npm run e2e:ui
```

### Run tests in headed mode (see browser)
```bash
npm run e2e:headed
```

### Debug a specific test
```bash
npm run e2e:debug
```

### Update visual regression snapshots
```bash
npm run e2e:update-snapshots
```

### View test report
```bash
npm run e2e:report
```

### Generate test code (record actions)
```bash
npm run e2e:codegen
```

## Test Structure

```
e2e/
├── fixtures/          # Custom test fixtures and setup
├── pages/            # Page Object Models
├── tests/            # Test specifications
├── utils/            # Helper utilities
└── README.md
```

## Test Categories

### Authentication Tests (`auth.spec.ts`)
- Login/logout flows
- Registration
- Password reset
- Token refresh
- Protected route access

### User Management Tests (`users.spec.ts`)
- CRUD operations for users
- Search and filtering
- Pagination
- Form validation
- Role management

### Company Management Tests (`companies.spec.ts`)
- CRUD operations for companies
- Search and filtering
- Domain validation
- Industry filtering

### Internationalization Tests (`i18n.spec.ts`)
- Language switching
- Translated content
- Validation messages in different languages
- Language persistence

### API Integration Tests (`api-integration.spec.ts`)
- Error handling
- Network timeouts
- Retry logic
- Concurrent modifications
- Real-time updates

### Visual Regression Tests (`visual-regression.spec.ts`)
- Screenshot comparisons
- Mobile responsive views
- Dark mode (if implemented)
- Loading states
- Error states

## Page Objects

Page objects provide a clean API for interacting with pages:

```typescript
// Example usage
const loginPage = new LoginPage(page);
await loginPage.goto();
await loginPage.login('user@example.com', 'password');
```

## Test Data Management

The `TestDataManager` utility helps create and clean up test data:

```typescript
const testDataManager = new TestDataManager(request);
const user = await testDataManager.createTestUser({
  email: generateTestEmail(),
  password: 'TestPassword123!',
  firstName: 'Test',
  lastName: 'User',
});

// Cleanup is automatic in afterEach
```

## Best Practices

1. **Use Page Objects**: Keep selectors and page logic in page objects
2. **Clean Test Data**: Always clean up created test data
3. **Unique Test Data**: Use generated emails/domains to avoid conflicts
4. **Wait for Elements**: Use Playwright's auto-waiting, avoid hard waits
5. **Parallel Execution**: Tests should be independent and parallelizable
6. **Meaningful Assertions**: Test user-visible behavior, not implementation

## Environment Variables

- `PLAYWRIGHT_BASE_URL`: Base URL for the frontend (default: http://localhost:5173)
- `CI`: Set to true in CI environments for optimized settings

## Debugging Tips

1. Use `page.pause()` to pause execution
2. Use the Playwright UI mode for step-by-step debugging
3. Use `--debug` flag to open Playwright Inspector
4. Check screenshots and videos in `test-results/` for failures
5. Use `console.log` with `page.evaluate()` for browser console access

## CI/CD Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests

Visual regression tests compare against baseline screenshots and report differences in PR comments.

## Troubleshooting

### Tests fail with "No such file or directory"
- Run `npx playwright install` to install browsers

### Tests timeout
- Check if backend and frontend are running
- Increase timeout in `playwright.config.ts`

### Visual regression tests fail
- Update snapshots if changes are intentional: `npm run e2e:update-snapshots`

### Cannot find elements
- Use Playwright codegen to find correct selectors: `npm run e2e:codegen`
- Check if elements have proper ARIA labels or test IDs