# Performance and Fatigue Measurement UI Implementation Plan

## Overview: Continuous Monitoring During Assessments

### Monitoring Components
1. Pre-Assessment Baseline (1 minute)
2. Reaction Time Checkpoints (between sections)
3. Attention Monitoring (embedded in quizzes)
4. Fatigue Detection Alerts
5. Post-Assessment Summary

## Architecture: Lightweight Background Monitoring

### Key Principles
- Non-intrusive monitoring
- Minimal performance impact
- Clear user communication
- Automatic break recommendations

## Detailed Implementation Steps

### Step 1: Create Performance Monitor Module (1 hour)

**1.1 Basic Monitor Structure**
```javascript
// performance_monitor.js
const PerformanceMonitor = {
    baseline: null,
    checkpoints: [],
    fatigueScore: 0,
    attentionLapses: 0,
    
    init() {
        this.startTime = Date.now();
        this.lastActivityTime = Date.now();
        this.setupEventListeners();
    },
    
    setupEventListeners() {
        // Monitor user activity
        document.addEventListener('click', () => this.recordActivity());
        document.addEventListener('keypress', () => this.recordActivity());
    }
};
```

**1.2 Activity Tracking**
```javascript
recordActivity() {
    const now = Date.now();
    const timeSinceLastActivity = now - this.lastActivityTime;
    
    // Detect long pauses (potential attention lapses)
    if (timeSinceLastActivity > 30000) { // 30 seconds
        this.attentionLapses++;
    }
    
    this.lastActivityTime = now;
}
```

### Step 2: Implement Baseline Test (1.5 hours)

**2.1 Simple Baseline UI**
```html
<!-- baseline_test.html -->
<div id="baseline-test">
    <h2>Quick Readiness Check</h2>
    <p>Before we begin, let's make sure you're ready for the assessment.</p>
    
    <div class="baseline-tasks">
        <!-- Task 1: Simple Reaction -->
        <div class="task" id="reaction-baseline">
            <p>Click the button as soon as it appears</p>
            <div class="test-area"></div>
        </div>
        
        <!-- Task 2: Pattern Recognition -->
        <div class="task" id="pattern-baseline">
            <p>Click when you see the letter X</p>
            <div class="letter-display"></div>
        </div>
    </div>
    
    <button id="start-assessment" disabled>Start Assessment</button>
</div>
```

**2.2 Baseline Logic**
```javascript
function runBaselineTest() {
    const tests = [
        runReactionTest(3), // 3 trials
        runPatternTest(10)  // 10 letters
    ];
    
    Promise.all(tests).then(results => {
        PerformanceMonitor.baseline = {
            avgReaction: results[0].average,
            patternAccuracy: results[1].accuracy,
            timestamp: Date.now()
        };
        
        enableStartButton();
    });
}
```

### Step 3: Create Reaction Time Checkpoints (1.5 hours)

**3.1 Between-Section Checks**
```javascript
// Quick reaction test between quiz sections
function reactionCheckpoint() {
    return new Promise(resolve => {
        showCheckpointUI();
        
        setTimeout(() => {
            showReactionPrompt();
            const startTime = Date.now();
            
            document.onclick = () => {
                const reactionTime = Date.now() - startTime;
                PerformanceMonitor.checkpoints.push({
                    time: reactionTime,
                    section: currentSection,
                    timestamp: Date.now()
                });
                
                hideCheckpointUI();
                resolve(reactionTime);
            };
        }, random(1000, 3000));
    });
}
```

**3.2 Checkpoint UI**
```html
<div id="checkpoint-overlay" style="display:none">
    <div class="checkpoint-box">
        <p>Quick check - Click when ready!</p>
        <div id="reaction-prompt" style="display:none">
            CLICK NOW!
        </div>
    </div>
</div>
```

### Step 4: Embed Attention Monitoring (2 hours)

