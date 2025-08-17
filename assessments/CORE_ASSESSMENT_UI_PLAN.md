# Core Cognitive Assessment UI Implementation Plan

## Overview: 4-Minute Assessment with 7 Sections

### Section Flow
1. Cognitive Reflection Test (CRT) - 3 questions
2. Numeracy & Calibration - 2 questions  
3. Actively Open-Minded Thinking (AOT) - 5 questions
4. Intent Attribution - 2 scenarios
5. Need for Closure - 3 questions (TO BUILD)
6. Anchoring Test - 2 questions (TO BUILD)
7. Confidence Calibration - Summary

## Detailed Implementation Steps

### Step 1: Create Unified Quiz Container (30 mins)

```html
<!-- assessments/templates/core_assessment.html -->
<div id="core-assessment">
    <header>
        <h1>Cognitive Assessment</h1>
        <div class="progress-text">Section <span id="current">1</span> of 7</div>
    </header>
    <main id="quiz-content">
        <!-- Dynamic content loads here -->
    </main>
    <footer>
        <button id="next-btn" disabled>Next</button>
    </footer>
</div>
```

**Actions:**
1. Create HTML template
2. Add basic CSS styling
3. Test container rendering
4. Verify mobile layout

### Step 2: Build CRT Section (2 hours)

**2.1 Create Question Renderer**
```javascript
function renderCRT() {
    const questions = [
        {id: 'bat_ball', text: 'A bat and a ball...', type: 'number'},
        {id: 'widget', text: 'If it takes 5 machines...', type: 'number'},
        {id: 'lily_pad', text: 'In a lake...', type: 'number'}
    ];
    
    return questions.map(q => `
        <div class="crt-question">
            <p>${q.text}</p>
            <input type="number" name="${q.id}" required>
            <div class="confidence">
                <label>Confidence:</label>
                <input type="radio" name="${q.id}_conf" value="low"> Low
                <input type="radio" name="${q.id}_conf" value="med"> Medium
                <input type="radio" name="${q.id}_conf" value="high"> High
            </div>
        </div>
    `).join('');
}
```

**2.2 Add Validation**
- Check for numeric input
- Require confidence selection
- Enable Next button when complete

**2.3 Implement Scoring**
```javascript
function scoreCRT(responses) {
    const correct = {
        bat_ball: 0.05,
        widget: 5,
        lily_pad: 47
    };
    let score = 0;
    // Compare and score
    return {score, details};
}
```

### Step 3: Build Numeracy Section (1.5 hours)

**3.1 Create Questions**
```javascript
const numeracyQuestions = [
    {
        id: 'percentage',
        text: 'If a disease affects 1 in 1000 people...',
        type: 'number',
        unit: 'percent'
    },
    {
        id: 'probability',
        text: 'A fair coin is flipped 3 times...',
        type: 'fraction'
    }
];
```

**3.2 Add Calibration**
- Confidence slider (simplified to 3 options)
- Population estimate input
- Clear instructions

**3.3 Scoring Logic**
- Check numerical accuracy
- Calculate calibration score
- Track overconfidence

### Step 4: Build AOT Scale (1 hour)

**4.1 Render Likert Questions**
```javascript
function renderAOT() {
    const questions = getAOTQuestions();
    return `
        <div class="aot-section">
            <p class="instructions">Rate your agreement (1-5)</p>
            ${questions.map(q => renderLikertQuestion(q)).join('')}
        </div>
    `;
}
```

**4.2 Handle Reverse Scoring**
```javascript
const reverseScored = ['q2', 'q3', 'q5'];
function scoreAOT(responses) {
    // Apply reverse scoring where needed
}
```

### Step 5: Build Intent Attribution (1.5 hours)

**5.1 Scenario Display**
```javascript
const scenarios = [
    {
        id: 'email',
        context: 'Your colleague didn\'t respond to your email...',
        options: [
            {value: 'hostile', text: 'They\'re ignoring me on purpose'},
            {value: 'neutral', text: 'They might be busy'},
            {value: 'benign', text: 'They probably didn\'t see it'}
        ]
    }
];
```

