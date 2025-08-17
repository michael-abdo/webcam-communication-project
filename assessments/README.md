# Bias-Resilient Interactive Assessment System

## Overview
This assessment system provides interactive UI quizzes designed to measure cognitive performance, detect biases, and assess fatigue levels through comprehensive psychological assessments.

## Assessment Structure

### Core 4-Minute Cognitive Assessment
Located in `core_4min/`, this assessment includes:
- **Cognitive Reflection Test (CRT)**: Classic problems testing intuitive vs deliberative thinking
- **Numeracy & Calibration**: Mathematical reasoning with confidence calibration
- **Actively Open-Minded Thinking (AOT)**: Measures intellectual humility and bias resistance
- **Intent Attribution**: Social scenario judgments to detect hostile attribution bias
- **Need for Closure**: Preference for certainty and quick decision-making
- **Anchoring Test**: Susceptibility to numerical anchoring effects

### Advanced 6-Minute Personality Assessment
Located in `advanced_6min/`, this assessment includes:
- **Emotion Regulation**: Strategies for managing emotional responses
- **Relationship Style**: Attachment patterns and interpersonal preferences
- **Listening Preferences**: Active vs passive communication styles
- **Loss Aversion**: Risk tolerance and framing effects
- **Perspective Taking**: Theory of mind and empathy assessment
- **Sunk Cost**: Tendency to continue failed investments
- **Temporal Discounting**: Present vs future reward preferences

### Performance Monitoring
Located in `performance_monitoring/`, this system tracks:
- **Baseline Establishment**: Pre-assessment cognitive state
- **Real-time Monitoring**: Continuous performance tracking during assessments
- **Behavioral Integration**: Multi-modal data collection (video, audio, interactions)
- **Adaptive Assessment**: Dynamic difficulty and pacing adjustments
- **Fatigue Detection**: Cognitive load and attention degradation indicators

## Technical Architecture

### Frontend Components
- **HTML Templates**: Located in `/templates/assessments/`
- **JavaScript**: Interactive logic in `/static/js/`
- **CSS Styling**: Visual design in `/static/css/`

### Backend Integration
- **FastAPI Routes**: API endpoints in `/assessments/api/`
- **Data Models**: Pydantic schemas in `/assessments/models/`
- **Scoring Algorithms**: Python scoring logic in each section's `scoring.py`

### Data Flow
1. User initiates assessment session
2. Frontend presents interactive questions with real-time response tracking
3. Behavioral signals captured simultaneously (if enabled)
4. Responses validated and scored in real-time
5. Results aggregated for bias detection and personality profiling
6. Comprehensive report generated with coaching recommendations

## Key Features

### Interactive UI Elements
- **Likert Scales**: Smooth visual feedback for agreement ratings
- **Confidence Sliders**: Calibration between certainty and accuracy
- **Timer Components**: Visual countdown and progress tracking
- **Response Tracking**: Keystroke patterns, hesitation detection, revision monitoring

### Bias Detection Capabilities
- **Cognitive Biases**: Intuitive thinking, anchoring, confirmation bias
- **Social Biases**: Hostile attribution, fundamental attribution error
- **Decision Biases**: Loss aversion, sunk cost fallacy, temporal discounting
- **Emotional Biases**: Suppression, rumination, defensive reactivity

### Adaptive Features
- **Performance-based Pacing**: Adjust timing based on fatigue indicators
- **Dynamic Difficulty**: Modify question complexity based on performance
- **Break Recommendations**: Suggest pauses when cognitive overload detected
- **Personalized Feedback**: Tailored coaching based on individual bias profile

## Implementation Phases

### Phase 1: Foundation (Current)
- Basic quiz infrastructure
- Core cognitive reflection test
- Simple response tracking

### Phase 2: Core Assessment
- Complete 4-minute assessment suite
- Basic scoring algorithms
- Session management

### Phase 3: Behavioral Integration
- Real-time performance monitoring
- Multi-modal data collection
- Fatigue detection

### Phase 4: Advanced Features
- Full personality assessment
- Adaptive algorithms
- Comprehensive reporting

## Development Guidelines

### Code Organization
- Each assessment section is self-contained with its own components
- Shared UI elements in `/shared_components/`
- Consistent naming conventions across all sections
- Modular design for easy extension

### Testing Requirements
- Unit tests for scoring algorithms
- Integration tests for assessment flow
- Performance tests for real-time monitoring
- Accessibility compliance testing

### Security Considerations
- PII data encryption for assessment responses
- Secure session management
- GDPR/CCPA compliance for behavioral data
- Regular security audits for data handling

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Set up FastAPI routes in main application
3. Configure behavioral signals API credentials
4. Launch development server: `uvicorn main:app --reload`
5. Access assessments at `/assessments/core` or `/assessments/advanced`

## Future Enhancements
- Mobile-responsive design
- Offline assessment capability
- Multi-language support
- Integration with learning management systems
- Advanced analytics dashboard