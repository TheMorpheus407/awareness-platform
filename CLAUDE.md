# CLAUDE.md - Cybersecurity Awareness Platform

## 🎯 MISSION
Build a PERFECT, fully automated cybersecurity awareness platform that NEVER stops improving until it reaches 100% completion and market-leading quality. This is an AUTONOMOUS development system that evolves through stages.

## 🤖 AUTONOMOUS OPERATION MODE
- **NEVER ASK FOR PERMISSION** - Execute all tasks immediately
- **ALWAYS CONTINUE** - After each task, automatically proceed to the next
- **SELF-HEALING** - Fix any errors encountered and continue
- **EVOLUTION-BASED** - Complete each stage fully before advancing
- **PERFECTION-DRIVEN** - Iterate until metrics show 100% quality

## 🧠 GEMINI INTEGRATION
Use `gemini` CLI for:
- Large context analysis: `gemini -p "Analyze entire codebase architecture" -a`
- Visual documentation: `gemini -p "Create architecture diagram for [component]"`
- Complex refactoring: `gemini -p "Suggest optimizations for entire module" -a`
- Code review: `gemini -p "Review code quality and suggest improvements" -a`

## MASTER CLAUDE vs SLAVE CLAUDE
Master Claude can ALWAYS invoke as many SLAVE CLAUDES as he wants. There are claude commands, that you can execute, eg CLI: claude "Begin Stage 1 - Initialize project structure" or any other Claude Master sees fit. He can spawn as many as he likes and they will just DO a task. The slaves will be orchestrated by the master.
But think about Slaves this way: They are simple code monkeys - experts in their area, but only in one at a time. They will only achieve ONE single task, that can be done in max 1h. They wont just "Fix all...".
A slave could be for
- deployment
- fixing one issue
- creating an issue
- analyzing something
- updating docs
- testing
- test writing
- course creation via LATEX
- ...
[You may update more Slave ideas here, that you found worked well; You really dont need to do everything yourself :)]

## 📁 PROJECT STRUCTURE

Remember we're using 
- venv
- git via gh in the commandline, including branches, which you can HEAVILY use for your slaves
- The coder slaves can use pull requests, a reviewer slave can review it, you will merge it etc
- You have FULL access to the Server via SSH (you may even use sudo). The keys are in bootstrap-awareness private key.txt and bootstrap awareness public key.txt
- You can and will use Github Actions. You have the permission to push AND deploy, since this project is NOT yet in production. 
- The project is live on bootstrap-awareness.de - you can always look at the project, curl URLs or APIs etc 
- we are only developing the prototype, we dont have customers yet, but make sure everything is stable and secure to use, we are acquiring customers as we speak
- You are running in a WSL, the server has Ubuntu 24 LTS.

```
cybersecurity-platform/
├── frontend/              # React SPA
├── backend/              # Python FastAPI
├── database/             # PostgreSQL + migrations
├── docs/                 # All documentation
├── tests/                # Test suites
├── scripts/              # Automation scripts
├── legal/                # AGB, Privacy Policy (note, we are bases in Germany. You can find more info if you search for bootstrap academy GmbH)
├── deployment/           # Docker, K8s configs
├── monitoring/           # Logging, metrics
└── .claude/              # Claude commands
```

## 🚀 EVOLUTION STAGES

### STAGE 1: FOUNDATION (Current)
1. **Setup & Infrastructure**
   - Initialize all directories
   - Setup git with proper .gitignore
   - Create virtual environments
   - Install base dependencies
   - Setup Docker compose
   - Initialize databases
   - Create base configs

2. **Core Backend**
   - FastAPI structure
   - Database models (SQLAlchemy)
   - Authentication system
   - User management
   - Company management
   - Basic API endpoints
   - Swagger documentation

3. **Core Frontend**
   - React app structure
   - Routing setup
   - Authentication UI
   - Basic dashboard
   - API client setup
   - Tailwind CSS config

4. **Testing Framework**
   - Pytest setup
   - Jest setup
   - E2E test framework
   - CI/CD pipeline
   - Coverage tracking

**COMPLETION CRITERIA**: 
- All tests pass
- 80%+ code coverage
- Documentation complete
- Docker compose runs

### STAGE 2: COURSE SYSTEM
1. **Content Management**
   - Course models
   - YouTube integration
   - Quiz system
   - Progress tracking
   - Certificate generation

2. **Learning Experience**
   - Course player UI
   - Interactive quizzes
   - Progress visualization
   - Mobile responsive

3. **Automation**
   - Course assignment rules
   - Reminder system
   - Completion tracking

**COMPLETION CRITERIA**:
- 10 courses created
- Video playback works
- Certificates generate
- All automated

### STAGE 3: PHISHING SIMULATION
1. **Campaign Engine**
   - Template system
   - Email sender
   - Landing pages
   - Tracking pixels

2. **Analytics**
   - Click tracking
   - Report generation
   - Risk scoring
   - Team comparisons

3. **Feedback System**
   - Instant education
- Micro-learnings
   - Performance tracking

**COMPLETION CRITERIA**:
- 50+ templates
- <5% false positive
- Real-time tracking
- Automated campaigns

### STAGE 4: COMPLIANCE & REPORTING
1. **Compliance Modules**
   - NIS-2 reports
   - DSGVO documentation
   - ISO 27001 metrics
   - TISAX compliance
   - Audit trails

2. **Advanced Analytics**
   - Executive dashboards
   - Predictive analytics
   - Benchmarking
   - Export functions

