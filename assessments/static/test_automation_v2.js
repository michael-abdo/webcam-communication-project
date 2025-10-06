// Assessment Test Automation Script v2
// Updated for single-question-per-page interface with textarea inputs
// Detects questions by text content and fills appropriate answers

const TestAutomationV2 = {
    // Configuration
    enabled: false,
    autoAdvance: true,
    fillDelay: 500, // Delay between detecting and filling (ms)
    advanceDelay: 1500, // Delay before clicking next (ms)
    
    // Question patterns and responses
    questionPatterns: {
        // CRT Questions (Cognitive Reflection Test)
        crt: {
            // Bat and ball variants
            batBall: {
                patterns: [
                    /tool.*case.*cost.*\$?110/i,
                    /bat.*ball.*cost.*\$?1\.10/i,
                    /pen.*pencil.*cost.*\$?1\.10/i,
                    /book.*bookmark.*cost.*\$?1\.10/i
                ],
                answer: "5" // $5 or 5 cents depending on variant
            },
            
            // Machine/widget questions
            widgets: {
                patterns: [
                    /machines?.*minutes?.*widgets?/i,
                    /workers?.*hours?.*products?/i,
                    /printers?.*minutes?.*pages?/i
                ],
                answer: "5" // 5 minutes for 100 machines to make 100 widgets
            },
            
            // Lily pad doubling questions
            lilyPad: {
                patterns: [
                    /lily pads?.*double.*lake/i,
                    /bacteria.*double.*petri/i,
                    /plants?.*double.*garden/i,
                    /patch.*double.*48 days/i
                ],
                answer: "47" // 47 days for half the lake
            }
        },
        
        // Numeracy Questions
        numeracy: {
            // Disease probability (Bayesian reasoning)
            bayesian: {
                patterns: [
                    /disease.*1 in 1,?000.*test.*99%/i,
                    /condition.*0\.1%.*test.*99%/i,
                    /illness.*test.*positive.*probability/i
                ],
                answer: "9" // Approximately 9% actual probability
            },
            
            // Coin flip probability
            coinFlip: {
                patterns: [
                    /coin.*3 times.*at least 2 heads/i,
                    /flip.*fair coin.*probability.*heads/i,
                    /toss.*coin.*2 or more heads/i
                ],
                answer: "0.5" // 50% probability
            },
            
            // Percentage questions
            percentage: {
                patterns: [
                    /what percentage/i,
                    /percent chance/i,
                    /probability.*percent/i
                ],
                answer: "50" // Default percentage answer
            }
        },
        
        // Anchoring Questions
        anchoring: {
            // Population estimates
            population: {
                patterns: [
                    /population.*morocco.*million/i,
                    /people.*country.*million/i,
                    /inhabitants.*nation/i
                ],
                answer: "37" // Morocco population estimate
            },
            
            // Company valuation
            valuation: {
                patterns: [
                    /startup.*revenue.*worth.*million/i,
                    /company.*valuation.*million/i,
                    /business.*value.*\$.*million/i
                ],
                answer: "60" // Reasonable startup valuation
            },
            
            // Comparison questions (more/less)
            comparison: {
                patterns: [
                    /more or less than/i,
                    /greater or less than/i,
                    /above or below/i
                ],
                answer: "more" // Default comparison answer
            }
        },
        
        // Social/Intent Questions
        social: {
            // Email response scenarios
            emailIntent: {
                patterns: [
                    /email.*3 days.*haven't responded/i,
                    /message.*no reply.*colleague/i,
                    /sent.*important.*no response/i
                ],
                answer: "They're probably busy with other priorities"
            },
            
            // Interruption scenarios
            interruptIntent: {
                patterns: [
                    /colleague interrupts.*presentation/i,
                    /someone interrupts.*meeting/i,
                    /interrupted.*speaking/i
                ],
                answer: "They're being direct about business concerns"
            }
        },
        
        // Probability/Statistics Questions (button-based)
        probability: {
            // Dice questions
            diceProbability: {
                patterns: [
                    /six-sided die.*rolled once.*more likely/i,
                    /fair die.*which.*more likely/i,
                    /die.*greater than.*even number/i
                ],
                answer: "An even number" // Even numbers: 2,4,6 (3/6) vs >4: 5,6 (2/6)
            },
            
            // Card probability
            cardProbability: {
                patterns: [
                    /deck of cards.*more likely/i,
                    /playing card.*probability/i
                ],
                answer: "Red card" // Default to more likely option
            },
            
            // General probability comparisons
            generalProbability: {
                patterns: [
                    /more likely.*probability/i,
                    /which.*greater chance/i,
                    /higher probability/i
                ],
                answer: "first" // Default to first option
            }
        }
    },
    
    // Main detection and filling function
    detectAndFillQuestion() {
        if (!this.enabled) return;
        
        console.log('🤖 Detecting question type...');
        
        // Get question text
        const questionElement = document.getElementById('questionText') || 
                               document.querySelector('.question-text') ||
                               document.querySelector('h3');
        
        if (!questionElement) {
            console.log('🤖 No question text found');
            return;
        }
        
        const questionText = questionElement.textContent || questionElement.innerText;
        console.log('🤖 Question text:', questionText);
        
        // Check for textarea input
        const textInput = document.querySelector('textarea.text-input') ||
                         document.querySelector('textarea') ||
                         document.querySelector('input[type="text"]') ||
                         document.querySelector('input[type="number"]');
        
        // Check for radio buttons
        const radioButtons = document.querySelectorAll('input[type="radio"]');
        
        // Check for option buttons (new interface)
        const optionButtons = document.querySelectorAll('.option-button');
        
        // Detect question type and get answer
        const answer = this.detectQuestionType(questionText);
        
        if (answer && textInput) {
            console.log('🤖 Filling text input with:', answer);
            textInput.value = answer;
            textInput.dispatchEvent(new Event('input', { bubbles: true }));
            textInput.dispatchEvent(new Event('change', { bubbles: true }));
        } else if (optionButtons.length > 0) {
            console.log('🤖 Handling option button question');
            this.handleOptionButtons(questionText, optionButtons);
        } else if (radioButtons.length > 0) {
            console.log('🤖 Handling radio button question');
            this.handleRadioQuestion(questionText, radioButtons);
        } else {
            console.log('🤖 No suitable input found or no answer pattern matched');
        }
        
        // Auto-advance if enabled
        if (this.autoAdvance) {
            setTimeout(() => {
                this.clickNext();
            }, this.advanceDelay);
        }
    },
    
    // Question type detection
    detectQuestionType(questionText) {
        // Check CRT patterns
        for (const [crtType, crtData] of Object.entries(this.questionPatterns.crt)) {
            for (const pattern of crtData.patterns) {
                if (pattern.test(questionText)) {
                    console.log('🤖 Detected CRT question:', crtType);
                    return crtData.answer;
                }
            }
        }
        
        // Check numeracy patterns
        for (const [numType, numData] of Object.entries(this.questionPatterns.numeracy)) {
            for (const pattern of numData.patterns) {
                if (pattern.test(questionText)) {
                    console.log('🤖 Detected numeracy question:', numType);
                    return numData.answer;
                }
            }
        }
        
        // Check anchoring patterns
        for (const [anchorType, anchorData] of Object.entries(this.questionPatterns.anchoring)) {
            for (const pattern of anchorData.patterns) {
                if (pattern.test(questionText)) {
                    console.log('🤖 Detected anchoring question:', anchorType);
                    return anchorData.answer;
                }
            }
        }
        
        // Check social patterns
        for (const [socialType, socialData] of Object.entries(this.questionPatterns.social)) {
            for (const pattern of socialData.patterns) {
                if (pattern.test(questionText)) {
                    console.log('🤖 Detected social question:', socialType);
                    return socialData.answer;
                }
            }
        }
        
        // Check probability patterns (for button-based questions)
        for (const [probType, probData] of Object.entries(this.questionPatterns.probability)) {
            for (const pattern of probData.patterns) {
                if (pattern.test(questionText)) {
                    console.log('🤖 Detected probability question:', probType);
                    return probData.answer;
                }
            }
        }
        
        console.log('🤖 No pattern matched, using fallback');
        return this.getFallbackAnswer(questionText);
    },
    
    // Handle option button questions (new interface)
    handleOptionButtons(questionText, optionButtons) {
        console.log('🤖 Processing option buttons...');
        
        // Get the answer for this question
        const targetAnswer = this.detectQuestionType(questionText);
        
        if (!targetAnswer) {
            console.log('🤖 No answer pattern found, selecting first option');
            optionButtons[0].click();
            return;
        }
        
        // Find button with matching text
        let selectedButton = null;
        for (const button of optionButtons) {
            const buttonText = button.textContent || button.innerText;
            console.log('🤖 Checking button text:', buttonText);
            
            // Exact match
            if (buttonText.trim() === targetAnswer) {
                selectedButton = button;
                console.log('🤖 Found exact match:', buttonText);
                break;
            }
            
            // Partial match (case insensitive)
            if (buttonText.toLowerCase().includes(targetAnswer.toLowerCase()) ||
                targetAnswer.toLowerCase().includes(buttonText.toLowerCase())) {
                selectedButton = button;
                console.log('🤖 Found partial match:', buttonText);
                break;
            }
        }
        
        // Fallback: check for specific patterns
        if (!selectedButton) {
            console.log('🤖 No text match, using pattern matching...');
            
            for (const button of optionButtons) {
                const buttonText = button.textContent || button.innerText;
                
                // Dice question specific logic
                if (/die.*greater than.*even/i.test(questionText)) {
                    if (/even number/i.test(buttonText)) {
                        selectedButton = button;
                        console.log('🤖 Selected even number for dice question');
                        break;
                    }
                }
                
                // General "more likely" patterns
                if (/more likely/i.test(questionText)) {
                    if (/even/i.test(buttonText) || /red/i.test(buttonText)) {
                        selectedButton = button;
                        console.log('🤖 Selected likely option:', buttonText);
                        break;
                    }
                }
            }
        }
        
        // Final fallback: select first option
        if (!selectedButton) {
            selectedButton = optionButtons[0];
            console.log('🤖 Fallback: selecting first option');
        }
        
        if (selectedButton) {
            selectedButton.click();
            selectedButton.classList.add('selected'); // Add visual feedback
            console.log('🤖 Clicked option button:', selectedButton.textContent);
        }
    },
    
    // Handle radio button questions (Likert scales, multiple choice)
    handleRadioQuestion(questionText, radioButtons) {
        // Group radio buttons by name
        const radioGroups = {};
        radioButtons.forEach(radio => {
            const name = radio.name;
            if (!radioGroups[name]) radioGroups[name] = [];
            radioGroups[name].push(radio);
        });
        
        // Fill each group
        Object.entries(radioGroups).forEach(([groupName, buttons]) => {
            let selectedValue = '3'; // Default to middle option
            
            // Check for specific patterns
            if (/more or less/i.test(questionText)) {
                // Anchoring comparison questions
                selectedValue = this.getComparisonAnswer(questionText);
            } else if (/agree|disagree/i.test(questionText)) {
                // Likert agreement scales
                selectedValue = '3'; // Neutral
            } else if (/scenario|situation/i.test(questionText)) {
                // Social scenario questions - pick neutral option
                const neutralOptions = buttons.filter(btn => 
                    /neutral|business|direct|busy|priorities/i.test(btn.value) ||
                    /neutral|business|direct|busy|priorities/i.test(btn.nextElementSibling?.textContent || '')
                );
                if (neutralOptions.length > 0) {
                    neutralOptions[0].checked = true;
                    neutralOptions[0].dispatchEvent(new Event('change', { bubbles: true }));
                    return;
                }
            }
            
            // Select by value or middle option
            const targetButton = buttons.find(btn => btn.value === selectedValue) ||
                               buttons[Math.floor(buttons.length / 2)];
            
            if (targetButton) {
                targetButton.checked = true;
                targetButton.dispatchEvent(new Event('change', { bubbles: true }));
                console.log('🤖 Selected radio option:', selectedValue);
            }
        });
    },
    
    // Get comparison answer for anchoring questions
    getComparisonAnswer(questionText) {
        if (/morocco.*20 million/i.test(questionText)) return 'more';
        if (/startup.*80 million/i.test(questionText)) return 'less';
        return 'more'; // Default
    },
    
    // Fallback answer generation
    getFallbackAnswer(questionText) {
        // Number questions
        if (/\$\d+|\d+\$|cost|price|amount/i.test(questionText)) {
            if (/cent|¢/i.test(questionText)) return "5";
            if (/million/i.test(questionText)) return "50";
            if (/dollar|\$/i.test(questionText)) return "5";
            return "10";
        }
        
        // Probability questions
        if (/probability|chance|percent/i.test(questionText)) {
            return "0.5";
        }
        
        // Time questions
        if (/minute|hour|day|time/i.test(questionText)) {
            return "5";
        }
        
        // Default fallback
        return "3";
    },
    
    // Navigation function - updated for new interface
    clickNext() {
        // Try TestSession.submitAnswer() first (for the new interface)
        if (typeof TestSession !== 'undefined' && TestSession.submitAnswer) {
            console.log('🤖 Calling TestSession.submitAnswer()');
            TestSession.submitAnswer();
            return;
        }
        
        // Fallback to button clicking
        const nextSelectors = [
            '#submitButton',
            'button[onclick*="submitAnswer"]',
            'button[onclick*="next"]',
            '.submit-button',
            '.nav-button:not(#skipButton)',
            '#next-btn',
            '.btn-primary',
            'input[type="submit"]'
        ];
        
        for (const selector of nextSelectors) {
            const button = document.querySelector(selector);
            if (button && button.offsetParent !== null && !button.disabled) {
                console.log('🤖 Clicking button:', selector);
                button.click();
                return;
            }
        }
        
        console.log('🤖 No suitable next button found');
    },
    
    // Control functions
    start() {
        this.enabled = true;
        console.log('🤖 Test Automation V2 ENABLED');
        
        // Fill current question immediately
        setTimeout(() => {
            this.detectAndFillQuestion();
        }, this.fillDelay);
        
        // Set up observer for question changes
        this.setupQuestionObserver();
    },
    
    stop() {
        this.enabled = false;
        console.log('🤖 Test Automation V2 DISABLED');
        
        if (this.observer) {
            this.observer.disconnect();
        }
    },
    
    // Watch for question changes in single-question interface
    setupQuestionObserver() {
        if (this.observer) {
            this.observer.disconnect();
        }
        
        this.observer = new MutationObserver((mutations) => {
            if (!this.enabled) return;
            
            let shouldFill = false;
            mutations.forEach((mutation) => {
                // Check if question text changed
                if (mutation.target.id === 'questionText' || 
                    mutation.target.classList?.contains('question-text') ||
                    mutation.target.id === 'questionCard') {
                    shouldFill = true;
                }
                
                // Check if new content was added
                if (mutation.type === 'childList') {
                    const addedNodes = Array.from(mutation.addedNodes);
                    if (addedNodes.some(node => 
                        node.id === 'questionCard' || 
                        node.classList?.contains('question-card') ||
                        node.querySelector && node.querySelector('#questionText'))) {
                        shouldFill = true;
                    }
                }
            });
            
            if (shouldFill) {
                setTimeout(() => {
                    this.detectAndFillQuestion();
                }, this.fillDelay);
            }
        });
        
        // Observe the question container and document body
        const questionContainer = document.getElementById('questionCard') || 
                                document.querySelector('.question-card') || 
                                document.body;
        
        this.observer.observe(questionContainer, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class'],
            characterData: true
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
    },
    
    // Manual fill for current question
    fillCurrent() {
        this.detectAndFillQuestion();
    }
};

// Global convenience functions
window.startTestAutomationV2 = () => TestAutomationV2.start();
window.stopTestAutomationV2 = () => TestAutomationV2.stop();
window.fillCurrentQuestion = () => TestAutomationV2.fillCurrent();
window.autoAdvanceOn = () => TestAutomationV2.setAutoAdvance(true);
window.autoAdvanceOff = () => TestAutomationV2.setAutoAdvance(false);

// Backward compatibility
window.startTestAutomation = window.startTestAutomationV2;
window.stopTestAutomation = window.stopTestAutomationV2;
window.fillCurrentSection = window.fillCurrentQuestion;

// Auto-initialization message
console.log('🤖 Test Automation V2 Script Loaded');
console.log('🤖 Updated for single-question-per-page interface');
console.log('🤖 Usage:');
console.log('  startTestAutomationV2() - Start automatic question filling');
console.log('  stopTestAutomationV2() - Stop automation');
console.log('  fillCurrentQuestion() - Fill current question only');
console.log('  autoAdvanceOn/Off() - Control auto-navigation');

// Expose the main object
window.TestAutomationV2 = TestAutomationV2;