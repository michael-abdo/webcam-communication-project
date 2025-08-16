# Interactive Quiz Design Document

## Core Assessment Components (4-minute)

### 1. Cognitive Reflection Test (CRT)
**Purpose**: Measure intuitive vs deliberative thinking

**UI Components**:
- Text input fields for numerical answers
- Confidence slider (0-100%)
- Timer display showing remaining time
- Submit button with validation

**Tracking Metrics**:
- Response time per question
- Keystroke patterns and hesitations
- Answer revisions
- Confidence calibration

**Scoring**:
- Correct vs intuitive responses
- Cognitive style classification (deliberative/intuitive/mixed)
- Response time analysis

### 2. Numeracy and Calibration
**Purpose**: Assess mathematical reasoning and metacognitive accuracy

**UI Components**:
- Number input fields with unit labels
- Optional calculator widget
- Dual sliders for confidence and population estimates
- Visual progress indicators

**Tracking Metrics**:
- Calculator usage patterns
- Answer revision count
- Confidence vs accuracy correlation
- Population estimate accuracy

**Scoring**:
- Numerical accuracy within tolerance
- Calibration score (confidence vs performance)
- Overconfidence bias detection

### 3. Actively Open-Minded Thinking (AOT)
**Purpose**: Measure intellectual humility and bias resistance

**UI Components**:
- 5-point Likert scales with hover effects
- Optional reflection text area
- Certainty slider for each response
- Visual feedback for selections

**Tracking Metrics**:
- Response change patterns
- Deliberation time
- Reflection usage
- Certainty levels

**Scoring**:
- AOT average score
- Bias resistance profile
- Response stability metrics

### 4. Intent Attribution
**Purpose**: Detect hostile attribution bias and social reasoning

**UI Components**:
- Scenario cards with context
- Three attribution options (hostile/neutral/benign)
- Confidence scale
- Optional perspective-taking prompt

**Tracking Metrics**:
- Initial vs final choices
- Choice revision patterns
- Perspective-taking engagement
- Confidence levels

**Scoring**:
- Hostility bias score
- Attribution accuracy
- Perspective-taking usage

## Advanced Assessment Components (6-minute)

### 5. Emotion Regulation
**Purpose**: Assess emotional management strategies

**UI Components**:
- Multi-emotion intensity sliders (0-10)
- Strategy checkboxes (adaptive/maladaptive)
- Outcome effectiveness rating
- Color-coded emotion visualization

**Tracking Metrics**:
- Emotional reactivity levels
- Strategy selection patterns
- Time to strategy selection
- Effectiveness predictions

**Scoring**:
- Adaptive strategy ratio
- Emotional awareness
- Regulation effectiveness
- Specific bias indicators (suppression, rumination)

### 6. Relationship Style
**Purpose**: Measure attachment patterns and interpersonal preferences

**UI Components**:
- 2x2 attachment style matrix
- Scenario-based questions
- Relationship preference scales
- Visual attachment grid

### 7. Listening Preferences
**Purpose**: Assess active vs passive communication styles

**UI Components**:
- Communication scenario cards
- Multiple choice with reasoning
- Listening style indicators
- Preference selectors

### 8. Loss Aversion
**Purpose**: Measure sensitivity to losses vs gains

**UI Components**:
- Risk scenario presentations
- Interactive probability displays
- Gain/loss comparison sliders
- Visual risk calculator

### 9. Perspective Taking
**Purpose**: Evaluate theory of mind and empathy

**UI Components**:
- Multi-character scenarios
- Viewpoint switcher interface
- Perspective rating scales
- Character thought bubbles

### 10. Temporal Discounting
**Purpose**: Assess present vs future reward preferences

**UI Components**:
- Timeline slider interface
- Value comparison displays
- Delay period selectors
- Interactive time/value trade-offs

## Performance Monitoring Features

### Real-time Tracking
- Attention lapses detection
- Response time degradation
- Fatigue indicators
- Cognitive load visualization

### Adaptive Features
- Dynamic timing adjustments
- Difficulty modification
- Break recommendations
- Performance-based pacing

### Quality Assurance
- Signal validation
- Data completeness checks
- Response validity indicators
- Technical issue detection

## Technical Implementation

### Frontend Architecture
```
/static/
  /js/
    quiz-engine.js         # Core quiz functionality
    timer-components.js    # Countdown and progress
    response-capture.js    # User interaction tracking
    behavioral-integration.js  # API connections
  /css/
    quiz-base.css         # Common styling
    cognitive-reflection.css  # CRT-specific
    personality-scales.css    # Likert and sliders
```

### Backend Integration
```
/assessments/
  /api/
    core_assessment.py     # Core endpoints
    advanced_assessment.py # Advanced endpoints
    session_management.py  # State handling
    results_processing.py  # Scoring logic
```

### Data Models
```python
# Response tracking
ResponseData = {
    "question_id": str,
    "response_value": Any,
    "response_time": float,
    "confidence": float,
    "revisions": List[Revision],
    "metadata": Dict
}

# Session management
AssessmentSession = {
    "session_id": str,
    "user_id": str,
    "start_time": datetime,
    "sections_completed": List[str],
    "current_section": str,
    "behavioral_data": Dict
}
```

## Scoring Algorithms

### Bias Detection
- Pattern recognition across responses
- Cross-section correlation analysis
- Behavioral consistency checks
- Cognitive style profiling

### Calibration Metrics
- Brier score for confidence accuracy
- Resolution (discrimination ability)
- Reliability (consistency)
- Sharpness (confidence variation)

### Personality Profiling
- Trait aggregation
- Bias interaction mapping
- Coaching recommendation engine
- Risk factor identification

## User Experience Flow

1. **Onboarding**
   - Consent and instructions
   - Device capability check
   - Baseline establishment

2. **Assessment Progression**
   - Section transitions
   - Progress visualization
   - Adaptive pacing
   - Break opportunities

3. **Results Presentation**
   - Real-time scoring
   - Visual feedback
   - Comprehensive report
   - Coaching recommendations

## Accessibility Requirements
- Keyboard navigation
- Screen reader compatibility
- High contrast mode
- Adjustable timing
- Alternative input methods

## Privacy and Security
- End-to-end encryption
- Session isolation
- Data minimization
- Consent management
- Right to deletion