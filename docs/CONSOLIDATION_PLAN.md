# Webcam Project Consolidation Plan

## Current State Analysis

### Redundant Python Files:
1. **camera_status_dashboard.py** - Separate camera monitoring app (7 routes)
2. **integrated_fatigue_system.py** - Integrated fatigue system (6 routes)  
3. **enforced_dashboard.py** - Enforced dashboard (8 routes)

### Main App (app_lightweight.py):
- Already contains all necessary functionality
- Has 17 routes including all features
- Duplicate `/api/analyze` routes at lines 186 and 344

### Templates:
- **Keep**: dashboard.html, text_analysis.html, video_analysis.html, webcam_analysis.html, demo.html
- **Remove**: video_analysis_backup.html (backup file)

## Consolidation Actions:

### 1. Remove Redundant Files:
- Delete camera_tools/dashboards/camera_status_dashboard.py
- Delete integrated_fatigue_system.py
- Delete enforced_dashboard.py
- Delete templates/video_analysis_backup.html

### 2. Fix app_lightweight.py:
- Remove duplicate `/api/analyze` route (keep the one at line 186)

### 3. Streamline Pages:
The app will have these core pages:
- **/** - Home page
- **/dashboard** - Main fatigue monitoring dashboard
- **/webcam-analysis** - Live webcam analysis with NLP
- **/text-analysis** - Text-based cognitive load analysis
- **/video-analysis** - Batch video dataset analysis
- **/demo** - Simple demo interface for testing

### 4. Benefits:
- Reduced complexity and maintenance
- Single deployment artifact
- No conflicting routes or functionality
- Cleaner codebase