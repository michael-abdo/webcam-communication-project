# RTMS-Only Branch Cleanup Plan

## Overview
This document outlines the comprehensive plan to clean up the RTMS-only branch by removing all legacy Phase-1 components (fatigue detection, cognitive assessments, baseline capture) and focusing exclusively on the Real-Time Media Streaming (RTMS) analytics platform.

## Current State Analysis

### Components to Remove
- **Fatigue Detection System**: All video/webcam analysis endpoints
- **Assessment Framework**: Cognitive, bias-resilient, and personality tests  
- **Baseline Capture**: Video recording and baseline measurement systems
- **Legacy Documentation**: Non-RTMS related guides and plans
- **Mixed Codebase**: `app.py` contains both RTMS and fatigue detection code

### Components to Keep
- **RTMS Service**: Real-time media streaming from Zoom
- **Analytics Engine**: Talk time and participation metrics
- **Web Dashboard**: RTMS analytics UI with WebSocket updates
- **API Endpoints**: RTMS webhooks, analytics, and meeting management

## Cleanup Plan

### Phase 1: Core Application Refactoring

#### 1.1 Replace app.py with RTMS-only version
- [ ] Create new `app_rtms_only.py` with clean RTMS implementation
- [ ] Remove all fatigue detection routes:
  - `/api/analyze`
  - `/webcam-analysis`
  - `/text-analysis`
  - `/baseline`
  - `/video_analysis`
- [ ] Remove fatigue-related WebSocket handlers
- [ ] Update application metadata:
  - Title: "RTMS Analytics Platform"
  - Description: Focus on real-time media streaming
- [ ] Backup original app.py before replacement

#### 1.2 Update imports and dependencies
- [ ] Remove unused Python imports
- [ ] Clean up requirements.txt:
  - Remove computer vision libraries (if not used by RTMS)
  - Remove NLP/text analysis packages
  - Keep only RTMS-required dependencies

### Phase 2: Remove Legacy Scripts

#### 2.1 Scripts directory cleanup
Files to remove:
- [ ] `scripts/start_system.py`
- [ ] `scripts/development/validate_deployment.py`
- [ ] `scripts/development/validate_live_deployment.py`
- [ ] `scripts/development/monitor_deployment.py`

#### 2.2 Test files cleanup
- [ ] Remove `tests/test_real_system.py`
- [ ] Review and clean `test-before-deploy.sh`
- [ ] Remove integration tests for fatigue detection
- [ ] Keep only RTMS-specific tests

### Phase 3: Documentation Cleanup

#### 3.1 Remove irrelevant documentation
Documents to remove:
- [ ] `docs/NLP_INTEGRATION.md`
- [ ] `docs/CHATGPT_INTEGRATION.md`
- [ ] `docs/PILOT_PROGRAM.md` (if fatigue-focused)
- [ ] `docs/stages/core_functionality_validation_plan.txt`
- [ ] `docs/planning/REMOVED_FEATURES_DOCUMENTATION.md`
- [ ] Legacy deployment guides not specific to RTMS

#### 3.2 Update remaining documentation
- [ ] Update `README.md` to reflect RTMS-only focus
- [ ] Update `docs/API_REFERENCE.md`:
  - Remove fatigue detection endpoints
  - Document only RTMS/analytics endpoints
- [ ] Update deployment guides for RTMS-specific setup
- [ ] Create new `RTMS_ARCHITECTURE.md` if needed

### Phase 4: Final Verification

#### 4.1 Code verification
- [ ] Search for remaining references:
  ```bash
  grep -r -i "fatigue\|baseline\|cognitive\|assessment" --include="*.py" .
  ```
- [ ] Verify all imports resolve correctly
- [ ] Check for orphaned dependencies

#### 4.2 Functionality testing
- [ ] Test RTMS webhook endpoint
- [ ] Verify analytics dashboard loads
- [ ] Test WebSocket connections
- [ ] Verify Redis pub/sub for analytics
- [ ] Check all API endpoints return expected responses

### Phase 5: Commit and Deploy

#### 5.1 Git operations
- [ ] Stage all changes
- [ ] Create detailed commit message
- [ ] Tag as `rtms-v2.0.0`
- [ ] Push to RTMS-only branch

#### 5.2 Post-cleanup tasks
- [ ] Update CI/CD pipelines if needed
- [ ] Document any breaking changes
- [ ] Update environment variables documentation

## Files Already Removed

### Completed removals:
- ✅ `src/api/blueprints/capture_api.py` (643 lines)
- ✅ `src/api/assessments/` directory
- ✅ `tests/definitions/` (assessment definitions)
- ✅ `docs/pivot_history/` (fatigue detection history)
- ✅ `src/web/templates/tests/`
- ✅ `src/web/templates/dashboard.html`
- ✅ `src/web/templates/stream.html`
- ✅ `src/core_pipeline.py`
- ✅ `src/core/` and `src/data/` directories
- ✅ `tests/integration/test_baseline_demo.html`

## Success Metrics

1. **Clean Codebase**: No references to fatigue/cognitive/assessment in Python files
2. **Focused Documentation**: All docs relate to RTMS functionality
3. **Working Platform**: RTMS dashboard and analytics fully operational
4. **Reduced Size**: Significant reduction in codebase size (target: 500k+ lines removed)
5. **Clear Purpose**: Repository clearly focused on RTMS analytics

## Risk Mitigation

1. **Backup Strategy**: Keep original files in separate backup branch
2. **Incremental Testing**: Test after each major removal
3. **Dependency Check**: Verify no RTMS code depends on removed components
4. **Rollback Plan**: Tag stable version before major changes

## Timeline

- **Phase 1**: 1-2 hours (Application refactoring)
- **Phase 2**: 30 minutes (Script cleanup)
- **Phase 3**: 1 hour (Documentation cleanup)
- **Phase 4**: 30 minutes (Verification)
- **Phase 5**: 30 minutes (Commit and deploy)

**Total estimated time**: 3-4 hours

## Next Steps

1. Review and approve this plan
2. Create backup branch from current state
3. Execute cleanup in phases
4. Test thoroughly between phases
5. Deploy clean RTMS-only version

---

*Last updated: October 29, 2024*
*Status: Planning Phase*