**4.1 Response Time Tracking**
```javascript
// Track response times for all quiz questions
function trackQuestionResponse(questionId, startTime) {
    const responseTime = Date.now() - startTime;
    
    // Detect unusually slow responses
    if (responseTime > 60000) { // 1 minute
        PerformanceMonitor.attentionLapses++;
    }
    
    // Detect rushed responses  
    if (responseTime < 1000) { // Less than 1 second
        PerformanceMonitor.rushedResponses++;
    }
    
    return responseTime;
}
```

**4.2 Pattern Detection**
```javascript
function detectFatiguePatterns() {
    const recent = PerformanceMonitor.checkpoints.slice(-3);
    const baseline = PerformanceMonitor.baseline.avgReaction;
    
    // Calculate slowdown
    const avgRecent = recent.reduce((a,b) => a + b.time, 0) / recent.length;
    const slowdown = (avgRecent - baseline) / baseline;
    
    if (slowdown > 0.2) { // 20% slower
        return 'moderate_fatigue';
    }
    if (slowdown > 0.4) { // 40% slower
        return 'high_fatigue';
    }
    
    return 'normal';
}
```

### Step 5: Create Fatigue Alert System (1 hour)

**5.1 Alert UI**
```html
<div id="fatigue-alert" class="alert-box" style="display:none">
    <div class="alert-content">
        <h3>Take a Break?</h3>
        <p>You seem a bit tired. Would you like to take a short break?</p>
        <button onclick="takeBreak()">Yes, 2-minute break</button>
        <button onclick="continueAssessment()">No, continue</button>
    </div>
</div>
```

**5.2 Alert Logic**
```javascript
function checkFatigueLevel() {
    const fatigue = detectFatiguePatterns();
    
    if (fatigue === 'high_fatigue' && !PerformanceMonitor.breakOffered) {
        showFatigueAlert();
        PerformanceMonitor.breakOffered = true;
    }
}

function takeBreak() {
    // Show break screen
    showBreakScreen();
    
    // Set 2-minute timer
    setTimeout(() => {
        hideBreakScreen();
        // Boost expected performance after break
        PerformanceMonitor.postBreakBoost = true;
    }, 120000);
}
```

### Step 6: Implement Simple Attention Test (1 hour)

**6.1 Embedded Attention Checks**
```javascript
// Randomly insert attention check questions
function createAttentionCheck() {
    return {
        id: 'attention_check_' + Date.now(),
        text: 'Please select "Strongly Agree" for this question',
        type: 'attention_check',
        correct_answer: '5'
    };
}

function insertAttentionChecks(questions) {
    const checkIndices = [
        Math.floor(questions.length * 0.3),
        Math.floor(questions.length * 0.7)
    ];
    
    checkIndices.forEach((index, i) => {
        questions.splice(index + i, 0, createAttentionCheck());
    });
    
    return questions;
}
```

### Step 7: Create Performance Dashboard (1.5 hours)

**7.1 Real-time Status Bar**
```html
<div id="performance-status" class="status-bar">
    <div class="status-item">
        <span class="label">Focus:</span>
        <span class="value" id="focus-level">Good</span>
    </div>
    <div class="status-item">
        <span class="label">Time:</span>
        <span class="value" id="elapsed-time">2:34</span>
    </div>
    <div class="status-item">
        <span class="label">Progress:</span>
        <span class="value" id="progress">45%</span>
    </div>
</div>
```

**7.2 Update Logic**
```javascript
function updatePerformanceStatus() {
    const focusLevel = calculateFocusLevel();
    const elapsed = formatTime(Date.now() - startTime);
    const progress = (completedSections / totalSections) * 100;
    
    document.getElementById('focus-level').textContent = focusLevel;
    document.getElementById('elapsed-time').textContent = elapsed;
    document.getElementById('progress').textContent = progress + '%';
    
    // Update color based on performance
    if (focusLevel === 'Low') {
        document.getElementById('focus-level').style.color = '#ff5252';
    }
}

// Update every 5 seconds
setInterval(updatePerformanceStatus, 5000);
```

### Step 8: Build Results Summary (1 hour)

