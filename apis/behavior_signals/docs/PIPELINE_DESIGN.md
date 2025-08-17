# Behavioral Signals Pipeline Design

## Overview
A streamlined pipeline for analyzing YouTube videos using the Behavioral Signals API, designed to work within API constraints and provide automated behavioral analysis reports.

## Pipeline Architecture

### Workflow
```
YouTube URL → Download → Trim (2-3 min) → Submit to API → Generate Report
```

### Core Components

#### 1. **YouTube Downloader Module** (`src/pipeline/downloader.py`)
- Uses yt-dlp to download videos
- Saves to `data/downloads/`
- Returns path to downloaded MP4 file

#### 2. **Audio Processor Module** (`src/pipeline/processor.py`)
- Converts MP4 to MP3 using ffmpeg
- Trims audio to specified duration (default: 2 minutes)
- Handles the API's message size limitations
- Saves processed files to `data/samples/`

#### 3. **API Client** (`src/api/client.py`)
- Refactored from existing scripts
- Handles authentication and requests
- Monitors processing status
- Retrieves results when complete

#### 4. **Pipeline Orchestrator** (`src/pipeline/pipeline.py`)
- Coordinates all steps
- Tracks job progress
- Handles errors gracefully
- Saves state for recovery

#### 5. **Report Generator** (existing `src/analysis/create_report.py`)
- Analyzes JSON results
- Creates human-readable reports
- Saves to `data/reports/`

### Project Structure
```
behavior_signals/
├── src/
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── pipeline.py      # Main orchestrator
│   │   ├── downloader.py    # YouTube download
│   │   ├── processor.py     # Audio processing
│   │   └── config.py        # Configuration
│   ├── api/
│   │   ├── client.py        # API client class
│   │   └── (existing scripts)
│   └── analysis/
│       └── (existing analysis scripts)
├── config/
│   └── config.yaml          # Central configuration
├── data/
│   ├── downloads/           # Raw YouTube videos
│   ├── samples/            # Processed audio
│   ├── results/            # API JSON responses
│   ├── reports/            # Analysis reports
│   └── jobs/               # Pipeline job tracking
├── scripts/
│   └── run_pipeline.py     # CLI entry point
└── logs/                   # Application logs
```

### Configuration Schema
```yaml
api:
  key: "f38d44bfe4ae7c915e2be3ec32c2101f"
  client_id: "10000127"
  base_url: "https://api.behavioralsignals.com"
  
processing:
  default_duration: 120      # 2 minutes (avoids Kafka errors)
  max_duration: 180         # 3 minutes maximum
  audio_format: "mp3"
  sample_rate: 44100
  
timeouts:
  download: 300             # 5 minutes
  api_submission: 120       # 2 minutes
  api_check_interval: 5     # 5 seconds
  max_wait: 600            # 10 minutes
  
paths:
  downloads: "data/downloads"
  samples: "data/samples"
  results: "data/results"
  reports: "data/reports"
  jobs: "data/jobs"
```

### Usage Examples

#### Basic Usage
```bash
# Process single video (2-minute sample)
python scripts/run_pipeline.py "https://youtube.com/watch?v=VIDEO_ID"

# Custom duration (max 3 minutes)
python scripts/run_pipeline.py "https://youtube.com/watch?v=VIDEO_ID" --duration 180

# Check job status
python scripts/run_pipeline.py --status job_12345

# Process batch of URLs
python scripts/run_pipeline.py --batch urls.txt

# Generate report from existing results
python scripts/run_pipeline.py --report process_12345_results.json
```

#### Pipeline Job Tracking
Each pipeline run creates a job file in `data/jobs/` with:
- Job ID (timestamp-based)
- YouTube URL
- Current status
- Process IDs
- File paths
- Error messages (if any)

### Error Handling

1. **Download Failures**: Retry with exponential backoff
2. **API Errors**: 
   - Insufficient credits → Clear error message
   - Kafka size error → Automatically reduce duration
   - Network issues → Retry logic
3. **Processing Failures**: Save state for manual recovery

### Implementation Phases

**Phase 1: Foundation**
- Configuration management
- API client refactoring
- Basic logging setup

**Phase 2: Core Modules**
- YouTube downloader
- Audio processor
- Pipeline orchestrator

**Phase 3: Integration**
- CLI interface
- Job tracking
- Error recovery

**Phase 4: Enhancement**
- Batch processing
- Progress visualization
- Extended reporting

### Technical Constraints

1. **API Limitations**:
   - Maximum ~2-3 minutes of audio (Kafka message size)
   - Requires MP3 format
   - Processing credits required

2. **Dependencies**:
   - Python 3.x
   - yt-dlp (YouTube downloading)
   - ffmpeg (audio processing)
   - requests (API calls)

### Benefits

- **Automated**: One command from URL to report
- **Reliable**: Works within API constraints
- **Trackable**: Monitor progress and recover from failures
- **Extensible**: Easy to add new features
- **Reusable**: Leverages existing analysis code

### Future Enhancements

1. **Web Interface**: Simple UI for non-technical users
2. **Scheduling**: Process videos on a schedule
3. **Notifications**: Email/webhook when complete
4. **Advanced Sampling**: Intelligent segment selection
5. **Cost Estimation**: Predict API credit usage