# Project Restructuring Plan - Cybersecurity Awareness Platform

## 🚨 Critical Issues Identified

### 1. Structural Problems
- **Backend Duplication**: Code is in `/backend/` instead of root, creating confusion
- **Multiple Project Copies**: `cybersecurity-platform/` folder contains duplicate implementation
- **Scattered Documentation**: 5+ locations with conflicting information
- **No Single Source of Truth**: Multiple READMEs, specs, and configs

### 2. Missing Critical Information
- SSH key location and usage instructions
- Email service configuration
- GitHub repository access details
- Production server credentials
- Clear deployment procedures

## 🎯 Restructuring Goals

1. **Single Source of Truth**: One location for each type of content
2. **Clear Hierarchy**: Logical folder structure without duplication
3. **Complete Documentation**: All credentials and procedures documented
4. **Clean Codebase**: Remove duplicates and obsolete files
5. **Professional Structure**: Industry-standard layout

## 📁 New Project Structure

```
AwarenessSchulungen/
├── README.md                    # Single project overview
├── ARCHITECTURE.md              # System architecture
├── DEPLOYMENT.md               # Complete deployment guide
├── DEVELOPMENT.md              # Development setup
├── ROADMAP.md                  # Future development plans
├── .env.example                # Single environment template
├── .gitignore
├── docker-compose.yml          # Development compose
├── docker-compose.prod.yml     # Production compose
│
├── backend/                    # FastAPI backend (no nesting!)
│   ├── alembic/               # Database migrations
│   ├── api/                   # API endpoints
│   ├── core/                  # Core functionality
│   ├── models/                # Database models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   ├── tests/                 # Backend tests
│   ├── main.py               # Application entry
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container
│
├── frontend/                   # React frontend
│   ├── public/                # Static assets
│   ├── src/                   # Source code
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   ├── hooks/           # Custom hooks
│   │   ├── types/           # TypeScript types
│   │   └── utils/           # Utilities
│   ├── package.json          # Node dependencies
│   ├── Dockerfile           # Frontend container
│   └── vite.config.ts       # Build configuration
│
├── infrastructure/            # All deployment configs
│   ├── nginx/                # Web server configs
│   ├── scripts/              # Deployment scripts
│   ├── kubernetes/           # K8s manifests
│   └── monitoring/           # Monitoring configs
│
├── docs/                     # All documentation
│   ├── api/                  # API documentation
│   ├── guides/               # User guides
│   ├── legal/                # Legal documents
│   └── technical/            # Technical specs
│
└── .github/                  # GitHub specific
    ├── workflows/            # CI/CD pipelines
    └── ISSUE_TEMPLATE/      # Issue templates
```

## 🔄 Migration Steps

### Phase 1: Analysis & Backup (Current)
1. Complete analysis of all duplicates
2. Create backup of entire project
3. Document all findings
4. Map file movements

### Phase 2: Structure Creation
1. Create new folder structure
2. Move backend code from `/backend/backend/` to `/backend/`
3. Consolidate frontend code
4. Merge documentation

### Phase 3: Cleanup
1. Remove `cybersecurity-platform/` folder
2. Delete duplicate files
3. Clean up old configs
4. Remove obsolete scripts

### Phase 4: Documentation
1. Create single README.md
2. Document all credentials
3. Write deployment guide
4. Update todo.md

### Phase 5: Validation
1. Test all functionality
2. Verify deployment works
3. Check all links
4. Final cleanup

## 📋 Immediate Actions

1. **Backup Everything**: Create complete project backup
2. **Analyze Duplicates**: Compare all duplicate files
3. **Plan Movements**: Map every file to new location
4. **Execute Migration**: Move files systematically
5. **Update References**: Fix all import paths
6. **Test Everything**: Ensure nothing breaks

## ⚠️ Risk Mitigation

- Create full backup before any changes
- Test each step in isolation
- Keep detailed logs of all changes
- Have rollback plan ready
- Test deployment after each phase

## 📊 Success Criteria

- [ ] Single backend folder at root level
- [ ] No duplicate code or documentation
- [ ] All credentials documented in one place
- [ ] Clear deployment instructions
- [ ] Working CI/CD pipeline
- [ ] Clean git history
- [ ] Professional project structure

## 🚀 Let's Begin!

This plan will transform the chaotic current structure into a clean, professional project that's easy to maintain and deploy.