**5.2 Choice Interface**
- Radio buttons for options
- Clear scenario presentation
- Optional explanation field

### Step 6: Create Missing Components (2 hours)

**6.1 Need for Closure Scale**
```javascript
// Simple 3-question version
const nfcQuestions = [
    'I prefer tasks with clear right/wrong answers',
    'I feel uncomfortable with ambiguous situations',
    'I like to have things settled and decided'
];
```

**6.2 Anchoring Test**
```javascript
// Two-part anchoring test
function renderAnchoring() {
    return `
        <div class="anchoring-test">
            <p>Step 1: Is the population of Morocco more or less than 20 million?</p>
            <input type="radio" name="anchor" value="more"> More
            <input type="radio" name="anchor" value="less"> Less
            
            <p>Step 2: What is your best guess for the population?</p>
            <input type="number" name="estimate" placeholder="Enter number">
        </div>
    `;
}
```

### Step 7: Build Navigation System (1 hour)

**7.1 Section Management**
```javascript
const sections = [
    {id: 'crt', render: renderCRT, score: scoreCRT},
    {id: 'numeracy', render: renderNumeracy, score: scoreNumeracy},
    {id: 'aot', render: renderAOT, score: scoreAOT},
    {id: 'intent', render: renderIntent, score: scoreIntent},
    {id: 'nfc', render: renderNFC, score: scoreNFC},
    {id: 'anchoring', render: renderAnchoring, score: scoreAnchoring}
];

let currentSection = 0;
```

**7.2 Progress Tracking**
- Update section counter
- Store responses locally
- Enable back navigation

### Step 8: Implement Data Collection (1 hour)

**8.1 Response Storage**
```javascript
const sessionData = {
    userId: generateId(),
    startTime: Date.now(),
    responses: {},
    scores: {},
    timings: {}
};
```

**8.2 Section Timing**
- Track time per section
- Record response changes
- Flag rushed responses

### Step 9: Create Results Summary (1 hour)

**9.1 Calculate Overall Scores**
```javascript
function calculateSummary(sessionData) {
    return {
        cognitiveStyle: determineCognitiveStyle(sessionData),
        biasResistance: calculateBiasResistance(sessionData),
        confidenceCalibration: calculateCalibration(sessionData),
        recommendations: generateRecommendations(sessionData)
    };
}
```

**9.2 Display Results**
- Simple text summary
- Key metrics highlighted
- Actionable feedback

### Step 10: Testing & Integration (2 hours)

**10.1 Component Testing**
- Test each section individually
- Verify scoring accuracy
- Check data persistence

**10.2 Full Flow Testing**
- Complete assessment end-to-end
- Test interruption recovery
- Verify all data captured

## File Structure

```
assessments/
├── templates/
│   └── core_assessment.html
├── static/
│   ├── core_quiz.js
│   └── core_quiz.css
├── data/
│   ├── crt_questions.json
│   ├── aot_questions.json
│   ├── numeracy_questions.json
│   ├── intent_scenarios.json
│   ├── nfc_questions.json
│   └── anchoring_questions.json
└── api/
    └── core_assessment_api.py
```

## Time Estimates

- **Day 1**: Steps 1-3 (Container, CRT, Numeracy)
- **Day 2**: Steps 4-6 (AOT, Intent, Missing components)
- **Day 3**: Steps 7-10 (Navigation, Data, Results, Testing)

Total: 3 days for complete Core assessment

## Critical Success Factors

1. **All sections must save data** even if user quits
2. **Scoring must be accurate** for research validity
3. **Mobile must work** for accessibility
4. **Load time < 3 seconds** for user retention
5. **Clear instructions** for each section

## Simplified Features

- No animations or transitions
- Basic HTML5 validation only
- Simple radio/number inputs
- Text-based progress indicator
- Single-page sections
- No real-time sync

## Testing Checklist

- [ ] Each section renders correctly
- [ ] All inputs validate properly
- [ ] Scores calculate accurately
- [ ] Data persists on refresh
- [ ] Mobile layout works
- [ ] Keyboard navigation works
- [ ] Error messages are clear
- [ ] Results display correctly