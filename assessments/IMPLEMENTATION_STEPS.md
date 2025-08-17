# Interactive Quiz Implementation Steps

## Phase 1: Foundation Setup (Day 1-2)

### Step 1: Create Basic Directory Structure
```bash
mkdir -p assessments/static
mkdir -p assessments/templates
mkdir -p assessments/api
mkdir -p assessments/data
```

### Step 2: Set Up Basic HTML Template
1. Create `assessments/templates/base.html`
2. Add minimal CSS (no frameworks)
3. Include basic meta tags for mobile
4. Test in browser

### Step 3: Create Simple Quiz Engine
1. Create `assessments/static/quiz.js` (< 100 lines)
2. Implement basic form handling
3. Add local storage for session recovery
4. Test form submission

### Step 4: Set Up API Endpoint
1. Create `assessments/api/quiz_routes.py`
2. Add single POST endpoint `/api/quiz/submit`
3. Implement basic validation
4. Return JSON response

## Phase 2: Core Assessment Components (Day 3-5)

### Step 5: Implement CRT Quiz
1. Copy `crt_simple.html` to templates
2. Update `quiz.js` to handle CRT logic
3. Create scoring function (correct vs intuitive)
4. Test with 3 questions

### Step 6: Implement AOT Scale
1. Copy `aot_simple.html` to templates
2. Add Likert scale handling to `quiz.js`
3. Implement reverse scoring
4. Test with 5 questions

### Step 7: Implement Numeracy Test
1. Create simple numeracy HTML
2. Add number input validation
3. Create confidence radio buttons
4. Test calculations

### Step 8: Implement Intent Attribution
1. Create scenario display HTML
2. Add multiple choice logic
3. Create simple scoring
4. Test with 2 scenarios

## Phase 3: Performance Monitoring (Day 6-7)

### Step 9: Add Reaction Time Test
1. Copy `reaction_time_simple.html`
2. Implement timing logic
3. Calculate basic statistics
4. Add fatigue detection

### Step 10: Create Simple Progress Tracking
1. Add section counter
2. Show "Question X of Y"
3. Store progress in session
4. Enable section skipping

## Phase 4: Data Collection (Day 8-9)

### Step 11: Implement Data Storage
1. Create JSON file storage
2. Add timestamp to all responses
3. Implement basic data validation
4. Create results directory

### Step 12: Add Basic Results Display
1. Create results summary page
2. Calculate all scores
3. Show simple text feedback
4. Add "Download Results" button

## Phase 5: Integration (Day 10-11)

### Step 13: Connect to FastAPI
1. Mount static files
2. Add template rendering
3. Create session management
4. Test full flow

### Step 14: Add Error Handling
1. Implement try-catch blocks
2. Add user-friendly error messages
3. Create fallback for JS disabled
4. Test edge cases

## Phase 6: Testing & Polish (Day 12-14)

### Step 15: Cross-browser Testing
1. Test in Chrome, Firefox, Safari
2. Check mobile responsiveness
3. Verify form submissions
4. Fix any issues

### Step 16: Add Missing Components
1. Create Need for Closure questions
2. Create Anchoring Test
3. Update scoring logic
4. Test completeness

### Step 17: Documentation
1. Create user instructions
2. Document API endpoints
3. Add inline code comments
4. Create admin guide

## Detailed Task Breakdown

### Week 1 Focus
- **Monday**: Steps 1-4 (Foundation)
- **Tuesday**: Steps 5-6 (CRT & AOT)
- **Wednesday**: Steps 7-8 (Numeracy & Intent)
- **Thursday**: Steps 9-10 (Performance)
- **Friday**: Steps 11-12 (Data & Results)

### Week 2 Focus
- **Monday**: Steps 13-14 (Integration)
- **Tuesday**: Step 15 (Testing)
- **Wednesday**: Step 16 (Missing pieces)
- **Thursday**: Step 17 (Documentation)
- **Friday**: Buffer/Polish

## Command Checklist

```bash
# 1. Create all directories
mkdir -p assessments/{static,templates,api,data,results}

# 2. Copy simplified examples
cp assessments/static/crt_simple.html assessments/templates/
cp assessments/static/aot_simple.html assessments/templates/
cp assessments/static/reaction_time_simple.html assessments/templates/

# 3. Create main files
touch assessments/static/quiz.js
touch assessments/static/quiz.css
touch assessments/templates/base.html
touch assessments/api/quiz_routes.py

# 4. Test server
python -m http.server 8000 --directory assessments/static

# 5. Integration test
python main.py  # Assuming FastAPI app
```

## Success Criteria

Each step is complete when:
- [ ] Code runs without errors
- [ ] Data is captured correctly
- [ ] User can complete the flow
- [ ] Results are accurate
- [ ] No console errors
- [ ] Works on mobile

## Risk Mitigation

- **If behind schedule**: Skip advanced features, focus on core
- **If too complex**: Revert to simpler version
- **If bugs found**: Fix critical only, document others
- **If integration fails**: Use standalone version

## Daily Checklist

- [ ] Morning: Review today's steps
- [ ] Code for 2-hour blocks
- [ ] Test after each component
- [ ] Commit working code
- [ ] Evening: Update progress

## Remember

1. **Working > Perfect**
2. **Simple > Clever**
3. **Ship > Feature-complete**
4. **Data collection > Pretty UI**

The goal is a working assessment in 2 weeks, not a perfect one.