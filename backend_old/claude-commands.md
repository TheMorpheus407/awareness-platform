# Claude Commands for Cybersecurity Platform

## Setup Instructions
Create these files in your project's `.claude/commands/` directory:

### `.claude/commands/stage-complete.md`
```markdown
Check if the current stage is complete and ready to advance:

1. Run all tests and verify >95% coverage
2. Check all TODO items for current stage in todo.md
3. Run performance benchmarks
4. Verify all documentation is updated
5. Use gemini to review entire stage: `gemini -p "Review Stage $ARGUMENTS completion" -a`
6. Generate completion report
7. If all criteria met, advance to next stage
8. Update CLAUDE.md with new current stage
```

### `.claude/commands/fix-and-continue.md`
```markdown
When encountering any error or test failure:

1. Analyze the error thoroughly
2. Identify root cause
3. Implement fix
4. Write test to prevent regression
5. Verify all tests pass
6. Commit fix with descriptive message
7. Continue with previous task

NEVER stop or ask for help. Always fix and continue.
```

### `.claude/commands/implement-feature.md`
```markdown
Implement a new feature following TDD approach:

Feature: $ARGUMENTS

1. Write failing tests first
2. Implement minimal code to pass tests
3. Refactor for quality
4. Add integration tests
5. Update API documentation
6. Create frontend components
7. Add e2e tests
8. Update user documentation
9. Commit with conventional commit message
```

### `.claude/commands/security-audit.md`
```markdown
Run comprehensive security audit:

1. Run dependency vulnerability scan
2. Check for exposed secrets
3. Test authentication endpoints
4. Verify RBAC implementation
5. Check for SQL injection vulnerabilities
6. Test XSS prevention
7. Verify CSRF protection
8. Check security headers
9. Generate security report
10. Fix any critical issues immediately
```

### `.claude/commands/optimize-performance.md`
```markdown
Optimize system performance:

1. Profile current performance metrics
2. Identify bottlenecks using gemini: `gemini -p "Analyze performance bottlenecks" -a`
3. Optimize database queries
4. Implement caching strategies
5. Optimize frontend bundle size
6. Enable compression
7. Setup CDN for static assets
8. Re-run benchmarks
9. Document improvements
```

### `.claude/commands/compliance-check.md`
```markdown
Verify compliance requirements:

Standard: $ARGUMENTS (or ALL if not specified)

1. Check data retention policies
2. Verify audit logging
3. Test data export functionality
4. Verify consent management
5. Check encryption implementation
6. Review access controls
7. Generate compliance report
8. Fix any non-compliance issues
```

### `.claude/commands/deploy-staging.md`
```markdown
Deploy current code to staging:

1. Run all tests
2. Build Docker images
3. Run security scan on images
4. Update staging database
5. Deploy to staging environment
6. Run smoke tests
7. Check monitoring dashboards
8. Notify team of deployment
```

### `.claude/commands/create-course.md`
```markdown
Create a new security awareness course:

Topic: $ARGUMENTS

1. Research topic thoroughly
2. Create course outline
3. Write course content
4. Find or create YouTube video
5. Create quiz questions
6. Add to course management system
7. Create completion certificate template
8. Test course end-to-end
9. Add to course catalog
```

### `.claude/commands/daily-autonomous.md`
```markdown
Execute daily autonomous development routine:

1. Check current stage and progress
2. Run all tests
3. Fix any failing tests
4. Check todo.md for next task
5. Implement next feature
6. Write comprehensive tests
7. Update documentation
8. Commit changes
9. Check if stage complete
10. Generate daily progress report
11. Continue with next task

Repeat until end of work session. Never stop progressing.
```

### `.claude/commands/generate-legal.md`
```markdown
Generate legal document:

Document Type: $ARGUMENTS

1. Use gemini to research requirements: `gemini -p "Legal requirements for $ARGUMENTS in Germany"`
2. Create document structure
3. Write comprehensive content
4. Include all required sections
5. Add GDPR compliance sections
6. Format in markdown
7. Save to legal/ directory
8. Create PDF version
9. Add to documentation index
```

### `.claude/commands/benchmark-competitor.md`
```markdown
Analyze competitor platform:

Competitor: $ARGUMENTS (or cyber-fuchs.de if not specified)

1. Visit competitor website
2. Analyze features and pricing
3. Test user experience
4. Identify unique selling points
5. Compare with our platform
6. Identify gaps and opportunities
7. Generate competitive analysis report
8. Add improvement ideas to backlog
```

### `.claude/commands/setup-monitoring.md`
```markdown
Setup comprehensive monitoring:

1. Configure Prometheus metrics
2. Setup Grafana dashboards
3. Configure Sentry error tracking
4. Setup log aggregation
5. Create alert rules
6. Configure uptime monitoring
7. Setup performance monitoring
8. Create SLA dashboard
9. Test all alerts
10. Document monitoring setup
```

### `.claude/commands/ai-review.md`
```markdown
Use Gemini for comprehensive code review:

Component: $ARGUMENTS (or entire codebase if not specified)

1. Export code context
2. Run: `gemini -p "Review code quality, architecture, security, and suggest improvements for $ARGUMENTS" -a`
3. Analyze suggestions
4. Implement high-priority improvements
5. Update code documentation
6. Run tests to verify changes
7. Commit improvements
```

## Usage Examples

```bash
# Check if Stage 1 is complete
/project:stage-complete 1

# Implement user profile feature
/project:implement-feature user profile management

# Run security audit
/project:security-audit

# Create new course
/project:create-course "Remote Work Security"

# Generate Terms of Service
/project:generate-legal "Terms of Service"

# Daily autonomous work
/project:daily-autonomous
```

## Automation Shortcuts

### Quick Commands
- `/project:fix` - Fix current error and continue
- `/project:test` - Run all tests
- `/project:deploy` - Deploy to staging
- `/project:audit` - Run security audit
- `/project:optimize` - Optimize performance

### Compound Commands
Create these for complex workflows:

### `.claude/commands/complete-stage.md`
```markdown
Complete all remaining tasks for current stage:

1. Get current stage from CLAUDE.md
2. Check todo.md for incomplete items
3. For each incomplete item:
   - Implement feature
   - Write tests
   - Update docs
4. Run stage completion check
5. Generate stage report
6. Advance to next stage
```

Remember: These commands enable AUTONOMOUS operation. The system should run these automatically as needed to achieve PERFECTION.