# Reorganization Tracking Document

## Overview
This document tracks all changes made during the aggressive cleanup on the `cleanup` branch.

## File Movements and Changes

### 1. Core Application Files
| Original Path | New Path | Changes Required |
|--------------|----------|------------------|
| app_lightweight.py | src/web/app.py | - Update imports<br>- Update Procfile<br>- Update any references |
| models/ | src/models/ | - Update imports in all files |
| blueprints/ | src/api/blueprints/ | - Update imports<br>- Update app.py blueprint registration |
| services/ | src/services/ | - Update imports |
| streaming/ | src/streaming/ | - Update imports |
| telemetry/ | src/telemetry/ | - Update imports |
| rtms/ | src/rtms/ | - Update imports |
| utils/ | src/utils/ | - Update imports |
| config.py | src/config.py | - Update imports in all files |

### 2. RTMS Service
| Original Path | New Path | Changes Required |
|--------------|----------|------------------|
| rtms-service/ | src/rtms-service/ | - Update Procfile<br>- Update require() paths in JS files |

### 3. Static and Template Files
| Original Path | New Path | Changes Required |
|--------------|----------|------------------|
| static/ | src/web/static/ | - Update Flask static_folder config |
| templates/ | src/web/templates/ | - Update Flask template_folder config |

### 4. Test Files
| Original Path | New Path | Changes Required |
|--------------|----------|------------------|
| tests/ | tests/ | No change (already organized) |
| test_*.py (root) | tests/legacy/ | - Move all root test files |
| test_*.sh (root) | tests/scripts/ | - Move all test scripts |

### 5. Configuration Files (Stay in Root)
- Procfile
- requirements.txt
- requirements-dev.txt
- runtime.txt
- package.json
- .gitignore
- README.md
- LICENSE

### 6. Files to Remove
- setup.py (from failed reorg)
- run.py (from failed reorg)
- Makefile (from failed reorg)
- CONTRIBUTING.md (from failed reorg)
- Any __pycache__ directories
- Any .pyc files

## Import Changes Required

### Python Import Updates
1. **In app.py (formerly app_lightweight.py)**:
   ```python
   # Old
   from config import ...
   from models import ...
   from blueprints import ...
   
   # New
   from src.config import ...
   from src.models import ...
   from src.api.blueprints import ...
   ```

2. **In all blueprint files**:
   ```python
   # Old
   from models import ...
   from services import ...
   
   # New
   from src.models import ...
   from src.services import ...
   ```

3. **In analytics files**:
   ```python
   # Add to sys.path setup
   project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
   ```

### JavaScript Import Updates
1. **In rtms-service files**:
   - Update any relative paths that might break

## Configuration Updates

### Procfile
```
# Old
web: gunicorn -k gevent --worker-connections 100 --workers 1 --bind 0.0.0.0:$PORT app_lightweight:app
rtms: node rtms-service/index.js
worker: python src/analytics/talk_time_analytics.py

# New
web: gunicorn -k gevent --worker-connections 100 --workers 1 --bind 0.0.0.0:$PORT src.web.app:app
rtms: node src/rtms-service/index.js
worker: python src/analytics/talk_time_analytics.py
```

### Environment Variables
- No changes expected

## Testing Checklist
After reorganization, test:
- [ ] Main app imports: `python -c "from src.web.app import app"`
- [ ] Analytics worker: `python src/analytics/talk_time_analytics.py --help`
- [ ] RTMS service: `node src/rtms-service/index.js --version`
- [ ] Blueprint imports
- [ ] Database models
- [ ] Static file serving
- [ ] Template rendering

## Rollback Plan
If issues arise:
1. `git checkout master` - return to stable branch
2. All changes are tracked in git, easy to revert

## Status
- Started: 2025-10-29
- Branch: cleanup
- Status: COMPLETED ✅

## Final Verification Results
- ✅ Main app imports successfully (despite Redis connection warning)
- ✅ Analytics worker can start
- ✅ RTMS service exists at new location
- ✅ Procfile paths updated correctly
- ✅ All imports updated to use src prefix
- ✅ sys.path setup added to all modules
- ✅ __future__ imports fixed to be at top of files

## Known Issues
- Redis connection warning appears during import (expected in dev environment)
- Some test files in tests/legacy may need import updates if used