# Advanced Personality Assessment UI Implementation Plan

## Overview: 6-Minute Assessment with 7 Sections

### Section Flow
1. Emotion Regulation - 3 scenarios
2. Relationship Style - 4 questions
3. Listening Preferences - 2 scenarios + 2 questions
4. Loss Aversion - 3 choices (TO BUILD)
5. Perspective Taking - 2 scenarios (TO BUILD)
6. Sunk Cost Fallacy - 2 scenarios (TO BUILD)
7. Temporal Discounting - 4 choices (TO BUILD)

## Detailed Implementation Steps

### Step 1: Create Advanced Assessment Container (30 mins)

```html
<!-- assessments/templates/advanced_assessment.html -->
<div id="advanced-assessment">
    <header>
        <h1>Personality & Behavioral Assessment</h1>
        <div class="timer">Time remaining: <span id="timer">6:00</span></div>
        <div class="progress">Part <span id="current">1</span> of 7</div>
    </header>
    <main id="assessment-content">
        <!-- Dynamic content -->
    </main>
    <footer>
        <button id="back-btn" style="display:none">Back</button>
        <button id="next-btn" disabled>Next</button>
    </footer>
</div>
```

**Actions:**
1. Create HTML structure
2. Add simple timer (countdown only)
3. Style for readability
4. Test responsive design

### Step 2: Build Emotion Regulation Section (2 hours)

**2.1 Scenario Structure**
```javascript
const emotionScenarios = [
    {
        id: 'work_criticism',
        scenario: 'Your manager publicly criticizes your work in a team meeting.',
        emotions: ['angry', 'embarrassed', 'anxious', 'sad'],
        strategies: [
            {id: 'reframe', text: 'Think about it as constructive feedback', type: 'adaptive'},
            {id: 'suppress', text: 'Hide your emotions and act normal', type: 'maladaptive'},
            {id: 'express', text: 'Talk to manager privately later', type: 'adaptive'},
            {id: 'ruminate', text: 'Keep thinking about how unfair it was', type: 'maladaptive'}
        ]
    }
];
```

**2.2 Emotion Rating Interface**
```html
<div class="emotion-rating">
    <h3>How would you feel?</h3>
    <div class="emotion-scale">
        <label>Angry</label>
        <input type="range" name="angry" min="0" max="10" value="5">
        <span class="value">5</span>
    </div>
    <!-- Repeat for other emotions -->
</div>
```

**2.3 Strategy Selection**
```html
<div class="strategy-selection">
    <h3>What would you do?</h3>
    <label>
        <input type="checkbox" name="strategies" value="reframe">
        Think about it as constructive feedback
    </label>
    <!-- More strategies -->
</div>
```

**2.4 Scoring Logic**
```javascript
function scoreEmotionRegulation(responses) {
    const adaptiveCount = responses.strategies
        .filter(s => strategies[s].type === 'adaptive').length;
    const maladaptiveCount = responses.strategies
        .filter(s => strategies[s].type === 'maladaptive').length;
    
    return {
        adaptiveRatio: adaptiveCount / (adaptiveCount + maladaptiveCount),
        emotionalReactivity: calculateReactivity(responses.emotions)
    };
}
```

### Step 3: Build Relationship Style Section (1.5 hours)

**3.1 Attachment Questions**
```javascript
const attachmentQuestions = {
    anxiety: [
        'I often worry that people close to me don\'t really care about me',
        'I need a lot of reassurance that I am valued'
    ],
    avoidance: [
        'I prefer not to show others how I feel deep down',
        'I find it difficult to depend on others'
    ]
};
```

**3.2 Simple Grid Interface**
```html
<div class="attachment-grid">
    <h3>How much do you agree?</h3>
    <div class="statement">
        <p>I often worry that people close to me don't really care about me</p>
        <div class="scale-options">
            <label><input type="radio" name="q1" value="1"> Strongly Disagree</label>
            <label><input type="radio" name="q1" value="2"> Disagree</label>
            <label><input type="radio" name="q1" value="3"> Neutral</label>
            <label><input type="radio" name="q1" value="4"> Agree</label>
            <label><input type="radio" name="q1" value="5"> Strongly Agree</label>
        </div>
    </div>
</div>
```