**8.1 Performance Report**
```javascript
function generatePerformanceReport() {
    const checkpoints = PerformanceMonitor.checkpoints;
    const baseline = PerformanceMonitor.baseline;
    
    return {
        overallPerformance: calculateOverallPerformance(),
        fatigueOnset: detectFatigueOnsetTime(),
        attentionMetrics: {
            lapses: PerformanceMonitor.attentionLapses,
            rushedResponses: PerformanceMonitor.rushedResponses,
            attentionChecksPassed: PerformanceMonitor.attentionCheckResults
        },
        recommendations: generateRecommendations()
    };
}
```

**8.2 Summary UI**
```html
<div id="performance-summary">
    <h3>Performance Summary</h3>
    
    <div class="metric">
        <label>Focus Level:</label>
        <span id="final-focus">85%</span>
    </div>
    
    <div class="metric">
        <label>Consistency:</label>
        <span id="consistency">Good</span>
    </div>
    
    <div class="metric">
        <label>Fatigue Level:</label>
        <span id="fatigue-level">Mild</span>
    </div>
    
    <div class="recommendations">
        <h4>Recommendations:</h4>
        <ul id="performance-tips"></ul>
    </div>
</div>
```

### Step 9: Integration with Main Assessments (1.5 hours)

**9.1 Seamless Integration**
```javascript
// Initialize monitor when assessment starts
AssessmentController.start = function() {
    PerformanceMonitor.init();
    runBaselineTest().then(() => {
        startCoreAssessment();
    });
};

// Add checkpoints between sections
AssessmentController.nextSection = async function() {
    // Run checkpoint if not first or last section
    if (currentSection > 0 && currentSection < totalSections - 1) {
        await reactionCheckpoint();
        checkFatigueLevel();
    }
    
    loadNextSection();
};
```

### Step 10: Testing and Optimization (1 hour)

**10.1 Performance Testing**
```javascript
// Ensure monitoring doesn't slow down quiz
function benchmarkMonitoring() {
    const iterations = 1000;
    const start = performance.now();
    
    for (let i = 0; i < iterations; i++) {
        PerformanceMonitor.recordActivity();
        updatePerformanceStatus();
    }
    
    const elapsed = performance.now() - start;
    console.log(`Monitoring overhead: ${elapsed/iterations}ms per operation`);
}
```

## File Structure

```
assessments/
├── performance_monitoring/
│   ├── monitor.js
│   ├── baseline_test.html
│   ├── checkpoint_ui.html
│   └── performance_dashboard.css
├── static/
│   └── performance_integration.js
└── api/
    └── performance_api.py
```

## Implementation Timeline

- **Hour 1-2**: Basic monitor setup and activity tracking
- **Hour 3-4**: Baseline test implementation
- **Hour 5-6**: Checkpoint system
- **Hour 7-8**: Attention monitoring and fatigue detection
- **Hour 9-10**: Alerts and dashboard
- **Hour 11-12**: Integration and testing

Total: 12 hours (1.5 days)

## Simplification Strategies

1. **No complex algorithms** - Simple threshold-based detection
2. **No machine learning** - Rule-based fatigue detection
3. **Minimal UI** - Text-based status, no graphs
4. **Client-side only** - No real-time server sync
5. **Optional feature** - Can be disabled if issues

## Critical Metrics to Track

1. **Reaction Time Degradation**
   - Baseline vs current
   - Trend over time

2. **Attention Lapses**
   - Long pauses (>30s)
   - Missed attention checks

3. **Response Patterns**
   - Rushed responses (<1s)
   - Inconsistent timing

4. **Break Effectiveness**
   - Performance before/after breaks
   - Optimal break timing

## User Communication

Keep it simple and supportive:
- ✅ "You're doing great!"
- ✅ "Consider taking a short break"
- ✅ "Almost done - keep going!"
- ❌ "Your performance is declining"
- ❌ "You seem distracted"
- ❌ "Warning: Fatigue detected"

## Fallback Plan

If monitoring causes issues:
1. Disable real-time updates
2. Collect data passively
3. Show results only at end
4. Make entire system optional