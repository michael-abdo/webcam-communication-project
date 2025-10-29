// ==UserScript==
// @name         Auto Test Completion for Fatigue Detection
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Automatically completes assessment tests with neutral responses
// @author       Test Automation
// @match        https://fatigue-detection-api-570084330514.herokuapp.com/tests/*
// @match        https://fatigue-detection-api-*.herokuapp.com/tests/*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';

    console.log('🤖 Tampermonkey Auto Test Script Loading...');

    // Wait for page to fully load
    function waitForPageReady() {
        // Check if TestSession object exists (indicates test page is ready)
        if (typeof TestSession !== 'undefined') {
            console.log('🤖 Test page detected, injecting automation...');
            injectAutomation();
        } else {
            // Retry in 500ms
            setTimeout(waitForPageReady, 500);
        }
    }

    function injectAutomation() {
        // Inject the simple test automation script
        const script = document.createElement('script');
        script.textContent = `
// Simple Test Automation V2 for Single-Question Interface
// Auto-injected by Tampermonkey

(function() {
    console.log('🤖 Simple Test Automation V2 Loaded (Tampermonkey)');
    
    // Check for and disable full automation script if running
    if (window.TestAutomationV2 && window.TestAutomationV2.enabled) {
        console.log('🤖 Detected full automation running, stopping it...');
        window.TestAutomationV2.stop();
    }
    
    // Question patterns and answers
    const answers = {
        // CRT Questions
        'tool.*case.*cost.*110': '5',
        'bat.*ball.*cost.*1.10': '0.05',
        'machines?.*minutes?.*widgets?': '5',
        'lily pads?.*double.*lake': '47',
        'patch.*double.*48 days': '47',
        
        // Numeracy
        'disease.*1 in 1,?000.*test.*99%': '9',
        'coin.*3 times.*at least 2 heads': '0.5',
        'flip.*fair coin.*probability': '0.5',
        
        // Anchoring
        'population.*morocco.*million': '37',
        'startup.*revenue.*worth.*million': '60',
        'company.*valuation.*million': '60',
        
        // Fallbacks
        'cost|price|amount': '10',
        'probability|chance': '0.5',
        'percent': '50',
        'million': '50',
        'minute|hour|day': '5'
    };
    
    // Radio button responses
    const radioResponses = {
        'more or less than': 'more',
        'email.*3 days.*haven\\'t responded': 'neutral',
        'colleague interrupts.*presentation': 'neutral',
        'agree|disagree': '3' // Neutral on Likert scales
    };
    
    // Button-based responses (for option buttons)
    const buttonResponses = {
        'six-sided die.*rolled once.*more likely': 'An even number',
        'fair die.*which.*more likely': 'An even number',
        'die.*greater than.*even number': 'An even number',
        'deck of cards.*more likely': 'Red card',
        'more likely': 'even' // Generic fallback for probability questions
    };
    
    // Quick fill function for new interface
    function quickFillV2() {
        console.log('🤖 Quick filling current question...');
        
        // Get question text
        const questionElement = document.getElementById('questionText') || 
                               document.querySelector('.question-text') ||
                               document.querySelector('h3');
        
        if (!questionElement) {
            console.log('🤖 No question text found');
            return;
        }
        
        const questionText = questionElement.textContent || questionElement.innerText;
        console.log('🤖 Question:', questionText.substring(0, 100) + '...');
        
        // Check for text input (textarea or input)
        const textInput = document.querySelector('textarea.text-input') ||
                         document.querySelector('textarea') ||
                         document.querySelector('input[type="text"]') ||
                         document.querySelector('input[type="number"]');
        
        if (textInput) {
            // Find matching answer pattern
            let answer = '5'; // Default fallback
            
            for (const [pattern, value] of Object.entries(answers)) {
                const regex = new RegExp(pattern, 'i');
                if (regex.test(questionText)) {
                    answer = value;
                    console.log('🤖 Matched pattern:', pattern, '-> Answer:', answer);
                    break;
                }
            }
            
            textInput.value = answer;
            textInput.dispatchEvent(new Event('input', { bubbles: true }));
            textInput.dispatchEvent(new Event('change', { bubbles: true }));
            console.log('🤖 Filled text input with:', answer);
            return;
        }
        
        // Check for rating buttons (Likert scale - 1-5 or 1-7)
        const ratingButtons = document.querySelectorAll('.rating-button');
        if (ratingButtons.length > 0) {
            console.log('🤖 Found rating buttons (Likert scale)...');
            console.log('🤖 Number of rating buttons:', ratingButtons.length);
            
            // Always select the middle button for neutral response
            // Works for any scale: 1-5 (select 3), 1-7 (select 4), etc.
            let selectedButton = null;
            if (ratingButtons.length > 0) {
                const middleIndex = Math.floor(ratingButtons.length / 2);
                selectedButton = ratingButtons[middleIndex];
                console.log('🤖 Selecting middle rating (neutral):', selectedButton.textContent);
            }
            
            if (selectedButton) {
                selectedButton.click();
                selectedButton.classList.add('selected', 'active');
                console.log('🤖 Clicked rating button:', selectedButton.textContent);
            }
            return;
        }
        
        // Check for option buttons (new interface)
        const optionButtons = document.querySelectorAll('.option-button');
        if (optionButtons.length > 0) {
            console.log('🤖 Found option buttons, selecting appropriate answer...');
            
            let selectedButton = null;
            
            // Check for specific button response patterns
            for (const [pattern, response] of Object.entries(buttonResponses)) {
                const regex = new RegExp(pattern, 'i');
                if (regex.test(questionText)) {
                    // Find button with matching text
                    selectedButton = Array.from(optionButtons).find(btn => {
                        const btnText = btn.textContent || btn.innerText;
                        return btnText.toLowerCase().includes(response.toLowerCase()) ||
                               response.toLowerCase().includes(btnText.toLowerCase());
                    });
                    
                    if (selectedButton) {
                        console.log('🤖 Matched button pattern:', pattern, '-> Response:', response);
                        break;
                    }
                }
            }
            
            // Fallback: select based on common patterns
            if (!selectedButton) {
                console.log('🤖 Using fallback button selection...');
                for (const btn of optionButtons) {
                    const btnText = btn.textContent || btn.innerText;
                    
                    // For dice questions, prefer "even number"
                    if (/die.*greater than.*even/i.test(questionText) && /even number/i.test(btnText)) {
                        selectedButton = btn;
                        break;
                    }
                    
                    // For "more likely" questions, prefer even/red/common options
                    if (/more likely/i.test(questionText) && (/even/i.test(btnText) || /red/i.test(btnText))) {
                        selectedButton = btn;
                        break;
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
                selectedButton.classList.add('selected');
                console.log('🤖 Clicked option button:', selectedButton.textContent);
            }
            return;
        }
        
        // Check for radio buttons
        const radioButtons = document.querySelectorAll('input[type="radio"]');
        if (radioButtons.length > 0) {
            console.log('🤖 Found radio buttons, selecting appropriate answer...');
            
            // Group by name
            const radioGroups = {};
            radioButtons.forEach(radio => {
                const name = radio.name;
                if (!radioGroups[name]) radioGroups[name] = [];
                radioGroups[name].push(radio);
            });
            
            Object.entries(radioGroups).forEach(([groupName, buttons]) => {
                let selectedButton = null;
                
                // Check for specific response patterns
                for (const [pattern, response] of Object.entries(radioResponses)) {
                    const regex = new RegExp(pattern, 'i');
                    if (regex.test(questionText)) {
                        // Find button matching response
                        selectedButton = buttons.find(btn => 
                            btn.value === response ||
                            (btn.nextElementSibling && 
                             new RegExp(response, 'i').test(btn.nextElementSibling.textContent))
                        );
                        if (selectedButton) {
                            console.log('🤖 Matched radio pattern:', pattern, '-> Response:', response);
                            break;
                        }
                    }
                }
                
                // Fallback to middle option or neutral-sounding option
                if (!selectedButton) {
                    // Look for neutral options
                    selectedButton = buttons.find(btn => 
                        /neutral|moderate|business|busy|priorities|direct/i.test(btn.value) ||
                        (btn.nextElementSibling && 
                         /neutral|moderate|business|busy|priorities|direct/i.test(btn.nextElementSibling.textContent))
                    );
                    
                    // If no neutral option, select middle value or middle position
                    if (!selectedButton) {
                        selectedButton = buttons.find(btn => btn.value === '3') ||
                                       buttons[Math.floor(buttons.length / 2)];
                    }
                }
                
                if (selectedButton) {
                    selectedButton.checked = true;
                    selectedButton.dispatchEvent(new Event('change', { bubbles: true }));
                    console.log('🤖 Selected radio option');
                }
            });
            return;
        }
        
        console.log('🤖 No suitable input found');
    }
    
    // Navigation function for new interface
    function clickNextV2() {
        // Try TestSession.submitAnswer() first
        if (typeof TestSession !== 'undefined' && TestSession.submitAnswer) {
            console.log('🤖 Calling TestSession.submitAnswer()');
            TestSession.submitAnswer();
            return;
        }
        
        // Fallback to button clicking
        const selectors = [
            '#submitButton',
            'button[onclick*="submitAnswer"]',
            '.submit-button',
            '.nav-button:not(#skipButton)',
            'button[onclick*="next"]',
            '#next-btn',
            '.btn-primary',
            'input[type="submit"]'
        ];
        
        for (const sel of selectors) {
            const btn = document.querySelector(sel);
            if (btn && btn.offsetParent && !btn.disabled) {
                console.log('🤖 Clicking button:', sel);
                btn.click();
                return;
            }
        }
        
        console.log('🤖 No suitable next button found');
    }
    
    // Auto-run function
    function autoRunV2() {
        quickFillV2();
        setTimeout(clickNextV2, 1500);
    }
    
    // Continuous automation
    function startContinuousV2() {
        console.log('🤖 Starting continuous automation...');
        
        // Make sure full automation is stopped
        if (window.TestAutomationV2) {
            window.TestAutomationV2.stop();
            console.log('🤖 Full automation disabled for standalone mode');
        }
        
        // Store observer globally so we can stop it
        if (window.simpleAutoObserver) {
            window.simpleAutoObserver.disconnect();
        }
        
        window.simpleAutoObserver = new MutationObserver(() => {
            const questionCard = document.getElementById('questionCard');
            if (questionCard && questionCard.style.display !== 'none') {
                setTimeout(() => {
                    quickFillV2();
                    setTimeout(clickNextV2, 1500);
                }, 500);
            }
        });
        
        window.simpleAutoObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style']
        });
        
        // Fill current question immediately
        setTimeout(autoRunV2, 500);
        
        window.stopContinuousV2 = () => {
            if (window.simpleAutoObserver) {
                window.simpleAutoObserver.disconnect();
                window.simpleAutoObserver = null;
            }
            console.log('🤖 Continuous automation stopped');
        };
    }
    
    // Make functions globally available
    window.quickFillV2 = quickFillV2;
    window.clickNextV2 = clickNextV2;
    window.autoRunV2 = autoRunV2;
    window.startContinuousV2 = startContinuousV2;
    
    // Backward compatibility
    window.quickFill = quickFillV2;
    window.clickNext = clickNextV2;
    window.autoRun = autoRunV2;
    
    // Utility to ensure clean automation environment
    window.ensureCleanAutomation = () => {
        // Stop full automation if running
        if (window.TestAutomationV2 && window.TestAutomationV2.enabled) {
            window.TestAutomationV2.stop();
            console.log('🤖 Full automation stopped');
        }
        
        // Stop any existing simple automation
        if (window.simpleAutoObserver) {
            window.simpleAutoObserver.disconnect();
            window.simpleAutoObserver = null;
            console.log('🤖 Previous simple automation stopped');
        }
        
        console.log('🤖 Clean automation environment ready');
    };
    
    console.log('🤖 Tampermonkey automation ready!');
    console.log('🤖 Starting continuous automation in 2 seconds...');
    
    // Auto-start continuous mode after 2 seconds
    setTimeout(() => {
        console.log('🤖 Auto-starting continuous automation...');
        startContinuousV2();
    }, 2000);
    
})();
        `;
        
        document.head.appendChild(script);
        console.log('🤖 Automation script injected successfully');
    }

    // Start the process
    waitForPageReady();

    // Add stop automation keyboard shortcut (Ctrl/Cmd + Q)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'q') {
            e.preventDefault();
            if (window.stopContinuousV2) {
                window.stopContinuousV2();
                console.log('🤖 Automation stopped via keyboard shortcut (Ctrl/Cmd + Q)');
            }
        }
    });

    console.log('🤖 Tampermonkey script ready. Press Ctrl/Cmd + Q to stop automation.');
})();