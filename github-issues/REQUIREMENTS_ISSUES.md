# GitHub Issues - Actual Requirements

## Core Feature Issues

### Issue #1: Complete Basic Authentication System
**Type:** Feature
**Priority:** High
**Labels:** mvp, authentication, security

**Description:**
Implement a simple but secure authentication system with the following features:
- Email/password login
- JWT token management with refresh tokens
- Basic 2FA using TOTP (Time-based One-Time Password)
- Password reset functionality
- Secure session management

**Acceptance Criteria:**
- [ ] Users can register with email/password
- [ ] Users can login and receive JWT tokens
- [ ] 2FA can be enabled/disabled by users
- [ ] Password reset works via email
- [ ] Sessions expire appropriately
- [ ] All auth endpoints have proper validation

**Technical Notes:**
- Use existing FastAPI + SQLAlchemy setup
- Keep it simple - no need for OAuth or complex flows
- PyOTP for 2FA implementation

---

### Issue #2: Implement Multi-Tenant Company System
**Type:** Feature
**Priority:** High
**Labels:** mvp, multi-tenancy, database

**Description:**
Create a proper multi-tenant system where companies can manage their users:
- Company registration and profile
- User management within companies
- Role-based access (Company Admin, Regular User)
- Data isolation using PostgreSQL RLS

**Acceptance Criteria:**
- [ ] Companies can self-register
- [ ] Company admins can add/remove users
- [ ] Users can only see their company's data
- [ ] RLS policies properly isolate data
- [ ] Basic company profile management

**Technical Notes:**
- Leverage existing RLS setup
- Keep roles simple (just Admin/User for now)
- CSV import for bulk user creation

---

### Issue #3: Build Video-Based Course System
**Type:** Feature
**Priority:** High
**Labels:** mvp, courses, core-feature

**Description:**
Implement the course system with video content and quizzes:
- Course catalog with modules
- YouTube video integration (unlisted videos)
- Quiz functionality after each module
- Progress tracking per user
- Simple certificate generation

**Acceptance Criteria:**
- [ ] Display course catalog
- [ ] Play YouTube videos in-app
- [ ] Quiz system with multiple choice questions
- [ ] Track user progress through courses
- [ ] Generate PDF certificates on completion
- [ ] Course assignment by admin

**Technical Notes:**
- Use YouTube iframe API
- Store quiz questions in PostgreSQL
- Simple HTML-to-PDF for certificates
- No need for complex SCORM compliance

---

### Issue #4: Create Basic Phishing Simulation System
**Type:** Feature
**Priority:** High
**Labels:** mvp, phishing, security-training

**Description:**
Build a simple phishing simulation system:
- Template library for phishing emails
- Campaign creation and scheduling
- Email sending capability
- Click tracking and reporting
- Immediate feedback for users who click

**Acceptance Criteria:**
- [ ] Create phishing email templates
- [ ] Schedule campaigns for user groups
- [ ] Send emails via SMTP
- [ ] Track who clicked links
- [ ] Show educational content on click
- [ ] Basic reporting dashboard

**Technical Notes:**
- Start with 10-15 templates
- Use simple SMTP library
- Track via unique URLs
- No need for complex analytics yet

---

### Issue #5: Develop Simple Analytics Dashboard
**Type:** Feature
**Priority:** Medium
**Labels:** mvp, analytics, reporting

**Description:**
Create a basic analytics dashboard showing:
- User training progress
- Phishing simulation results
- Company-wide completion rates
- Basic charts and metrics

**Acceptance Criteria:**
- [ ] Dashboard shows completion rates
- [ ] Phishing campaign success rates
- [ ] User progress overview
- [ ] Export data as CSV
- [ ] Real-time updates

**Technical Notes:**
- Use React charts library (already installed)
- Simple SQL queries for metrics
- No need for complex BI tools

---

### Issue #6: Implement Certificate Generation
**Type:** Feature
**Priority:** Medium
**Labels:** mvp, courses, documentation

**Description:**
Generate simple PDF certificates when users complete courses:
- Template-based certificates
- Include user name, course name, date
- Company branding options
- Downloadable PDF format

**Acceptance Criteria:**
- [ ] Generate certificates on course completion
- [ ] Include relevant completion data
- [ ] Allow company logo upload
- [ ] PDF download functionality
- [ ] Store certificates for later access

**Technical Notes:**
- HTML template to PDF
- No need for complex PDF libraries
- Store as files or base64 in DB

---

## Infrastructure & Deployment Issues

### Issue #7: Simplify Deployment to Single Docker Compose
**Type:** Infrastructure
**Priority:** High
**Labels:** deployment, devops, simplification

**Description:**
Consolidate deployment to a single, simple Docker Compose setup:
- One docker-compose.yml file
- Basic nginx configuration
- PostgreSQL with persistent volume
- No complex orchestration

**Acceptance Criteria:**
- [ ] Single docker-compose.yml works for production
- [ ] Data persists across restarts
- [ ] SSL/TLS properly configured
- [ ] Easy to deploy on any VPS

---

### Issue #8: Setup Basic CI/CD Pipeline
**Type:** Infrastructure
**Priority:** Medium
**Labels:** ci-cd, automation, testing

**Description:**
Create simple GitHub Actions workflow:
- Run tests on PR
- Build and push Docker images
- Deploy to production on merge to main
- Basic health checks

**Acceptance Criteria:**
- [ ] Tests run automatically
- [ ] Docker images built and pushed
- [ ] Automatic deployment works
- [ ] Rollback capability exists

---

## Documentation Issues

### Issue #9: Create End-User Documentation
**Type:** Documentation
**Priority:** Medium
**Labels:** documentation, user-guide

**Description:**
Write simple documentation for:
- Company admin guide
- User guide
- API documentation
- Deployment guide

**Acceptance Criteria:**
- [ ] Clear setup instructions
- [ ] User workflows documented
- [ ] API endpoints documented
- [ ] Troubleshooting guide

---

### Issue #10: Write Developer Documentation
**Type:** Documentation
**Priority:** Low
**Labels:** documentation, developer-guide

**Description:**
Document the codebase for future developers:
- Architecture overview
- Database schema
- Development setup
- Contributing guidelines

**Acceptance Criteria:**
- [ ] README is comprehensive
- [ ] Local dev setup works
- [ ] Architecture decisions documented
- [ ] Code style guide exists