# NLP Text Analysis Integration

## Overview

The NLP text analysis feature adds cognitive load detection through text analysis as a complementary data stream to the existing video/webcam fatigue detection.

## Architecture

### Client-Side Processing
- All NLP processing happens in the browser using **compromise.js** (lightweight NLP library)
- No server-side text processing - maintains privacy and lightweight backend
- Real-time analysis with 500ms debouncing to prevent overload

### Metrics Calculated

1. **Basic Metrics**
   - Word count
   - Sentence count
   - Average word length
   - Reading Ease (Flesch score: 0-100)

2. **Advanced Metrics**
   - Sentiment analysis (Positive/Negative/Neutral)
   - Typing speed (Words per Minute)
   - Pause detection (breaks > 2 seconds)
   - Text complexity classification

3. **Cognitive Load Score (0-1)**
   - Formula: `0.3*complexity + 0.3*speed + 0.2*sentiment + 0.2*length`
   - Higher scores indicate higher cognitive load

## API Endpoints

### GET /text-analysis
- Text analysis interface page
- Rate limited: 10 requests/minute per IP

### POST /api/text-analysis-result
- Receives text analysis results from client
- Required fields: `word_count`, `sentence_count`, `cognitive_load`, `timestamp`
- Optional fields: `sentiment`, `typing_speed`, `complexity`, `text_snippet`

## Data Flow

```
User Types → Client NLP Processing → Metrics Extraction → Backend Storage → Dashboard Display
```

## Privacy

- Text content is **never sent to the server**
- Only metrics and optional 100-char snippet are transmitted
- All processing happens locally in the browser

## Integration with Existing System

### Source Detection
- `text` - Only text analysis active
- `video` - Only video analysis active  
- `camera` - Only webcam analysis active
- `combined` - Multiple sources active

### Combined Fatigue Score
When both video/webcam and text are active:
- Combined score = `0.6 * video_fatigue + 0.4 * text_fatigue`

## Usage

1. Navigate to `/text-analysis`
2. Start typing or paste text
3. Analysis runs automatically after 500ms pause
4. Metrics update in real-time
5. Results sync with main dashboard

## Technical Details

### Character Limit
- Maximum 10,000 characters
- Visual indicator shows usage

### XSS Prevention
- All input sanitized before processing
- Paste events filtered for safety

### Performance
- Processing time tracked and displayed
- Typical analysis: 10-50ms for 1000 words

## Future Enhancements

- Speech-to-text integration
- Multi-language support
- Advanced sentiment models
- Keystroke dynamics analysis