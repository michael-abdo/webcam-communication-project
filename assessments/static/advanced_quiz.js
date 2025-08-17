// Advanced Assessment Quiz Engine
const AdvancedAssessment = {
    // Configuration
    totalTime: 360000, // 6 minutes in milliseconds
    sections: [
        {
            id: 'emotion_regulation',
            name: 'Emotion Regulation',
            template: 'emotion_regulation_template',
            timeAllocation: 0.25 // 25% of total time
        },
        {
            id: 'relationship_style',
            name: 'Relationship Style',
            template: 'relationship_style_template',
            timeAllocation: 0.20 // 20% of total time
        },
        {
            id: 'listening_preferences',
            name: 'Listening Preferences',
            template: 'listening_preferences_template',
            timeAllocation: 0.20 // 20% of total time
        },
        {
            id: 'loss_aversion',
            name: 'Loss Aversion',
            template: 'loss_aversion_template',
            timeAllocation: 0.20 // 20% of total time
        },
        {
            id: 'perspective_taking',
            name: 'Perspective Taking',
            template: 'perspective_taking_template',
            timeAllocation: 0.15 // 15% of total time
        }
    ],

    // State
    currentSection: -1, // -1 = intro, 0-4 = sections, 5 = results
    startTime: null,
    timeRemaining: 360000,
    sessionData: {
        userId: null,
        startTime: null,
        responses: {},
        sectionTimes: {},
        completed: false
    },
    timerInterval: null,

    // Initialization
    init() {
        this.sessionData.userId = this.generateUserId();
        this.setupEventListeners();
        this.loadFromStorage();
        this.updateDisplay();
        console.log('Advanced Assessment initialized');
    },

    generateUserId() {
        return 'adv_user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    setupEventListeners() {
        // Handle form submissions within sections
        document.addEventListener('submit', (e) => {
            if (e.target.closest('#section-content')) {
                e.preventDefault();
                this.handleSectionSubmit(e.target);
            }
        });

        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.saveToStorage();
        });
    },

    // Timer Management
    startTimer() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        
        this.startTime = Date.now();
        this.sessionData.startTime = this.startTime;
        
        this.timerInterval = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            this.timeRemaining = Math.max(0, this.totalTime - elapsed);
            
            this.updateTimerDisplay();
            
            // Time warnings
            if (this.timeRemaining <= 90000 && this.timeRemaining > 60000) {
                this.showTimeWarning('⏰ 1.5 minutes remaining');
            } else if (this.timeRemaining <= 60000 && this.timeRemaining > 30000) {
                this.showTimeWarning('⏰ 1 minute remaining');
            } else if (this.timeRemaining <= 30000 && this.timeRemaining > 0) {
                this.showTimeWarning('⚠️ 30 seconds remaining', true);
            } else if (this.timeRemaining <= 0) {
                this.timeExpired();
            }
        }, 1000);
    },

    updateTimerDisplay() {
        const minutes = Math.floor(this.timeRemaining / 60000);
        const seconds = Math.floor((this.timeRemaining % 60000) / 1000);
        const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        document.getElementById('timer').textContent = `Time remaining: ${display}`;
        
        // Change color as time runs out
        const timerElement = document.getElementById('timer');
        if (this.timeRemaining <= 30000) {
            timerElement.style.color = '#dc3545';
        } else if (this.timeRemaining <= 90000) {
            timerElement.style.color = '#ffc107';
        } else {
            timerElement.style.color = '#2196f3';
        }
    },

    showTimeWarning(message, critical = false) {
        const warningElement = document.getElementById('time-warning');
        warningElement.textContent = message;
        warningElement.style.display = 'block';
        if (critical) {
            warningElement.classList.add('time-critical');
        }
    },

    timeExpired() {
        clearInterval(this.timerInterval);
        this.autoSubmit();
    },

    // Navigation
    nextSection() {
        // Save current section data if in a section
        if (this.currentSection >= 0 && this.currentSection < this.sections.length) {
            this.saveSectionData();
        }

        this.currentSection++;
        
        if (this.currentSection === 0) {
            // Starting first section
            this.startTimer();
        }
        
        if (this.currentSection >= this.sections.length) {
            // Assessment complete
            this.completeAssessment();
        } else {
            this.loadSection(this.currentSection);
        }
        
        this.updateDisplay();
    },

    previousSection() {
        // Note: Generally disabled in timed assessment
        if (this.currentSection > 0) {
            this.currentSection--;
            this.loadSection(this.currentSection);
            this.updateDisplay();
        }
    },

    // Section Loading
    loadSection(sectionIndex) {
        const section = this.sections[sectionIndex];
        const container = document.getElementById('section-content');
        
        // Show section content, hide others
        document.getElementById('intro-screen').classList.remove('active');
        document.getElementById('results-screen').classList.remove('active');
        container.classList.add('active');
        
        // Record section start time
        this.sessionData.sectionTimes[section.id] = {
            startTime: Date.now()
        };

        // Load the appropriate section template
        this.loadSectionTemplate(section, container);
    },

    loadSectionTemplate(section, container) {
        let content = '';
        
        switch(section.id) {
            case 'emotion_regulation':
                content = this.getEmotionRegulationTemplate();
                break;
            case 'relationship_style':
                content = this.getRelationshipStyleTemplate();
                break;
            case 'listening_preferences':
                content = this.getListeningPreferencesTemplate();
                break;
            case 'loss_aversion':
                content = this.getLossAversionTemplate();
                break;
            case 'perspective_taking':
                content = this.getPerspectiveTakingTemplate();
                break;
        }
        
        container.innerHTML = `
            <div class="section-title">${section.name}</div>
            ${content}
        `;
    },

    // Section Templates (simplified versions for the unified assessment)
    getEmotionRegulationTemplate() {
        return `
            <form id="emotion-regulation-form">
                <div class="question-group">
                    <p><strong>Scenario: Your manager publicly criticizes your project unfairly. How would you handle this?</strong></p>
                    <div class="radio-group">
                        <label><input type="radio" name="emotion_strategy" value="reappraisal" required> <span>Reframe the situation positively</span></label>
                        <label><input type="radio" name="emotion_strategy" value="suppression" required> <span>Hide my emotions and stay professional</span></label>
                        <label><input type="radio" name="emotion_strategy" value="expression" required> <span>Speak up and defend my work</span></label>
                        <label><input type="radio" name="emotion_strategy" value="support" required> <span>Talk to colleagues for support</span></label>
                    </div>
                </div>
                <div class="question-group">
                    <p><strong>How intense would your emotional reaction be? (0 = Calm, 10 = Very upset)</strong></p>
                    <input type="range" name="emotion_intensity" min="0" max="10" value="5" 
                           oninput="this.nextElementSibling.textContent = this.value">
                    <span>5</span>
                </div>
            </form>
        `;
    },

    getRelationshipStyleTemplate() {
        return `
            <form id="relationship-style-form">
                <div class="question-group">
                    <p><strong>I worry about being abandoned by people close to me.</strong></p>
                    <div class="radio-group">
                        ${[1,2,3,4,5].map(val => `
                            <label><input type="radio" name="attachment_anxiety" value="${val}" required> <span>${val}</span></label>
                        `).join('')}
                    </div>
                    <small>1 = Strongly Disagree, 5 = Strongly Agree</small>
                </div>
                <div class="question-group">
                    <p><strong>I find it difficult to depend on others.</strong></p>
                    <div class="radio-group">
                        ${[1,2,3,4,5].map(val => `
                            <label><input type="radio" name="attachment_avoidance" value="${val}" required> <span>${val}</span></label>
                        `).join('')}
                    </div>
                    <small>1 = Strongly Disagree, 5 = Strongly Agree</small>
                </div>
            </form>
        `;
    },

    getListeningPreferencesTemplate() {
        return `
            <form id="listening-preferences-form">
                <div class="question-group">
                    <p><strong>When a friend shares a problem, what's your most natural response?</strong></p>
                    <div class="radio-group">
                        <label><input type="radio" name="listening_style" value="emotional_support" required> <span>Provide emotional comfort</span></label>
                        <label><input type="radio" name="listening_style" value="problem_solving" required> <span>Offer practical solutions</span></label>
                        <label><input type="radio" name="listening_style" value="perspective_taking" required> <span>Help them see different angles</span></label>
                        <label><input type="radio" name="listening_style" value="active_listening" required> <span>Ask questions to explore feelings</span></label>
                    </div>
                </div>
            </form>
        `;
    },

    getLossAversionTemplate() {
        return `
            <form id="loss-aversion-form">
                <div class="question-group">
                    <p><strong>Investment choice: $1,000 to invest. Which do you prefer?</strong></p>
                    <div class="radio-group">
                        <label><input type="radio" name="investment_choice" value="safe" required> <span>Guaranteed $200 gain</span></label>
                        <label><input type="radio" name="investment_choice" value="risky" required> <span>50% chance $400 gain, 50% chance $0</span></label>
                    </div>
                </div>
                <div class="question-group">
                    <p><strong>Loss scenario: Facing a $1,000 expense. Which do you prefer?</strong></p>
                    <div class="radio-group">
                        <label><input type="radio" name="loss_choice" value="certain" required> <span>Guaranteed $300 loss</span></label>
                        <label><input type="radio" name="loss_choice" value="gamble" required> <span>50% chance $600 loss, 50% chance $0 loss</span></label>
                    </div>
                </div>
            </form>
        `;
    },

    getPerspectiveTakingTemplate() {
        return `
            <form id="perspective-taking-form">
                <div class="question-group">
                    <p><strong>Team deadline conflict: Manager wants to push hard, developer wants quality, junior is burned out. Which perspective is most reasonable?</strong></p>
                    <div class="radio-group">
                        <label><input type="radio" name="team_perspective" value="manager" required> <span>Manager (deadline priority)</span></label>
                        <label><input type="radio" name="team_perspective" value="developer" required> <span>Developer (quality focus)</span></label>
                        <label><input type="radio" name="team_perspective" value="junior" required> <span>Junior (wellbeing concern)</span></label>
                        <label><input type="radio" name="team_perspective" value="balanced" required> <span>All have valid points</span></label>
                    </div>
                </div>
            </form>
        `;
    },

    // Data Management
    handleSectionSubmit(form) {
        // Validate form
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        // Proceed to next section
        this.nextSection();
    },

    saveSectionData() {
        if (this.currentSection < 0 || this.currentSection >= this.sections.length) return;
        
        const section = this.sections[this.currentSection];
        const form = document.querySelector(`#${section.id}-form`);
        
        if (form) {
            const formData = new FormData(form);
            const responses = {};
            
            for (let [key, value] of formData.entries()) {
                responses[key] = value;
            }
            
            this.sessionData.responses[section.id] = {
                ...responses,
                completedAt: Date.now()
            };
            
            // Record section completion time
            if (this.sessionData.sectionTimes[section.id]) {
                this.sessionData.sectionTimes[section.id].endTime = Date.now();
                this.sessionData.sectionTimes[section.id].duration = 
                    this.sessionData.sectionTimes[section.id].endTime - 
                    this.sessionData.sectionTimes[section.id].startTime;
            }
        }
        
        this.saveToStorage();
    },

    saveToStorage() {
        try {
            localStorage.setItem('advancedAssessmentData', JSON.stringify(this.sessionData));
        } catch (e) {
            console.warn('Could not save to localStorage:', e);
        }
    },

    loadFromStorage() {
        try {
            const saved = localStorage.getItem('advancedAssessmentData');
            if (saved) {
                const data = JSON.parse(saved);
                // Check if data is recent (within 1 hour)
                if (data.startTime && (Date.now() - data.startTime) < 3600000) {
                    this.sessionData = { ...this.sessionData, ...data };
                }
            }
        } catch (e) {
            console.warn('Could not load from localStorage:', e);
        }
    },

    // Assessment Control
    completeAssessment() {
        clearInterval(this.timerInterval);
        this.sessionData.completed = true;
        this.sessionData.completionTime = Date.now();
        
        // Calculate total time used
        const totalTimeUsed = this.sessionData.completionTime - this.sessionData.startTime;
        
        // Show results screen
        document.getElementById('section-content').classList.remove('active');
        document.getElementById('results-screen').classList.add('active');
        
        // Update completion stats
        const sectionsCompleted = Object.keys(this.sessionData.responses).length;
        document.getElementById('sections-completed').textContent = `${sectionsCompleted}/5`;
        
        const timeUsedMin = Math.floor(totalTimeUsed / 60000);
        const timeUsedSec = Math.floor((totalTimeUsed % 60000) / 1000);
        document.getElementById('time-used').textContent = `${timeUsedMin}:${timeUsedSec.toString().padStart(2, '0')}`;
        
        // Submit data to server
        this.submitAssessment();
        
        this.updateDisplay();
    },

    autoSubmit() {
        console.log('Time expired - auto-submitting assessment');
        this.completeAssessment();
    },

    submitAssessment() {
        const assessmentData = {
            ...this.sessionData,
            assessmentType: 'advanced',
            userAgent: navigator.userAgent,
            screenResolution: `${screen.width}x${screen.height}`
        };

        // Submit to server
        fetch('/api/quiz/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(assessmentData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Assessment submitted successfully:', data);
        })
        .catch(error => {
            console.error('Error submitting assessment:', error);
        });
    },

    // UI Updates
    updateDisplay() {
        // Update section indicator
        const indicator = document.getElementById('section-indicator');
        if (this.currentSection < 0) {
            indicator.textContent = 'Ready to begin';
        } else if (this.currentSection >= this.sections.length) {
            indicator.textContent = 'Assessment complete';
        } else {
            indicator.textContent = `Section ${this.currentSection + 1} of ${this.sections.length}`;
        }

        // Update progress bar
        const progress = this.currentSection < 0 ? 0 : 
                        this.currentSection >= this.sections.length ? 100 :
                        ((this.currentSection + 1) / this.sections.length) * 100;
        
        document.getElementById('progress-fill').style.width = `${progress}%`;
        
        // Update progress text
        const progressText = document.getElementById('progress-text');
        if (this.currentSection < 0) {
            progressText.textContent = 'Ready to begin';
        } else if (this.currentSection >= this.sections.length) {
            progressText.textContent = 'Assessment completed';
        } else {
            progressText.textContent = `${this.sections[this.currentSection].name}`;
        }

        // Update navigation buttons
        const nextBtn = document.getElementById('next-btn');
        const backBtn = document.getElementById('back-btn');
        
        if (this.currentSection < 0) {
            nextBtn.textContent = 'Begin Assessment';
            nextBtn.style.display = 'block';
            backBtn.style.display = 'none';
        } else if (this.currentSection >= this.sections.length) {
            nextBtn.style.display = 'none';
            backBtn.style.display = 'none';
        } else {
            nextBtn.textContent = this.currentSection === this.sections.length - 1 ? 'Complete Assessment' : 'Next Section';
            nextBtn.style.display = 'block';
            backBtn.style.display = 'none'; // Disabled in timed assessment
        }
    }
};

// Global functions for HTML onclick handlers
function nextSection() {
    AdvancedAssessment.nextSection();
}

function previousSection() {
    AdvancedAssessment.previousSection();
}

function viewDetailedResults() {
    // Redirect to detailed results page
    window.location.href = '/results/advanced/' + AdvancedAssessment.sessionData.userId;
}