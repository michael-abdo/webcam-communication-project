# 🎥 Camera Tools Suite

A comprehensive collection of camera health monitoring, diagnostics, and testing tools for webcam applications.

## 📁 Directory Structure

```
camera_tools/
├── health_monitoring/      # Real-time camera health monitoring
├── diagnostics/           # Camera diagnostics and permissions
├── dashboards/           # Web-based monitoring dashboards
├── tests/               # Camera testing and quality assessment
├── output/              # Test results and captured frames
└── README.md           # This file
```

## 🛠️ Available Tools

### 1. Health Monitoring (`health_monitoring/`)

#### `webcam_health_monitor.py`
Comprehensive webcam health monitoring and continuous surveillance.

**Features:**
- Camera enumeration and detection
- Real-time health status monitoring
- Performance metrics tracking
- Continuous monitoring mode

**Usage:**
```bash
cd camera_tools/health_monitoring
python webcam_health_monitor.py
```

### 2. Diagnostics (`diagnostics/`)

#### `camera_diagnostics.py`
Deep camera system analysis and troubleshooting.

**Features:**
- Connectivity testing
- Camera properties analysis
- Frame capture analysis
- Multi-format compatibility testing
- Alternative backend testing

**Usage:**
```bash
cd camera_tools/diagnostics
python camera_diagnostics.py
```

#### `check_camera_permissions.py`
Platform-specific camera permissions verification.

**Features:**
- OS-specific permission checks
- Manual verification guides
- Direct camera access testing
- Troubleshooting recommendations

**Usage:**
```bash
cd camera_tools/diagnostics
python check_camera_permissions.py
```

### 3. Dashboards (`dashboards/`)

#### `camera_status_dashboard.py`
Real-time web-based camera monitoring dashboard with live video streaming.

**Features:**
- Live video feed streaming
- Real-time camera status display
- Metrics visualization and tracking
- Historical data analysis
- Web API endpoints
- Single-source camera architecture (no resource conflicts)

**Usage:**
```bash
cd camera_tools/dashboards
python camera_status_dashboard.py
# Access at: http://localhost:5002
```

### 4. Tests (`tests/`)

#### `quick_camera_test.py`
Quick camera functionality verification.

**Features:**
- Camera detection
- Frame capture testing
- Basic metrics display
- Test frame saving

**Usage:**
```bash
cd camera_tools/tests
python quick_camera_test.py
```

#### `camera_quality_test.py`
Comprehensive camera quality assessment.

**Features:**
- Resolution support testing
- FPS consistency analysis
- Image quality metrics
- Low light performance
- Autofocus testing

**Usage:**
```bash
cd camera_tools/tests
python camera_quality_test.py
```

## 🚀 Quick Start

1. **Check Camera Availability:**
   ```bash
   cd camera_tools/tests
   python quick_camera_test.py
   ```

2. **Verify Permissions:**
   ```bash
   cd camera_tools/diagnostics
   python check_camera_permissions.py
   ```

3. **Run Full Diagnostics:**
   ```bash
   cd camera_tools/diagnostics
   python camera_diagnostics.py
   ```

4. **Start Monitoring Dashboard:**
   ```bash
   cd camera_tools/dashboards
   python camera_status_dashboard.py
   ```

## 📊 Output Files

All test results and captured frames are saved to the `output/` directory:
- `camera_*_test_frame.jpg` - Test frames from cameras
- `camera_quality_report_*.json` - Detailed quality test results

## 🔧 Requirements

- Python 3.7+
- OpenCV (cv2)
- NumPy
- Flask (for dashboards)

Install dependencies:
```bash
pip install opencv-python numpy flask
```

## 🎯 Common Use Cases

### 1. Verify Camera is Working
```bash
cd camera_tools/tests
python quick_camera_test.py
```

### 2. Troubleshoot Camera Issues
```bash
cd camera_tools/diagnostics
python camera_diagnostics.py
python check_camera_permissions.py
```

### 3. Monitor Camera Health
```bash
cd camera_tools/health_monitoring
python webcam_health_monitor.py
```

### 4. Assess Camera Quality
```bash
cd camera_tools/tests
python camera_quality_test.py
```

## 📈 Camera Status Indicators

- ✅ **Healthy**: Camera working normally
- ⚠️ **Warning**: Minor issues detected
- ❌ **Error**: Camera not accessible or major issues
- 🔍 **Unknown**: Status not determined

## 🐛 Troubleshooting

### Camera Not Detected
1. Check USB connection (for external cameras)
2. Verify camera permissions
3. Close other applications using the camera
4. Restart your computer

### Low Quality or Dark Frames
1. Check lighting conditions
2. Remove lens cover
3. Adjust camera settings
4. Try different resolutions

### Permission Denied
1. macOS: System Preferences → Security & Privacy → Privacy → Camera
2. Windows: Settings → Privacy → Camera
3. Linux: Add user to 'video' group

## 📝 Notes

- Camera index 0 is typically the default/built-in camera
- Some features may vary depending on camera hardware
- Web dashboards require Flask to be installed
- Test results are automatically saved to the output directory

## 🤝 Contributing

To add new camera tools:
1. Create appropriate script in relevant subdirectory
2. Follow existing naming conventions
3. Update this README with tool documentation
4. Test on multiple camera configurations

---

**Last Updated**: June 2024
**Version**: 1.0.0