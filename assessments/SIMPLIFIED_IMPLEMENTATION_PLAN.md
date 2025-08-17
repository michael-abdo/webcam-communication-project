# Simplified Interactive Quiz Implementation Plan

## Principle: Start Simple, Iterate Later

### Phase 1: MVP (Week 1-2)
**Goal**: Basic working quizzes with data collection

#### Technology Stack
- **Frontend**: Plain HTML + CSS + Vanilla JavaScript
- **Backend**: Existing FastAPI endpoints
- **Data Storage**: JSON files initially
- **No Complex Frameworks**: No React/Vue/Angular yet

#### Core Components Only
1. **Cognitive Reflection Test (3 questions)**
   - Simple text inputs
   - Basic validation
   - Submit button

2. **Numeracy Test (2 questions)**
   - Number inputs
   - Simple confidence radio buttons (Low/Medium/High)

3. **Open-Minded Thinking (5 questions)**
   - Radio button Likert scales (1-5)
   - No fancy sliders

4. **Intent Attribution (2 scenarios)**
   - Multiple choice radio buttons
   - Simple text display

#### Simplifications
- No real-time behavioral tracking
- No fancy animations
- No progress bars
- No timers (track server-side)
- No adaptive features
- Single page per section

### Phase 2: Enhanced (Week 3-4)
**Goal**: Better UX and basic monitoring

#### Add Features
- Progress indicator (simple percentage)
- Basic timer display
- Session persistence
- Simple results page
- Basic styling improvements

#### Add Missing Core Components
- Need for Closure Scale
- Anchoring Bias Test

### Phase 3: Advanced (Week 5-6)
**Goal**: Full assessment suite

#### Add Advanced Assessments
- Emotion Regulation
- Relationship Style
- Listening Preferences
- Basic performance monitoring

#### Add Polish
- Transitions between sections
- Better error handling
- Mobile responsive design
- Basic accessibility

## File Structure (Simplified)

```
/assessments/
  /static/
    quiz.js          # All quiz logic in one file initially
    quiz.css         # All styles in one file
  /templates/
    quiz_base.html   # Single template for all quizzes
  /api/
    quiz_api.py      # Single API file for all endpoints
```

## Sample Implementation

### HTML (quiz_base.html)
```html
<!DOCTYPE html>
<html>
<head>
    <title>Bias Assessment</title>
    <link rel="stylesheet" href="/static/quiz.css">
</head>
<body>
    <div id="quiz-container">
        <h2 id="section-title"></h2>
        <form id="quiz-form">
            <div id="questions"></div>
            <button type="submit">Next</button>
        </form>
    </div>
    <script src="/static/quiz.js"></script>
</body>
</html>
```

### JavaScript (quiz.js)
```javascript
// Simple quiz engine
const Quiz = {
    currentSection: 0,
    sections: ['crt', 'numeracy', 'aot', 'intent'],
    responses: {},
    
    init() {
        this.loadSection(this.currentSection);
        document.getElementById('quiz-form').onsubmit = (e) => {
            e.preventDefault();
            this.saveResponses();
            this.nextSection();
        };
    },
    
    loadSection(index) {
        // Load questions from API
        fetch(`/api/quiz/section/${this.sections[index]}`)
            .then(r => r.json())
            .then(data => this.renderQuestions(data));
    },
    
    renderQuestions(data) {
        const container = document.getElementById('questions');
        container.innerHTML = data.questions.map(q => 
            this.renderQuestion(q)
        ).join('');
    },
    
    renderQuestion(question) {
        // Simple rendering based on type
        if (question.type === 'text') {
            return `
                <div class="question">
                    <label>${question.text}</label>
                    <input type="text" name="${question.id}" required>
                </div>
            `;
        }
        // Add other types...
    },
    
    saveResponses() {
        const formData = new FormData(document.getElementById('quiz-form'));
        this.responses[this.sections[this.currentSection]] = 
            Object.fromEntries(formData);
    },
    
    nextSection() {
        this.currentSection++;
        if (this.currentSection < this.sections.length) {
            this.loadSection(this.currentSection);
        } else {
            this.submitAll();
        }
    },
    
    submitAll() {
        fetch('/api/quiz/submit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(this.responses)
        }).then(() => {
            window.location.href = '/results';
        });
    }
};

Quiz.init();
```

### API (quiz_api.py)
```python
from fastapi import APIRouter
import json

router = APIRouter()

@router.get("/quiz/section/{section_name}")
async def get_section(section_name: str):
    # Load questions from JSON files
    with open(f"assessments/{section_name}/questions.json") as f:
        return json.load(f)

@router.post("/quiz/submit")
async def submit_quiz(responses: dict):
    # Simple scoring logic
    scores = calculate_scores(responses)
    # Save to file for now
    with open(f"results/{datetime.now().isoformat()}.json", "w") as f:
        json.dump({"responses": responses, "scores": scores}, f)
    return {"status": "success"}
```

## Benefits of Simple Approach

1. **Fast Development**: Can have working MVP in days
2. **Easy Testing**: Simple to debug and test
3. **Low Complexity**: Anyone can understand and modify
4. **Progressive Enhancement**: Easy to add features later
5. **Fail-Safe**: If JS fails, forms still work

## What We're NOT Doing (Yet)

- Complex state management
- Real-time behavioral tracking
- WebSocket connections
- Advanced animations
- Machine learning integration
- Video/audio processing
- Complex routing
- Component frameworks

## Success Metrics

- Users can complete all assessments
- Data is collected accurately
- Results are calculated correctly
- System is stable and fast
- Code is maintainable

## Next Steps

1. Create basic HTML template
2. Write simple quiz.js engine
3. Set up API endpoints
4. Test with real users
5. Iterate based on feedback