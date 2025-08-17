# Behavioral Signals Pipeline

An automated pipeline for analyzing YouTube videos using the Behavioral Signals API.

## Quick Start

```bash
# Process a YouTube video (automatically downloads, trims to 2 minutes, submits to API, generates report)
python scripts/run_pipeline.py "https://youtube.com/watch?v=VIDEO_ID"
```

## Features

- **Automated**: One command from YouTube URL to behavioral analysis report
- **Chunking Support**: Split long videos into multiple segments for complete analysis
- **Multiple Video Processing**: Process multiple URLs simultaneously
- **Configurable**: 2-minute default (avoids API size limits), customizable duration and minimum chunk size
- **Preview Mode**: See chunking breakdown and cost impact before processing
- **Trackable**: Job tracking with recovery from failures
- **Complete**: Downloads video → Extracts audio → Trims/Chunks → API submission → Generates report

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install ffmpeg (required for audio processing):
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg
```

## Usage Examples

### Basic Usage
```bash
# Process single video (2-minute sample)
python scripts/run_pipeline.py "https://youtube.com/watch?v=VIDEO_ID"

# Custom duration (max 3 minutes to avoid API limits)
python scripts/run_pipeline.py "https://youtube.com/watch?v=VIDEO_ID" --duration 180
```

### Chunking Mode (NEW!)
```bash
# Preview chunking breakdown (shows cost impact)
python scripts/run_pipeline.py "URL" --preview --duration 120 --min 30

# Enable chunking mode (splits video into multiple 2-minute segments)
python scripts/run_pipeline.py "URL" --chunk

# Custom chunking with 3-minute chunks and 45-second minimum
python scripts/run_pipeline.py "URL" --chunk --duration 180 --min 45
```

### Multiple Video Processing (NEW!)
```bash
# Process multiple videos directly
python scripts/run_pipeline.py "URL1" "URL2" "URL3"

# Multiple videos with chunking
python scripts/run_pipeline.py "URL1" "URL2" --chunk
```

### Job Management
```bash
# Check job status
python scripts/run_pipeline.py --status 20240808_143022

# View verbose output
python scripts/run_pipeline.py "URL" --verbose
```

### Batch Processing
```bash
# Create a file with URLs (one per line)
echo "https://youtube.com/watch?v=VIDEO_ID1" > urls.txt
echo "https://youtube.com/watch?v=VIDEO_ID2" >> urls.txt

# Process all URLs
python scripts/run_pipeline.py --batch urls.txt
```

### Generate Reports from Existing Results
```bash
python scripts/run_pipeline.py --report data/results/process_12345_results.json
```

## Pipeline Flow

### Standard Mode
1. **Download**: Uses yt-dlp to download YouTube video to `data/downloads/`
2. **Process**: Converts to MP3 and trims to specified duration (saves to `data/samples/`)
3. **Submit**: Uploads audio to Behavioral Signals API
4. **Monitor**: Tracks processing status
5. **Results**: Downloads JSON results to `data/results/`
6. **Report**: Generates human-readable analysis report in `data/reports/`

### Chunking Mode
1. **Download**: Uses yt-dlp to download YouTube video to `data/downloads/`
2. **Chunk**: Converts to MP3 and splits into multiple chunks (saves to `data/samples/`)
3. **Submit Each**: Uploads each chunk separately to Behavioral Signals API
4. **Monitor Each**: Tracks processing status for all chunks
5. **Results**: Downloads JSON results for each chunk to `data/results/`
6. **Report**: Generates analysis report (currently uses first chunk)

## Configuration

Edit `config/config.yaml` to customize:

```yaml
processing:
  default_duration: 120    # 2 minutes (recommended to avoid API limits)
  max_duration: 180       # 3 minutes maximum
  min_duration: 30        # Minimum chunk duration for chunking mode

timeouts:
  download: 300          # Video download timeout
  max_wait: 600         # Max time to wait for API processing
```

## Job Tracking

Each pipeline run creates a job file in `data/jobs/` with:
- Unique job ID (timestamp-based)
- Current status and progress
- File paths for all generated files
- Error messages (if any)

## Output Files

```
data/
├── downloads/           # Original YouTube videos (.mp4)
├── samples/            # Processed audio clips (.mp3)
├── results/            # API JSON responses
├── reports/            # Human-readable analysis reports
└── jobs/               # Job tracking files
```

## Error Handling

- **Download failures**: Retries with timeout
- **API errors**: Clear error messages with suggestions
- **Size errors**: Automatically reduces duration if file too large
- **Network issues**: Retry logic with exponential backoff

## Dependencies

- Python 3.7+
- yt-dlp (YouTube downloading)
- ffmpeg (audio processing)
- PyYAML (configuration)
- requests (API communication)

## API Limitations

- Maximum ~2-3 minutes of audio (due to Kafka message size limits)
- Requires MP3 format
- Processing credits required
- Best quality with clear speech audio