**3.3 Style Classification**
```javascript
function classifyAttachment(anxietyScore, avoidanceScore) {
    if (anxietyScore < 3 && avoidanceScore < 3) return 'secure';
    if (anxietyScore >= 3 && avoidanceScore < 3) return 'anxious';
    if (anxietyScore < 3 && avoidanceScore >= 3) return 'avoidant';
    return 'fearful-avoidant';
}
```

### Step 4: Build Listening Preferences Section (1.5 hours)

**4.1 Scenario Presentation**
```javascript
const listeningScenarios = [
    {
        id: 'colleague_problem',
        context: 'A colleague comes to you frustrated about project challenges.',
        responses: {
            action: 'Let\'s break this down and create an action plan',
            time: 'I have 10 minutes - give me the key points',
            people: 'That sounds frustrating. How are you feeling?',
            content: 'Tell me all the details so I understand fully'
        }
    }
];
```

**4.2 Response Selection**
```html
<div class="listening-scenario">
    <p class="context">A colleague comes to you frustrated...</p>
    <h4>How would you respond?</h4>
    <div class="response-options">
        <label>
            <input type="radio" name="response" value="action">
            "Let's break this down and create an action plan"
        </label>
        <!-- Other options -->
    </div>
</div>
```

**4.3 Style Scoring**
```javascript
function scoreListeningStyle(responses) {
    const styleCounts = {action: 0, time: 0, people: 0, content: 0};
    responses.forEach(r => styleCounts[r]++);
    return {
        primaryStyle: getMaxStyle(styleCounts),
        flexibility: calculateFlexibility(styleCounts)
    };
}
```

### Step 5: Create Missing Components - Loss Aversion (1 hour)

**5.1 Simple Choice Scenarios**
```javascript
const lossAversionChoices = [
    {
        id: 'coin_flip',
        question: 'Would you accept a coin flip where:',
        win: 'Heads: You win $150',
        lose: 'Tails: You lose $100',
        options: ['Yes, I\'ll play', 'No, I\'ll pass']
    },
    {
        id: 'guaranteed',
        question: 'Which would you prefer?',
        optionA: 'Guaranteed $40',
        optionB: '50% chance of $100, 50% chance of nothing',
        options: ['Guaranteed $40', 'Take the 50/50 chance']
    }
];
```

**5.2 Choice Interface**
```html
<div class="loss-aversion">
    <h3>Decision Making</h3>
    <div class="choice-scenario">
        <p>Would you accept a coin flip where:</p>
        <p class="outcome win">Heads: You win $150</p>
        <p class="outcome lose">Tails: You lose $100</p>
        <div class="choice-buttons">
            <button onclick="selectChoice('yes')">Yes, I'll play</button>
            <button onclick="selectChoice('no')">No, I'll pass</button>
        </div>
    </div>
</div>
```

### Step 6: Create Perspective Taking Section (1 hour)

**6.1 Multi-Perspective Scenarios**
```javascript
const perspectiveScenarios = [
    {
        id: 'meeting_late',
        setup: 'Sarah arrives 20 minutes late to an important meeting.',
        perspectives: {
            sarah: 'Traffic was terrible and my child was sick this morning',
            boss: 'This is the third time this month she\'s been late',
            colleague: 'We had to start without her and repeat everything'
        },
        question: 'Rate how each person likely feels (1-5 scale)'
    }
];
```

**6.2 Perspective Rating**
```html
<div class="perspective-scenario">
    <p class="setup">Sarah arrives 20 minutes late...</p>
    <div class="perspective-ratings">
        <h4>How frustrated is each person?</h4>
        <div class="rating-row">
            <span>Sarah:</span>
            <input type="range" name="sarah_frustrated" min="1" max="5">
        </div>
        <div class="rating-row">
            <span>Boss:</span>
            <input type="range" name="boss_frustrated" min="1" max="5">
        </div>
    </div>
</div>
```

### Step 7: Create Temporal Discounting Section (1 hour)

**7.1 Time/Value Tradeoffs**
```javascript
const temporalChoices = [
    {
        id: 'week_month',
        immediate: '$50 today',
        delayed: '$60 in one month',
        delay: 30
    },
    {
        id: 'month_year',
        immediate: '$100 in one month',
        delayed: '$150 in one year',
        delay: 365
    }
];
```

