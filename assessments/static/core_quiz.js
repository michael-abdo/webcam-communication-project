// Core Assessment Quiz Engine
const CoreAssessment = {
    // Configuration
    totalTime: 240000, // 4 minutes in milliseconds
    sections: [
        {
            id: 'crt',
            name: 'Cognitive Reflection Test',
            template: 'crt_template',
            timeAllocation: 0.25 // 25% of total time
        },
        {
            id: 'numeracy',
            name: 'Numeracy & Calibration',
            template: 'numeracy_template',
            timeAllocation: 0.20 // 20% of total time
        },
        {
            id: 'aot',
            name: 'Open-Minded Thinking',
            template: 'aot_template',
            timeAllocation: 0.15 // 15% of total time
        },
        {
            id: 'intent',
            name: 'Intent Attribution',
            template: 'intent_template',
            timeAllocation: 0.15 // 15% of total time
        },
        {
            id: 'nfc',
            name: 'Need for Closure',
            template: 'nfc_template',
            timeAllocation: 0.15 // 15% of total time
        },
        {
            id: 'anchoring',
            name: 'Anchoring Test',
            template: 'anchoring_template',
            timeAllocation: 0.10 // 10% of total time
        }
    ],

    // State
    currentSection: -1, // -1 = intro, 0-5 = sections, 6 = results
    startTime: null,
    timeRemaining: 240000,
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
        console.log('Core Assessment initialized');
    },

    generateUserId() {
        return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
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
            if (this.timeRemaining <= 60000 && this.timeRemaining > 30000) {
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
        } else if (this.timeRemaining <= 60000) {
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
            case 'crt':
                content = this.getCRTTemplate();
                break;
            case 'numeracy':
                content = this.getNumeracyTemplate();
                break;
            case 'aot':
                content = this.getAOTTemplate();
                break;
            case 'intent':
                content = this.getIntentTemplate();
                break;
            case 'nfc':
                content = this.getNFCTemplate();
                break;
            case 'anchoring':
                content = this.getAnchoringTemplate();
                break;
        }
        
        container.innerHTML = `
            <div class="section-title">${section.name}</div>
            ${content}
        `;
    },

    // Section Templates (simplified versions for the unified assessment)
    getCRTTemplate() {
        return `
            <form id="crt-form">
                <div class="question-group">
                    <p><strong>1. A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?</strong></p>
                    <input type="number" name="bat_ball" step="0.01" required placeholder="Enter amount in dollars">
                </div>
                <div class="question-group">
                    <p><strong>2. If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?</strong></p>
                    <input type="number" name="widgets" required placeholder="Enter time in minutes">
                </div>
                <div class="question-group">
                    <p><strong>3. In a lake, there is a patch of lily pads. Every day, the patch doubles in size. If it takes 48 days for the patch to cover the entire lake, how long would it take for the patch to cover half of the lake?</strong></p>
                    <input type="number" name="lily_pad" required placeholder="Enter number of days">
                </div>
            </form>
            <style>
                .question-group { margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; }
                .question-group input { width: 100%; padding: 8px; margin-top: 10px; border: 1px solid #ddd; border-radius: 4px; }
            </style>
        `;
    },

    getNumeracyTemplate() {
        return `
            <form id="numeracy-form">
                <div class="question-group">
                    <p><strong>1. If a disease affects 1 in 1,000 people, and you test positive with a 99% accurate test, what is the probability you actually have the disease?</strong></p>
                    <input type="number" name="disease_prob" step="0.01" max="100" required placeholder="Enter percentage (0-100)">
                </div>
                <div class="question-group">
                    <p><strong>2. If you flip a fair coin 3 times, what is the probability of getting at least 2 heads?</strong></p>
                    <input type="number" name="coin_prob" step="0.01" max="1" required placeholder="Enter probability (0-1)">
                </div>
            </form>
            <style>
                .question-group { margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; }
                .question-group input { width: 100%; padding: 8px; margin-top: 10px; border: 1px solid #ddd; border-radius: 4px; }
            </style>
        `;
    },

    getAOTTemplate() {
        const questions = [
            "People should take into consideration evidence that goes against their beliefs.",
            "It is important to persevere in your beliefs even when evidence is brought to bear against them.",
            "Changing your mind is a sign of weakness."
        ];
        
        let content = '<form id="aot-form">';
        questions.forEach((q, i) => {
            content += `
                <div class="question-group">
                    <p><strong>${i+1}. ${q}</strong></p>
                    <div class="radio-group">
                        ${[1,2,3,4,5].map(val => `
                            <label><input type="radio" name="q${i+1}" value="${val}" required> ${val}</label>
                        `).join('')}
                    </div>
                </div>
            `;
        });
        content += '</form>';
        
        content += `
            <style>
                .question-group { margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; }
                .radio-group { display: flex; gap: 15px; margin-top: 10px; }
                .radio-group label { cursor: pointer; padding: 5px 10px; border: 1px solid #ddd; border-radius: 3px; }
            </style>
        `;
        
        return content;
    },

    getIntentTemplate() {
        return `
            <form id="intent-form">
                <div class="question-group">
                    <p><strong>Scenario: You sent an important work email 3 days ago. Your colleague hasn't responded yet.</strong></p>
                    <p>Why do you think they haven't responded?</p>
                    <div class="radio-group-vertical">
                        <label><input type="radio" name="email_intent" value="hostile" required> They're deliberately ignoring me</label>
                        <label><input type="radio" name="email_intent" value="neutral" required> They're probably busy with other priorities</label>
                        <label><input type="radio" name="email_intent" value="benign" required> They might have missed the email</label>
                    </div>
                </div>
                <div class="question-group">
                    <p><strong>Scenario: A colleague interrupts you during a presentation to point out problems with your idea.</strong></p>
                    <p>Why do you think they interrupted?</p>
                    <div class="radio-group-vertical">
                        <label><input type="radio" name="interrupt_intent" value="hostile" required> They want to undermine me</label>
                        <label><input type="radio" name="interrupt_intent" value="neutral" required> They're being direct about business concerns</label>
                        <label><input type="radio" name="interrupt_intent" value="benign" required> They're trying to help improve the idea</label>
                    </div>
                </div>
            </form>
            <style>
                .question-group { margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; }
                .radio-group-vertical { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
                .radio-group-vertical label { cursor: pointer; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }
            </style>
        `;
    },

    getNFCTemplate() {
        const questions = [
            "I prefer tasks and situations that have clear, definite right and wrong answers.",
            "I feel uncomfortable when I don't understand the reason why an event occurred in my life.",
            "I like to have things settled and decided rather than leaving them open and uncertain."
        ];
        
        let content = '<form id="nfc-form">';
        questions.forEach((q, i) => {
            content += `
                <div class="question-group">
                    <p><strong>${i+1}. ${q}</strong></p>
                    <div class="radio-group">
                        ${[1,2,3,4,5].map(val => `
                            <label><input type="radio" name="nfc${i+1}" value="${val}" required> ${val}</label>
                        `).join('')}
                    </div>
                </div>
            `;
        });
        content += '</form>';
        
        content += `
            <style>
                .question-group { margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; }
                .radio-group { display: flex; gap: 15px; margin-top: 10px; }
                .radio-group label { cursor: pointer; padding: 5px 10px; border: 1px solid #ddd; border-radius: 3px; }
            </style>
        `;
        
        return content;
    },

    getAnchoringTemplate() {
        return `
            <form id="anchoring-form">
                <div class="question-group">
                    <p><strong>1. Is the population of Morocco more or less than 20 million people?</strong></p>
                    <div class="radio-group-vertical">
                        <label><input type="radio" name="morocco_comparison" value="more" required> More than 20 million</label>
                        <label><input type="radio" name="morocco_comparison" value="less" required> Less than 20 million</label>
                    </div>
                    <p style="margin-top: 15px;"><strong>What is your best estimate for Morocco's population?</strong></p>
                    <input type="number" name="morocco_estimate" min="1" max="100" required placeholder="Enter in millions">
                </div>
                <div class="question-group">
                    <p><strong>2. A tech startup with $10M revenue - worth more or less than $80 million?</strong></p>
                    <div class="radio-group-vertical">
                        <label><input type="radio" name="company_comparison" value="more" required> More than $80 million</label>
                        <label><input type="radio" name="company_comparison" value="less" required> Less than $80 million</label>
                    </div>
                    <p style="margin-top: 15px;"><strong>What is your valuation estimate?</strong></p>
                    <input type="number" name="company_estimate" min="1" max="1000" required placeholder="Enter in millions">
                </div>
            </form>
            <style>
                .question-group { margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; }
                .radio-group-vertical { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
                .radio-group-vertical label { cursor: pointer; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }
                .question-group input[type="number"] { width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ddd; border-radius: 4px; }
            </style>
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
            localStorage.setItem('coreAssessmentData', JSON.stringify(this.sessionData));
        } catch (e) {
            console.warn('Could not save to localStorage:', e);
        }
    },

    loadFromStorage() {
        try {
            const saved = localStorage.getItem('coreAssessmentData');
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
        document.getElementById('sections-completed').textContent = `${sectionsCompleted}/6`;
        
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
            assessmentType: 'core',
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
            // Redirect to results page after successful submission
            setTimeout(() => {
                window.location.href = '/results/core/' + this.sessionData.userId;
            }, 2000); // 2 second delay to show completion message
        })
        .catch(error => {
            console.error('Error submitting assessment:', error);
            // Even if submission fails, still redirect to results page
            setTimeout(() => {
                window.location.href = '/results/core/' + this.sessionData.userId;
            }, 3000);
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
    CoreAssessment.nextSection();
}

function previousSection() {
    CoreAssessment.previousSection();
}

function viewDetailedResults() {
    // Redirect to detailed results page
    window.location.href = '/results/core/' + CoreAssessment.sessionData.userId;
}