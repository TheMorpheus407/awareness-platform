# Coding Standards Guide

## Table of Contents
1. [General Principles](#general-principles)
2. [Python/FastAPI Standards](#pythonfastapi-standards)
3. [TypeScript/React Standards](#typescriptreact-standards)
4. [Git Conventions](#git-conventions)
5. [Testing Requirements](#testing-requirements)
6. [Documentation Standards](#documentation-standards)
7. [Code Review Process](#code-review-process)

## General Principles

### Philosophy
- **Clean Code**: Write code that is self-documenting and easy to understand
- **DRY (Don't Repeat Yourself)**: Avoid code duplication
- **SOLID Principles**: Follow object-oriented design principles
- **Security First**: Always consider security implications
- **Performance Aware**: Consider performance impacts of code changes

### Universal Rules
- Maximum line length: 100 characters
- Use UTF-8 encoding for all files
- End files with a newline character
- No trailing whitespace
- Use meaningful variable and function names

## Python/FastAPI Standards

### Code Formatting
- **Formatter**: Black (line length: 100)
- **Linter**: Flake8 with the following config:

```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = .git,__pycache__,venv,migrations
```

### Code Style
1. **Imports**
   ```python
   # Standard library imports
   import os
   import sys
   from datetime import datetime
   
   # Third-party imports
   import numpy as np
   from fastapi import FastAPI, HTTPException
   from sqlalchemy.orm import Session
   
   # Local imports
   from app.core.config import settings
   from app.models.user import User
   ```

2. **Type Hints**
   - Always use type hints for function parameters and return values
   ```python
   def calculate_risk_score(
       user_id: int, 
       phishing_attempts: list[dict[str, Any]]
   ) -> float:
       """Calculate user's security risk score."""
       pass
   ```

3. **Docstrings**
   - Use Google-style docstrings for all public functions, classes, and modules
   ```python
   def send_phishing_email(
       recipient: str, 
       template_id: int, 
       campaign_id: int
   ) -> bool:
       """Send a phishing simulation email to a user.
       
       Args:
           recipient: Email address of the recipient
           template_id: ID of the phishing template to use
           campaign_id: ID of the phishing campaign
           
       Returns:
           True if email was sent successfully, False otherwise
           
       Raises:
           HTTPException: If template or campaign not found
       """
       pass
   ```

4. **Constants and Enums**
   ```python
   # Constants in uppercase
   MAX_LOGIN_ATTEMPTS = 5
   SESSION_TIMEOUT_MINUTES = 30
   
   # Use Enums for related constants
   from enum import Enum
   
   class UserRole(str, Enum):
       ADMIN = "admin"
       USER = "user"
       COMPANY_ADMIN = "company_admin"
   ```

5. **Error Handling**
   ```python
   # Be specific with exceptions
   try:
       user = db.query(User).filter(User.id == user_id).first()
       if not user:
           raise HTTPException(
               status_code=404, 
               detail=f"User with id {user_id} not found"
           )
   except SQLAlchemyError as e:
       logger.error(f"Database error: {str(e)}")
       raise HTTPException(
           status_code=500, 
           detail="Internal server error"
       )
   ```

### FastAPI Specific
1. **API Versioning**
   ```python
   app = FastAPI(title="Cybersecurity Awareness API")
   
   # Version 1 routes
   app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
   app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
   ```

2. **Dependency Injection**
   ```python
   def get_current_user(
       token: str = Depends(oauth2_scheme),
       db: Session = Depends(get_db)
   ) -> User:
       """Get current authenticated user."""
       pass
   ```

3. **Response Models**
   ```python
   from pydantic import BaseModel, Field
   
   class UserResponse(BaseModel):
       id: int
       email: str = Field(..., example="user@example.com")
       role: UserRole
       created_at: datetime
       
       class Config:
           from_attributes = True
   ```

## TypeScript/React Standards

### Code Formatting
- **Formatter**: Prettier with the following config:

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

- **Linter**: ESLint with TypeScript support

### TypeScript Style
1. **File Naming**
   - Components: `PascalCase.tsx` (e.g., `UserDashboard.tsx`)
   - Utilities: `camelCase.ts` (e.g., `formatDate.ts`)
   - Types: `PascalCase.types.ts` (e.g., `User.types.ts`)
   - Tests: `ComponentName.test.tsx` or `fileName.test.ts`

2. **Type Definitions**
   ```typescript
   // Prefer interfaces for objects
   interface User {
     id: number;
     email: string;
     role: UserRole;
     createdAt: Date;
   }
   
   // Use type aliases for unions/intersections
   type UserRole = 'admin' | 'user' | 'company_admin';
   
   // Use enums sparingly, prefer union types
   enum PhishingStatus {
     Pending = 'PENDING',
     Sent = 'SENT',
     Clicked = 'CLICKED',
     Reported = 'REPORTED',
   }
   ```

3. **Function Components**
   ```typescript
   import React, { FC, useState, useEffect } from 'react';
   
   interface DashboardProps {
     userId: number;
     onUpdate?: (data: DashboardData) => void;
   }
   
   export const Dashboard: FC<DashboardProps> = ({ userId, onUpdate }) => {
     const [data, setData] = useState<DashboardData | null>(null);
     const [loading, setLoading] = useState(true);
     
     useEffect(() => {
       // Effect logic
     }, [userId]);
     
     if (loading) return <LoadingSpinner />;
     if (!data) return <ErrorMessage message="No data available" />;
     
     return (
       <div className="dashboard">
         {/* Component content */}
       </div>
     );
   };
   ```

4. **Hooks**
   ```typescript
   // Custom hooks in separate files
   export const useAuth = () => {
     const [user, setUser] = useState<User | null>(null);
     const [loading, setLoading] = useState(true);
     
     // Hook logic
     
     return { user, loading, login, logout };
   };
   ```

5. **Error Boundaries**
   ```typescript
   class ErrorBoundary extends React.Component<Props, State> {
     static getDerivedStateFromError(error: Error): State {
       return { hasError: true, error };
     }
     
     componentDidCatch(error: Error, info: ErrorInfo) {
       console.error('Error caught by boundary:', error, info);
     }
     
     render() {
       if (this.state.hasError) {
         return <ErrorFallback error={this.state.error} />;
       }
       
       return this.props.children;
     }
   }
   ```

### React Best Practices
1. **Component Organization**
   ```
   src/
   ├── components/
   │   ├── common/
   │   │   ├── Button/
   │   │   │   ├── Button.tsx
   │   │   │   ├── Button.test.tsx
   │   │   │   ├── Button.styles.ts
   │   │   │   └── index.ts
   │   ├── features/
   │   │   ├── Dashboard/
   │   │   └── PhishingSimulation/
   ```

2. **State Management**
   - Use Zustand for global state
   - Keep component state local when possible
   - Lift state up only when necessary

3. **Performance**
   - Use React.memo for expensive components
   - Implement proper key props in lists
   - Use useMemo and useCallback appropriately

## Git Conventions

### Branch Naming
```
feature/issue-123-add-phishing-templates
bugfix/issue-456-fix-login-error
hotfix/critical-security-patch
chore/update-dependencies
docs/improve-api-documentation
```

### Commit Messages
Follow Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Examples:**
```
feat(auth): implement two-factor authentication

- Add TOTP support for user accounts
- Create QR code generation endpoint
- Update login flow to check 2FA status

Closes #123
```

```
fix(phishing): correct email template rendering issue

Fixed issue where custom variables were not being replaced
in phishing email templates.

Fixes #456
```

### Pull Request Process
1. Create feature branch from `develop`
2. Make changes following coding standards
3. Write/update tests
4. Update documentation
5. Create PR with description template
6. Ensure all CI checks pass
7. Request review from team members
8. Address review feedback
9. Squash and merge when approved

## Testing Requirements

### Python/Backend
- **Minimum Coverage**: 80%
- **Test Framework**: pytest
- **Test Structure**:
  ```python
  def test_should_create_user_with_valid_data(db_session):
      """Test user creation with valid input data."""
      # Arrange
      user_data = {
          "email": "test@example.com",
          "password": "SecurePass123!",
          "role": UserRole.USER
      }
      
      # Act
      user = UserService.create_user(db_session, user_data)
      
      # Assert
      assert user.email == user_data["email"]
      assert user.role == UserRole.USER
      assert verify_password("SecurePass123!", user.hashed_password)
  ```

### TypeScript/Frontend
- **Minimum Coverage**: 75%
- **Test Framework**: Vitest + React Testing Library
- **Test Structure**:
  ```typescript
  describe('LoginForm', () => {
     it('should display error message on invalid credentials', async () => {
       // Arrange
       const mockLogin = vi.fn().mockRejectedValue(new Error('Invalid credentials'));
       render(<LoginForm onLogin={mockLogin} />);
       
       // Act
       const emailInput = screen.getByLabelText(/email/i);
       const passwordInput = screen.getByLabelText(/password/i);
       const submitButton = screen.getByRole('button', { name: /login/i });
       
       await userEvent.type(emailInput, 'test@example.com');
       await userEvent.type(passwordInput, 'wrongpassword');
       await userEvent.click(submitButton);
       
       // Assert
       expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument();
     });
  });
  ```

### Integration Tests
- Test API endpoints with real database connections
- Test frontend/backend integration
- Test third-party service integrations

## Documentation Standards

### Code Comments
- Write self-documenting code that rarely needs comments
- Use comments to explain "why", not "what"
- Keep comments up-to-date with code changes

### API Documentation
- Use OpenAPI/Swagger annotations
- Document all endpoints, parameters, and responses
- Include example requests and responses

### README Files
Each module should have a README with:
- Purpose and overview
- Installation/setup instructions
- Usage examples
- API reference (if applicable)
- Contributing guidelines

### Architecture Decision Records (ADRs)
Document significant architectural decisions using the ADR format:
```markdown
# ADR-001: Use FastAPI for Backend Framework

## Status
Accepted

## Context
We need to choose a Python web framework for our backend API.

## Decision
We will use FastAPI for the following reasons:
- Built-in OpenAPI documentation
- Excellent performance
- Native async support
- Strong typing with Pydantic

## Consequences
- Positive: Automatic API documentation, better performance
- Negative: Smaller ecosystem compared to Django
```

## Code Review Process

### Review Checklist
- [ ] Code follows project style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Error handling is appropriate
- [ ] Code is DRY and maintainable

### Review Guidelines
1. **Be Constructive**: Provide specific, actionable feedback
2. **Focus on Code**: Review the code, not the person
3. **Explain Why**: Provide context for suggestions
4. **Acknowledge Good Work**: Highlight well-written code
5. **Use Tools**: Leverage automated tools for style/lint checks

### Review Comments Examples
```
// Good
"Consider using a more descriptive variable name here. 
Instead of 'data', something like 'userPhishingStats' 
would make the code more self-documenting."

// Bad
"This code is confusing."
```

## Enforcement

### Pre-commit Hooks
Install pre-commit hooks to enforce standards:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
        
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        types_or: [javascript, typescript, tsx, css, json]
```

### CI/CD Integration
- All PRs must pass linting checks
- Code coverage must not decrease
- All tests must pass before merge

## Updates and Maintenance

This document should be reviewed and updated quarterly or when significant technology changes occur. All developers are encouraged to propose improvements through the standard PR process.

Last Updated: 2025-01-07