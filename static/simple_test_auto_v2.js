// Simple Test Automation V2 for Single-Question Interface
// Copy-paste this into browser console for quick automation

(function() {
    console.log('🤖 Simple Test Automation V2 Loaded');
    
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
        'email.*3 days.*haven\'t responded': 'neutral',
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
            
            let targetRating = '3'; // Default to neutral
            
            // Check for specific question patterns
            if (/look for reasons.*might be wrong/i.test(questionText) ||
                /consider evidence.*against/i.test(questionText) ||
                /open to changing.*opinion/i.test(questionText)) {
                targetRating = '4'; // Slightly agree for open-mindedness questions
            } else if (/changing.*mind.*weakness/i.test(questionText) ||
                      /stick to.*beliefs/i.test(questionText)) {
                targetRating = '2'; // Disagree with closed-minded statements
            }
            
            // Find and click the target rating button
            let selectedButton = null;
            for (const btn of ratingButtons) {
                if (btn.textContent.trim() === targetRating) {
                    selectedButton = btn;
                    break;
                }
            }
            
            // Fallback to middle button
            if (!selectedButton && ratingButtons.length > 0) {
                const middleIndex = Math.floor(ratingButtons.length / 2);
                selectedButton = ratingButtons[middleIndex];
                console.log('🤖 Fallback: selecting middle rating');
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
        
        const observer = new MutationObserver(() => {
            const questionCard = document.getElementById('questionCard');
            if (questionCard && questionCard.style.display !== 'none') {
                setTimeout(() => {
                    quickFillV2();
                    setTimeout(clickNextV2, 1500);
                }, 500);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style']
        });
        
        // Fill current question immediately
        setTimeout(autoRunV2, 500);
        
        window.stopContinuousV2 = () => {
            observer.disconnect();
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
    
    console.log('🤖 Available commands:');
    console.log('  quickFillV2() - Fill current question');
    console.log('  clickNextV2() - Click next button');
    console.log('  autoRunV2() - Fill and advance once');
    console.log('  startContinuousV2() - Fully automated test completion');
    console.log('  stopContinuousV2() - Stop continuous automation');
})();