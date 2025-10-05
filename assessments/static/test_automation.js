// Assessment Test Automation Script
// This script automatically detects question types and provides dummy answers
// for rapid test completion and verification purposes

const TestAutomation = {
    // Configuration
    enabled: false,
    autoAdvance: true,
    fillDelay: 500, // Delay between filling fields (ms)
    advanceDelay: 1000, // Delay before clicking next (ms)
    
    // Dummy response patterns
    responses: {
        // CRT responses (deliberately mix correct and incorrect for testing)
        crt: {
            bat_ball: 0.05,  // Correct answer
            widgets: 5,      // Correct answer  
            lily_pad: 47     // Correct answer
        },
        
        // Numeracy responses
        numeracy: {
            disease_prob: 9.0,  // Approximately correct Bayesian answer
            coin_prob: 0.5      // 50% probability
        },
        
        // Likert scale responses (1-5 scale)
        likert: {
            default: 3,  // Neutral/middle response
            pattern: [3, 2, 4, 3, 2] // Varied pattern for multiple questions
        },
        
        // Multiple choice intent attribution
        intent: {
            email_intent: 'neutral',
            interrupt_intent: 'neutral'
        },
        
        // Anchoring responses
        anchoring: {
            morocco_comparison: 'more',
            morocco_estimate: 37,  // Close to actual population
            company_comparison: 'less',
            company_estimate: 60   // Reasonable tech startup valuation
        },
        
        // Advanced assessment responses
        advanced: {
            // Attachment style questions
            attachment: 'secure',
            
            // Big 5 personality responses (neutral to positive range)
            personality: {
                openness: 4,
                conscientiousness: 4,
                extraversion: 3,
                agreeableness: 4,
                neuroticism: 2
            },
            
            // Emotion regulation strategies
            regulation: {
                reappraisal: 4,
                suppression: 2,
                acceptance: 4,
                problem_solving: 4
            }
        }
    },
    
    // Auto-fill functions for different question types
    fillCRTQuestions() {
        console.log('🤖 Filling CRT questions...');
        
        // Bat and ball question
        const batBallInput = document.querySelector('input[name="bat_ball"]');
        if (batBallInput) {
            batBallInput.value = this.responses.crt.bat_ball;
            batBallInput.dispatchEvent(new Event('input'));
        }
        
        // Widgets question 
        const widgetsInput = document.querySelector('input[name="widgets"]');
        if (widgetsInput) {
            widgetsInput.value = this.responses.crt.widgets;
            widgetsInput.dispatchEvent(new Event('input'));
        }
        
        // Lily pad question
        const lilyPadInput = document.querySelector('input[name="lily_pad"]');
        if (lilyPadInput) {
            lilyPadInput.value = this.responses.crt.lily_pad;
            lilyPadInput.dispatchEvent(new Event('input'));
        }
    },
    
    fillNumeracyQuestions() {
        console.log('🤖 Filling Numeracy questions...');
        
        const diseaseProbInput = document.querySelector('input[name="disease_prob"]');
        if (diseaseProbInput) {
            diseaseProbInput.value = this.responses.numeracy.disease_prob;
            diseaseProbInput.dispatchEvent(new Event('input'));
        }
        
        const coinProbInput = document.querySelector('input[name="coin_prob"]');
        if (coinProbInput) {
            coinProbInput.value = this.responses.numeracy.coin_prob;
            coinProbInput.dispatchEvent(new Event('input'));
        }
    },
    
    fillLikertQuestions(sectionId = 'unknown') {
        console.log(`🤖 Filling Likert scale questions for ${sectionId}...`);
        
        // Find all radio button groups
        const radioGroups = {};
        const radioInputs = document.querySelectorAll('input[type="radio"]');
        
        radioInputs.forEach(input => {
            const name = input.name;
            if (!radioGroups[name]) {
                radioGroups[name] = [];
            }
            radioGroups[name].push(input);
        });
        
        // Fill each group with responses
        let patternIndex = 0;
        Object.keys(radioGroups).forEach(groupName => {
            const value = this.responses.likert.pattern[patternIndex % this.responses.likert.pattern.length] || this.responses.likert.default;
            const targetRadio = radioGroups[groupName].find(radio => radio.value == value);
            
            if (targetRadio) {
                targetRadio.checked = true;
                targetRadio.dispatchEvent(new Event('change'));
            }
            
            patternIndex++;
        });
    },
    
    fillIntentQuestions() {
        console.log('🤖 Filling Intent Attribution questions...');
        
        // Email intent question
        const emailIntentRadio = document.querySelector(`input[name="email_intent"][value="${this.responses.intent.email_intent}"]`);
        if (emailIntentRadio) {
            emailIntentRadio.checked = true;
            emailIntentRadio.dispatchEvent(new Event('change'));
        }
        
        // Interrupt intent question
        const interruptIntentRadio = document.querySelector(`input[name="interrupt_intent"][value="${this.responses.intent.interrupt_intent}"]`);
        if (interruptIntentRadio) {
            interruptIntentRadio.checked = true;
            interruptIntentRadio.dispatchEvent(new Event('change'));
        }
    },
    
    fillAnchoringQuestions() {
        console.log('🤖 Filling Anchoring questions...');
        
        // Morocco questions
        const moroccoCompRadio = document.querySelector(`input[name="morocco_comparison"][value="${this.responses.anchoring.morocco_comparison}"]`);
        if (moroccoCompRadio) {
            moroccoCompRadio.checked = true;
            moroccoCompRadio.dispatchEvent(new Event('change'));
        }
        
        const moroccoEstInput = document.querySelector('input[name="morocco_estimate"]');
        if (moroccoEstInput) {
            moroccoEstInput.value = this.responses.anchoring.morocco_estimate;
            moroccoEstInput.dispatchEvent(new Event('input'));
        }
        
        // Company valuation questions
        const companyCompRadio = document.querySelector(`input[name="company_comparison"][value="${this.responses.anchoring.company_comparison}"]`);
        if (companyCompRadio) {
            companyCompRadio.checked = true;
            companyCompRadio.dispatchEvent(new Event('change'));
        }
        
        const companyEstInput = document.querySelector('input[name="company_estimate"]');
        if (companyEstInput) {
            companyEstInput.value = this.responses.anchoring.company_estimate;
            companyEstInput.dispatchEvent(new Event('input'));
        }
    },
    
    // Main detection and filling function
    detectAndFillQuestions() {
        if (!this.enabled) return;
        
        console.log('🤖 Auto-filling detected questions...');
        
        // Detect current section by looking at form IDs or section content
        const crtForm = document.getElementById('crt-form');
        const numeracyForm = document.getElementById('numeracy-form');
        const aotForm = document.getElementById('aot-form');
        const nfcForm = document.getElementById('nfc-form');
        const intentForm = document.getElementById('intent-form');
        const anchoringForm = document.getElementById('anchoring-form');
        
        // Fill based on detected section
        if (crtForm && crtForm.offsetParent !== null) {
            this.fillCRTQuestions();
        } else if (numeracyForm && numeracyForm.offsetParent !== null) {
            this.fillNumeracyQuestions();
        } else if (aotForm && aotForm.offsetParent !== null) {
            this.fillLikertQuestions('aot');
        } else if (nfcForm && nfcForm.offsetParent !== null) {
            this.fillLikertQuestions('nfc');
        } else if (intentForm && intentForm.offsetParent !== null) {
            this.fillIntentQuestions();
        } else if (anchoringForm && anchoringForm.offsetParent !== null) {
            this.fillAnchoringQuestions();
        } else {
            // Fallback: detect by input types and names
            this.detectByInputPatterns();
        }
        
        // Auto-advance if enabled
        if (this.autoAdvance) {
            setTimeout(() => {
                this.clickNext();
            }, this.advanceDelay);
        }
    },
    
    // Fallback detection method
    detectByInputPatterns() {
        console.log('🤖 Using pattern detection...');
        
        // Check for CRT-specific inputs
        if (document.querySelector('input[name="bat_ball"]')) {
            this.fillCRTQuestions();
            return;
        }
        
        // Check for numeracy inputs
        if (document.querySelector('input[name="disease_prob"]')) {
            this.fillNumeracyQuestions();
            return;
        }
        
        // Check for intent inputs
        if (document.querySelector('input[name="email_intent"]')) {
            this.fillIntentQuestions();
            return;
        }
        
        // Check for anchoring inputs
        if (document.querySelector('input[name="morocco_comparison"]')) {
            this.fillAnchoringQuestions();
            return;
        }
        
        // Default to Likert if radio buttons found
        const radioButtons = document.querySelectorAll('input[type="radio"]');
        if (radioButtons.length > 0) {
            this.fillLikertQuestions('generic');
        }
    },
    
    // Navigation helper
    clickNext() {
        // Try multiple selectors for next button
        const nextSelectors = [
            '#next-btn',
            'button[onclick*="next"]',
            'button:contains("Next")',
            'button:contains("Continue")',
            'button:contains("Complete")',
            'input[type="submit"]',
            '.btn-primary'
        ];
        
        for (const selector of nextSelectors) {
            const button = document.querySelector(selector);
            if (button && button.offsetParent !== null && !button.disabled) {
                console.log('🤖 Clicking next button:', selector);
                button.click();
                break;
            }
        }
    },
    
    // Control functions
    start() {
        this.enabled = true;
        console.log('🤖 Test automation ENABLED');
        
        // Fill current section immediately
        setTimeout(() => {
            this.detectAndFillQuestions();
        }, this.fillDelay);
        
        // Set up observer for new sections
        this.setupSectionObserver();
    },
    
    stop() {
        this.enabled = false;
        console.log('🤖 Test automation DISABLED');
        
        if (this.observer) {
            this.observer.disconnect();
        }
    },
    
    // Watch for section changes
    setupSectionObserver() {
        if (this.observer) {
            this.observer.disconnect();
        }
        
        this.observer = new MutationObserver((mutations) => {
            if (!this.enabled) return;
            
            let shouldFill = false;
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' || mutation.type === 'attributes') {
                    // Check if new form content was added
                    if (mutation.target.querySelector && 
                        (mutation.target.querySelector('form') || 
                         mutation.target.id === 'section-content')) {
                        shouldFill = true;
                    }
                }
            });
            
            if (shouldFill) {
                setTimeout(() => {
                    this.detectAndFillQuestions();
                }, this.fillDelay);
            }
        });
        
        // Observe changes to the section content area
        const sectionContent = document.getElementById('section-content') || document.body;
        this.observer.observe(sectionContent, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
    },
    
    // Configuration helpers
    setAutoAdvance(enabled) {
        this.autoAdvance = enabled;
        console.log('🤖 Auto-advance:', enabled ? 'ENABLED' : 'DISABLED');
    },
    
    setTimings(fillDelay, advanceDelay) {
        this.fillDelay = fillDelay;
        this.advanceDelay = advanceDelay;
        console.log(`🤖 Timings updated: fill=${fillDelay}ms, advance=${advanceDelay}ms`);
    }
};

// Global convenience functions
window.startTestAutomation = () => TestAutomation.start();
window.stopTestAutomation = () => TestAutomation.stop();
window.fillCurrentSection = () => TestAutomation.detectAndFillQuestions();
window.autoAdvanceOn = () => TestAutomation.setAutoAdvance(true);
window.autoAdvanceOff = () => TestAutomation.setAutoAdvance(false);

// Auto-initialization when script loads
console.log('🤖 Test Automation Script Loaded');
console.log('🤖 Usage:');
console.log('  startTestAutomation() - Start automatic form filling');
console.log('  stopTestAutomation() - Stop automation');
console.log('  fillCurrentSection() - Fill current section only');
console.log('  autoAdvanceOn/Off() - Control auto-navigation');

// Expose the main object for advanced usage
window.TestAutomation = TestAutomation;