# GitHub Issues - Simplification Tasks

## Critical Cleanup Issues

### Issue #1: Fix Project Structure - Remove Duplicate Directories
**Type:** Bug
**Priority:** Critical
**Labels:** tech-debt, cleanup, blocking

**Description:**
The project has severe structural issues with duplicate directories:
- `/backend/backend/` - backend folder nested inside itself
- `/frontend/backend/` - backend folder inside frontend
- Multiple duplicate Python modules at root level

**Tasks:**
- [ ] Move all backend code to single `/backend` directory
- [ ] Remove `/backend/backend/` duplicate
- [ ] Remove `/frontend/backend/` entirely
- [ ] Move root-level Python modules (`/api`, `/core`, `/models`) into `/backend`
- [ ] Update all import statements
- [ ] Update Docker configurations
- [ ] Test everything still works

**Impact:** This is blocking proper development and causing massive confusion.

---

### Issue #2: Consolidate Test Files and Structure
**Type:** Tech Debt
**Priority:** High
**Labels:** testing, cleanup, tech-debt

**Description:**
Tests are scattered across multiple locations with duplicates:
- 8+ versions of `test_auth.py` in different directories
- 3 different `conftest.py` files
- 3 different `pytest.ini` files
- Tests in `/tests`, `/backend/tests`, and `/frontend/backend/tests`

**Tasks:**
- [ ] Choose single test location: `/backend/tests`
- [ ] Merge duplicate test files
- [ ] Create single `conftest.py`
- [ ] Create single `pytest.ini`
- [ ] Remove all duplicate test files
- [ ] Ensure all tests still pass

**Expected Outcome:** Single, clean test structure that's easy to maintain.

---

### Issue #3: Remove Technical Debt Fix Scripts
**Type:** Tech Debt
**Priority:** High
**Labels:** cleanup, tech-debt, code-quality

**Description:**
10+ "fix" scripts indicate band-aid solutions:
- `fix_2fa_field_names.py`
- `fix_field_mismatches.py`
- `fix_all_migration_issues.py`
- And 7 more...

**Tasks:**
- [ ] Understand what each fix script does
- [ ] Apply fixes properly to source code
- [ ] Update database migrations properly
- [ ] Delete all fix_*.py scripts
- [ ] Document any permanent changes made

**Note:** These scripts suggest rushed development. Let's fix issues properly.

---

### Issue #4: Simplify Dependencies - Remove Unnecessary Packages
**Type:** Tech Debt
**Priority:** High
**Labels:** dependencies, performance, simplification

**Description:**
Backend has 66+ dependencies when ~20 would suffice. Remove:
- Stripe (no payment processing in MVP)
- Celery + Redis (premature optimization)
- Boto3/S3 (local storage is fine)
- Sentry (overkill for current stage)
- Prometheus + Grafana (too complex)
- ReportLab (use simple HTML->PDF)

**Tasks:**
- [ ] Remove unused dependencies from requirements.txt
- [ ] Remove related code/imports
- [ ] Update Docker images
- [ ] Test everything still works
- [ ] Document why each remaining dependency is needed

**Expected Savings:** Faster builds, smaller images, less complexity.

---

### Issue #5: Consolidate Docker Configuration
**Type:** Tech Debt
**Priority:** Medium
**Labels:** docker, devops, simplification

**Description:**
Multiple Docker configurations exist:
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `docker-compose.dev.yml`
- Multiple Dockerfiles

**Tasks:**
- [ ] Create single `docker-compose.yml` with override files
- [ ] Merge Dockerfile configurations
- [ ] Remove redundant configurations
- [ ] Simplify environment variable handling
- [ ] Test both dev and prod setups work

---

### Issue #6: Simplify Database Migrations
**Type:** Tech Debt
**Priority:** Medium
**Labels:** database, migrations, cleanup

**Description:**
Migration files show signs of issues:
- Multiple fix migrations
- Conflicting enum types
- UUID type problems
- Missing indexes added later

**Tasks:**
- [ ] Squash migrations into clean set
- [ ] Fix all type issues properly
- [ ] Ensure indexes are in initial migrations
- [ ] Test fresh database creation
- [ ] Document migration strategy

---

### Issue #7: Remove Premature Microservice Patterns
**Type:** Tech Debt
**Priority:** Medium
**Labels:** architecture, simplification, monolith

**Description:**
Code shows premature microservice patterns:
- Too many service layers
- Over-abstracted interfaces
- Unnecessary async everywhere
- Complex dependency injection

**Tasks:**
- [ ] Simplify service layer to single level
- [ ] Remove unnecessary abstractions
- [ ] Use async only where beneficial
- [ ] Simplify dependency injection
- [ ] Keep it monolithic until scale demands otherwise

---

### Issue #8: Clean Up Frontend Dependencies
**Type:** Tech Debt
**Priority:** Low
**Labels:** frontend, dependencies, cleanup

**Description:**
Frontend has duplicate UI component libraries:
- Custom UI components
- Headless UI
- Multiple icon libraries
- Duplicate form libraries

**Tasks:**
- [ ] Choose single UI component approach
- [ ] Remove duplicate libraries
- [ ] Consolidate icon usage
- [ ] Update all components
- [ ] Ensure consistent UI

---

### Issue #9: Simplify Monitoring and Logging
**Type:** Tech Debt
**Priority:** Low
**Labels:** monitoring, logging, simplification

**Description:**
Current monitoring is overly complex:
- Prometheus + Grafana
- Sentry error tracking
- Custom monitoring endpoints
- Multiple logging libraries

**Tasks:**
- [ ] Remove Prometheus/Grafana
- [ ] Remove Sentry
- [ ] Use simple Python logging
- [ ] Add basic health check endpoint
- [ ] Log to files with rotation

**Note:** Can add complex monitoring when actually needed.

---

### Issue #10: Create Single Source of Configuration
**Type:** Tech Debt
**Priority:** Medium
**Labels:** configuration, environment, cleanup

**Description:**
Configuration is scattered:
- Multiple .env files
- Configuration in code
- Docker environment variables
- No clear precedence

**Tasks:**
- [ ] Create single .env.example
- [ ] Document all environment variables
- [ ] Centralize configuration loading
- [ ] Remove duplicate config files
- [ ] Clear precedence rules

---

## Process Improvement Issues

### Issue #11: Establish Clear Development Workflow
**Type:** Process
**Priority:** High
**Labels:** process, documentation, workflow

**Description:**
Establish clear, simple development workflow:
- No more fix scripts
- Proper PR process
- Testing requirements
- Deployment checklist

**Tasks:**
- [ ] Document PR process
- [ ] Require tests for new features
- [ ] Setup pre-commit hooks
- [ ] Create deployment checklist
- [ ] Train team on process

---

### Issue #12: Implement "YAGNI" Principle
**Type:** Process
**Priority:** Medium
**Labels:** process, architecture, principles

**Description:**
Establish "You Aren't Gonna Need It" as core principle:
- Document what features are actually needed
- Remove speculative features
- Simplify before adding complexity
- Regular complexity reviews

**Tasks:**
- [ ] Document MVP requirements clearly
- [ ] Remove non-MVP code
- [ ] Create complexity budget
- [ ] Regular simplification reviews
- [ ] Educate team on YAGNI