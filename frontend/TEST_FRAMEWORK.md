# Frontend Test Framework Documentation

## Overview

This document describes the custom test framework for the Awareness Platform frontend, providing comprehensive testing without SonarQube dependencies.

## Test Stack

- **Test Runner**: Vitest
- **Testing Library**: React Testing Library
- **User Interaction**: @testing-library/user-event
- **Mocking**: vitest mocks, axios-mock-adapter
- **Coverage**: @vitest/coverage-v8
- **E2E Tests**: Playwright

## Test Structure

```
src/
├── components/
│   ├── Auth/
│   │   ├── LoginForm.tsx
│   │   └── LoginForm.test.tsx
│   └── [component]/
│       ├── [Component].tsx
│       └── [Component].test.tsx
├── services/
│   ├── api.ts
│   └── api.test.ts
├── utils/
│   ├── helpers.ts
│   └── helpers.test.ts
├── hooks/
│   ├── useAuth.ts
│   └── useAuth.test.ts
└── test/
    └── setup.ts
```

## Running Tests

### Basic Commands

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run tests with UI
npm run test:ui

# Run specific test file
npm test LoginForm

# Run tests matching pattern
npm test -- --grep "authentication"
```

### E2E Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests in headed mode
npm run e2e:headed

# Run E2E tests with UI
npm run e2e:ui

# Update snapshots
npm run e2e:update-snapshots
```

## Writing Tests

### Component Tests

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" />);
    
    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    
    render(<MyComponent onClick={handleClick} />);
    
    await user.click(screen.getByRole('button'));
    
    expect(handleClick).toHaveBeenCalledOnce();
  });
});
```

### Service Tests

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import { api } from './api';
import { userService } from './userService';

describe('UserService', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(api);
  });

  afterEach(() => {
    mock.restore();
  });

  it('fetches users successfully', async () => {
    const users = [{ id: 1, name: 'Test User' }];
    mock.onGet('/users').reply(200, users);

    const result = await userService.getUsers();
    
    expect(result).toEqual(users);
  });
});
```

### Hook Tests

```typescript
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('increments counter', () => {
    const { result } = renderHook(() => useCounter());
    
    act(() => {
      result.current.increment();
    });
    
    expect(result.current.count).toBe(1);
  });
});
```

## Test Categories

### 1. Unit Tests
- Test individual components in isolation
- Mock all external dependencies
- Focus on component logic and rendering
- File pattern: `*.test.tsx`, `*.test.ts`

### 2. Integration Tests
- Test component interactions
- Test with real API calls (mocked backend)
- Test complex user flows
- File pattern: `*.integration.test.tsx`

### 3. E2E Tests
- Test complete user journeys
- Run against real application
- Test critical paths
- Location: `e2e/` directory

## Mocking Strategies

### Component Mocks

```typescript
// Mock a component
vi.mock('@/components/Button', () => ({
  Button: ({ children, onClick }: any) => (
    <button onClick={onClick}>{children}</button>
  ),
}));
```

### API Mocks

```typescript
// Mock API module
vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));
```

### Store Mocks

```typescript
// Mock Zustand store
vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    user: { id: 1, email: 'test@example.com' },
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));
```

## Testing Best Practices

### 1. Test User Behavior, Not Implementation

```typescript
// ❌ Bad: Testing implementation details
expect(component.state.isOpen).toBe(true);

// ✅ Good: Testing user-visible behavior
expect(screen.getByRole('dialog')).toBeVisible();
```

### 2. Use Testing Library Queries Correctly

```typescript
// Priority order:
// 1. getByRole
// 2. getByLabelText
// 3. getByPlaceholderText
// 4. getByText
// 5. getByDisplayValue
// 6. getByAltText
// 7. getByTitle
// 8. getByTestId (last resort)
```

### 3. Wait for Async Operations

```typescript
// ❌ Bad: Not waiting for async updates
fireEvent.click(submitButton);
expect(screen.getByText('Success')).toBeInTheDocument();

// ✅ Good: Properly waiting
await userEvent.click(submitButton);
await waitFor(() => {
  expect(screen.getByText('Success')).toBeInTheDocument();
});
```

### 4. Test Accessibility

```typescript
it('is accessible', async () => {
  const { container } = render(<MyComponent />);
  const results = await axe(container);
  
  expect(results).toHaveNoViolations();
});
```

## Coverage Requirements

### Minimum Coverage Thresholds
- Statements: 60%
- Branches: 60%
- Functions: 60%
- Lines: 60%

### Coverage by Component Type
- Business Logic: 80%+
- UI Components: 70%+
- Utilities: 90%+
- Services: 80%+

### Coverage Exclusions
- Test files
- Type definitions
- Configuration files
- Mock files
- Main entry point

## CI/CD Integration

### GitHub Actions Workflow

```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
    - run: npm ci
    - run: npm run test:coverage
    - run: npm run lint
    - run: npm run type-check
```

### Pre-commit Hooks

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged"
    }
  },
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write",
      "vitest related --run"
    ]
  }
}
```

## Debugging Tests

### VS Code Configuration

```json
{
  "jest.jestCommandLine": "npm run test --",
  "jest.autoRun": {
    "watch": true,
    "onSave": "test-file"
  }
}
```

### Debug Single Test

```bash
# Run single test file in debug mode
npm test -- LoginForm --inspect-brk

# Run specific test
npm test -- LoginForm -t "handles login"
```

### Common Issues

1. **Module Resolution**
   ```typescript
   // vitest.config.ts
   resolve: {
     alias: {
       '@': path.resolve(__dirname, './src'),
     },
   }
   ```

2. **CSS Modules**
   ```typescript
   // test/setup.ts
   vi.mock('*.module.css', () => ({}));
   ```

3. **Canvas/WebGL**
   ```typescript
   // test/setup.ts
   HTMLCanvasElement.prototype.getContext = vi.fn();
   ```

## Performance Testing

### Component Render Performance

```typescript
import { measureRenders } from '@/test/utils';

it('renders efficiently', () => {
  const { renderCount } = measureRenders(
    <ExpensiveComponent data={largeDataset} />
  );
  
  expect(renderCount).toBeLessThan(3);
});
```

### Bundle Size Testing

```typescript
it('maintains reasonable bundle size', async () => {
  const stats = await import('bundle-stats.json');
  const componentSize = stats.components['MyComponent'];
  
  expect(componentSize).toBeLessThan(50000); // 50KB
});
```

## Migration from SonarQube

### What We Replaced
- Code coverage → Vitest coverage
- Code smells → ESLint rules
- Security hotspots → eslint-plugin-security
- Duplication → eslint-plugin-sonarjs
- Complexity → eslint-plugin-complexity

### New Features
- Faster test execution
- Better IDE integration
- Component testing utilities
- Visual regression testing
- Performance benchmarks

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Playwright Documentation](https://playwright.dev/)