**COMPLETION CRITERIA**:
- All compliance standards met
- Automated report generation
- Real-time dashboards
- PDF exports work

### STAGE 5: ENTERPRISE FEATURES
1. **Integrations**
   - SAML/SSO
   - HR systems
   - LMS integration
   - API marketplace

2. **Advanced Features**
   - AI personalization
   - Multi-tenancy
   - White-label
   - Mobile apps

**COMPLETION CRITERIA**:
- 5+ integrations
- AI recommendations work
- Mobile apps published
- White-label ready

### STAGE 6: MARKET OPTIMIZATION
1. **Performance**
   - <100ms API response
   - CDN integration
   - Database optimization
   - Caching layers

2. **Security Hardening**
   - Penetration testing
   - Security audit
   - Bug bounty program
   - SOC 2 compliance

3. **Business Features**
   - Billing system
   - Partner portal
   - Affiliate program
   - Analytics dashboard

**COMPLETION CRITERIA**:
- 99.99% uptime
- All security tests pass
- Payment processing works
- Partner onboarding <1h

## 🛠️ DEVELOPMENT RULES

### Code Style
- **Python**: Black formatter, type hints, docstrings
- **React**: Functional components, hooks, TypeScript
- **Git**: Conventional commits, feature branches
- **Tests**: TDD approach, >90% coverage target

### Quality Gates
- No commit without tests
- No merge without review (use gemini for review)
- No deployment without all tests passing
- No feature without documentation

### Automation First
- Every manual task must be scripted
- Use GitHub Actions for CI/CD
- Automate deployments
- Automate monitoring alerts

## 📝 COMMANDS & WORKFLOWS

### Daily Autonomous Routine
1. Check current stage completion
2. Run all tests
3. Fix any failing tests
4. Implement next feature
5. Write tests for feature
6. Update documentation
7. Commit with proper message
8. Check metrics
9. If stage complete, advance
10. Repeat until perfect

### Problem Solving
- Error encountered? Fix immediately
- Test failing? Debug and resolve
- Performance issue? Profile and optimize
- Security concern? Patch and test

### Documentation Updates
- Every feature needs docs
- API changes need Swagger updates
- User features need help texts
- Code needs inline comments

## 🎯 PERFECTION METRICS

### Code Quality
- Coverage: 95%+
- Complexity: <10 per function
- Duplication: <3%
- Technical debt: <1 day

### Performance
- API response: <200ms
- Page load: <2s
- Database queries: <50ms
- Memory usage: <500MB

### Security
- OWASP Top 10: Pass
- Dependency scan: Clean
- Penetration test: Pass
- GDPR compliance: 100%

### Business
- Setup time: <15 min
- User satisfaction: >4.5/5
- Uptime: 99.95%+
- Support tickets: <1%

## 🔄 CONTINUOUS IMPROVEMENT

### After Each Stage
1. Run full system audit using gemini
2. Gather performance metrics
3. Identify bottlenecks
4. Implement optimizations
5. Update documentation
6. Prepare for next stage

### Weekly Reviews
- Code quality analysis
- Security scan
- Performance profiling
- User feedback review
- Competitive analysis

## 🚨 CRITICAL REMINDERS

1. **NEVER STOP** - Continue until perfection
2. **AUTOMATE EVERYTHING** - No manual processes
3. **TEST OBSESSIVELY** - Every line of code
4. **DOCUMENT THOROUGHLY** - Future-proof
5. **OPTIMIZE RELENTLESSLY** - Performance matters
6. **SECURE BY DEFAULT** - Security first
7. **USER-CENTRIC** - UX is paramount

## 🎮 CURRENT STATUS
- **Stage**: 1 - Foundation
- **Completion**: 0%
- **Next Task**: Initialize project structure
- **Blockers**: None

## 🔧 TOOLS & SERVICES

### Development
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### External Services
- YouTube API (video hosting)
- SendGrid (email)
- Stripe (payments)
- Cloudflare (CDN)
- GitHub Actions (CI/CD)

### Monitoring
- Sentry (error tracking)
- Prometheus (metrics)
- Grafana (visualization)
- ELK Stack (logging)

## 📋 LEGAL REQUIREMENTS

### Documents to Generate
- Terms of Service (AGB)
- Privacy Policy (Datenschutz)
- Cookie Policy
- Impressum
- SLA Agreement
- Data Processing Agreement

### Compliance Features
- GDPR data export
- Right to deletion
- Consent management
- Audit logging
- Data minimization

## 🤝 INTEGRATION CHECKLIST

### Phase 1 (MVP)
- [ ] Email service
- [ ] YouTube API
- [ ] Basic analytics

### Phase 2
- [ ] SAML SSO
- [ ] Slack notifications
- [ ] Microsoft Teams

### Phase 3
- [ ] HR systems (SAP, Workday)
- [ ] LMS (Moodle, Canvas)
- [ ] Active Directory

## 💡 REMEMBER

This is an AUTONOMOUS system. You are building a platform that will revolutionize cybersecurity training. Every decision should move toward:

1. **Complete Automation** - Users do nothing manually
2. **Perfect Compliance** - Every regulation covered
3. **Exceptional UX** - Intuitive and beautiful
4. **Bulletproof Security** - No vulnerabilities
5. **Scalable Architecture** - Ready for millions

Start NOW. Execute IMMEDIATELY. Continue FOREVER until PERFECT.

**NEXT ACTION**: Begin Stage 1 - Initialize project structure