**7.2 Simple Choice Interface**
```html
<div class="temporal-choice">
    <h3>Which would you prefer?</h3>
    <div class="options">
        <button class="choice-btn" onclick="choose('immediate')">
            $50 today
        </button>
        <span>OR</span>
        <button class="choice-btn" onclick="choose('delayed')">
            $60 in one month
        </button>
    </div>
</div>
```

### Step 8: Create Sunk Cost Section (45 mins)

**8.1 Sunk Cost Scenarios**
```javascript
const sunkCostScenarios = [
    {
        id: 'movie_ticket',
        setup: 'You bought a $15 movie ticket. 30 minutes in, you\'re bored.',
        options: [
            'Stay and watch the rest (you paid for it)',
            'Leave and do something else'
        ]
    }
];
```

### Step 9: Integrate All Sections (1.5 hours)

**9.1 Section Navigation**
```javascript
const advancedSections = [
    {id: 'emotion', title: 'Emotion Regulation', render: renderEmotion},
    {id: 'attachment', title: 'Relationship Style', render: renderAttachment},
    {id: 'listening', title: 'Listening Preferences', render: renderListening},
    {id: 'loss', title: 'Decision Making', render: renderLossAversion},
    {id: 'perspective', title: 'Perspective Taking', render: renderPerspective},
    {id: 'sunk', title: 'Sunk Cost', render: renderSunkCost},
    {id: 'temporal', title: 'Time Preferences', render: renderTemporal}
];
```

**9.2 Timer Management**
```javascript
let timeRemaining = 360; // 6 minutes in seconds
const timer = setInterval(() => {
    timeRemaining--;
    updateTimerDisplay(timeRemaining);
    if (timeRemaining <= 0) {
        clearInterval(timer);
        autoSubmit();
    }
}, 1000);
```

### Step 10: Results and Scoring (1 hour)

**10.1 Comprehensive Scoring**
```javascript
function calculatePersonalityProfile(responses) {
    return {
        emotionRegulation: scoreEmotionRegulation(responses.emotion),
        attachmentStyle: classifyAttachment(responses.attachment),
        listeningStyle: scoreListeningStyle(responses.listening),
        lossAversion: calculateLossAversion(responses.loss),
        perspectiveTaking: scorePerspective(responses.perspective),
        sunkCostBias: scoreSunkCost(responses.sunk),
        temporalDiscounting: scoreTemporalDiscounting(responses.temporal)
    };
}
```

## File Structure

```
assessments/
├── templates/
│   └── advanced_assessment.html
├── static/
│   ├── advanced_quiz.js
│   └── advanced_quiz.css
├── data/
│   ├── emotion_scenarios.json
│   ├── attachment_questions.json
│   ├── listening_scenarios.json
│   ├── loss_aversion_choices.json
│   ├── perspective_scenarios.json
│   ├── sunk_cost_scenarios.json
│   └── temporal_choices.json
└── api/
    └── advanced_assessment_api.py
```

## Time Estimates

- **Day 1**: Steps 1-3 (Container, Emotion, Attachment)
- **Day 2**: Steps 4-7 (Listening, Loss, Perspective, Temporal)
- **Day 3**: Steps 8-10 (Sunk Cost, Integration, Results)

Total: 3 days for complete Advanced assessment

## Simplification Strategies

1. **Use basic HTML inputs** instead of custom components
2. **Simple timer countdown** instead of complex time tracking
3. **Radio/checkbox only** instead of drag-drop or complex interactions
4. **Static scenarios** instead of dynamic generation
5. **Client-side scoring** to reduce server calls

## Testing Priorities

1. Timer works correctly and auto-submits
2. All sections save data before navigation
3. Scoring algorithms are accurate
4. Mobile layout is usable
5. Back button works properly

## MVP Features Only

- ✓ Basic form inputs
- ✓ Simple timer
- ✓ Linear navigation
- ✓ Text-based scenarios
- ✓ Basic scoring
- ✗ NO animations
- ✗ NO complex visualizations
- ✗ NO real-time sync
- ✗ NO advanced interactions