/**
 * Test Video Session Manager
 * Coordinates test-taking with synchronized video recording
 */

const TestVideoSession = {
    // Test session properties
    sessionId: null,
    testData: null,
    currentTest: null,
    currentQuestionIndex: 0,
    currentAnswer: null,
    startTime: null,
    questionStartTime: null,
    sessionTimer: null,
    questionTimer: null,
    
    // Video recorder instance
    videoRecorder: null,
    videoSessionId: null,
    
    // Event tracking for correlation
    events: [],
    
    /**
     * Initialize the combined test-video session
     */
    async init() {
        console.log('[TestVideoSession] Initializing...');
        
        // Initialize video recorder first
        await this.initializeVideoRecorder();
        
        // Get test session ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        this.sessionId = urlParams.get('id') || sessionStorage.getItem('test_session_id');
        
        if (!this.sessionId) {
            this.showError('No test session found');
            setTimeout(() => window.location.href = '/tests', 2000);
            return;
        }
        
        // Load test data
        const testDataStr = sessionStorage.getItem('test_data');
        if (testDataStr) {
            this.testData = JSON.parse(testDataStr);
            await this.loadTestDefinition();
        } else {
            // Fallback: load from server
            await this.loadSessionFromServer();
        }
        
        console.log('[TestVideoSession] Initialization complete');
    },
    
    /**
     * Initialize video recorder component
     */
    async initializeVideoRecorder() {
        console.log('[TestVideoSession] Initializing video recorder...');
        
        // Create video recorder instance
        this.videoRecorder = new VideoRecorder({
            onRecordingStart: (videoSessionId, testSessionId) => {
                this.onVideoRecordingStart(videoSessionId, testSessionId);
            },
            onRecordingStop: (videoSessionId, testSessionId) => {
                this.onVideoRecordingStop(videoSessionId, testSessionId);
            },
            onError: (errorType, error, context) => {
                this.onVideoError(errorType, error, context);
            },
            onChunkUploaded: (chunkNumber, totalUploaded, testSessionId) => {
                this.onVideoChunkUploaded(chunkNumber, totalUploaded, testSessionId);
            }
        });
        
        // Initialize camera
        const cameraInitialized = await this.videoRecorder.initializeCamera();
        if (!cameraInitialized) {
            console.warn('[TestVideoSession] Camera initialization failed, continuing without video');
        }
        
        return cameraInitialized;
    },
    
    /**
     * Load test definition from server
     */
    async loadTestDefinition() {
        try {
            const response = await fetch(`/api/tests/${this.testData.test_id}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.currentTest = data.test;
                this.setupTest();
            } else {
                this.showError('Failed to load test definition');
            }
        } catch (error) {
            console.error('[TestVideoSession] Error loading test:', error);
            this.showError('Failed to load test');
        }
    },
    
    /**
     * Load session from server
     */
    async loadSessionFromServer() {
        try {
            const response = await fetch(`/api/tests/session/${this.sessionId}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.currentQuestionIndex = data.session.current_question;
                await this.loadTestDefinition();
            } else {
                this.showError('Invalid session');
            }
        } catch (error) {
            console.error('[TestVideoSession] Error loading session:', error);
            this.showError('Failed to load session');
        }
    },
    
    /**
     * Set up test interface
     */
    setupTest() {
        // Update UI with test info
        document.getElementById('testTitle').textContent = this.currentTest.title;
        document.getElementById('instructionsText').textContent = 
            this.currentTest.instructions || 'Please answer all questions to the best of your ability.';
        
        // Setup progress
        this.updateProgress();
        
        // Start session timer
        this.startTime = Date.now();
        this.startSessionTimer();
        
        // Log test setup event
        this.logEvent('test_setup', {
            test_id: this.currentTest.test_id,
            total_questions: this.currentTest.questions.length
        });
    },
    
    /**
     * Start the test and video recording
     */
    async startTest() {
        console.log('[TestVideoSession] Starting test and video recording...');
        
        // Log test start event
        this.logEvent('test_start', {
            test_id: this.currentTest.test_id,
            session_id: this.sessionId
        });
        
        // Start video recording with test session link
        if (this.videoRecorder) {
            const recordingStarted = await this.videoRecorder.startRecording(this.sessionId);
            if (!recordingStarted) {
                console.warn('[TestVideoSession] Video recording failed to start, continuing with test only');
            }
        }
        
        // Hide instructions, show first question
        document.getElementById('instructionsCard').style.display = 'none';
        document.getElementById('questionCard').style.display = 'block';
        
        this.showQuestion(0);
    },
    
    /**
     * Show specific question
     */
    showQuestion(index) {
        if (index >= this.currentTest.questions.length) {
            this.completeTest();
            return;
        }
        
        this.currentQuestionIndex = index;
        this.currentAnswer = null;
        this.questionStartTime = Date.now();
        
        const question = this.currentTest.questions[index];
        
        // Log question start event
        this.logEvent('question_start', {
            question_id: question.id,
            question_index: index,
            question_type: question.type
        });
        
        // Update question display
        document.getElementById('questionNumber').textContent = 
            `Question ${index + 1} of ${this.currentTest.questions.length}`;
        document.getElementById('questionText').textContent = question.question;
        document.getElementById('questionDescription').textContent = question.description || '';
        
        // Show/hide skip button
        const skipButton = document.getElementById('skipButton');
        skipButton.style.display = 
            this.currentTest.settings?.allow_skip ? 'block' : 'none';
        
        // Update submit button text
        const submitButton = document.getElementById('submitButton');
        submitButton.textContent = 
            index === this.currentTest.questions.length - 1 ? 'Finish' : 'Next';
        
        // Render answer input based on question type
        this.renderAnswerInput(question);
        
        // Update progress
        this.updateProgress();
        
        // Start question timer if needed
        if (question.time_limit_seconds) {
            this.startQuestionTimer(question.time_limit_seconds);
        }
    },
    
    /**
     * Render answer input based on question type
     */
    renderAnswerInput(question) {
        const container = document.getElementById('answerContainer');
        container.innerHTML = '';
        
        switch (question.type) {
            case 'multiple_choice':
                this.renderMultipleChoice(question, container);
                break;
            case 'true_false':
                this.renderTrueFalse(question, container);
                break;
            case 'text_input':
                this.renderTextInput(question, container);
                break;
            case 'slider':
                this.renderSlider(question, container);
                break;
            case 'rating':
                this.renderRating(question, container);
                break;
            default:
                container.innerHTML = '<p>Unsupported question type</p>';
        }
    },
    
    /**
     * Render multiple choice question
     */
    renderMultipleChoice(question, container) {
        const optionsDiv = document.createElement('div');
        optionsDiv.className = 'answer-options';
        
        question.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.className = 'option-button';
            button.textContent = option.label;
            button.onclick = () => {
                // Log answer selection
                this.logEvent('answer_selected', {
                    question_id: question.id,
                    answer_value: option.value,
                    answer_label: option.label
                });
                
                // Clear previous selection
                optionsDiv.querySelectorAll('.option-button').forEach(btn => 
                    btn.classList.remove('selected'));
                // Select this option
                button.classList.add('selected');
                this.currentAnswer = option.value;
            };
            optionsDiv.appendChild(button);
        });
        
        container.appendChild(optionsDiv);
    },
    
    /**
     * Render true/false question
     */
    renderTrueFalse(question, container) {
        const tfDiv = document.createElement('div');
        tfDiv.className = 'true-false-container';
        
        ['True', 'False'].forEach(value => {
            const button = document.createElement('button');
            button.className = 'true-false-button';
            button.textContent = value;
            button.onclick = () => {
                // Log answer selection
                this.logEvent('answer_selected', {
                    question_id: question.id,
                    answer_value: value.toLowerCase()
                });
                
                tfDiv.querySelectorAll('.true-false-button').forEach(btn => 
                    btn.classList.remove('selected'));
                button.classList.add('selected');
                this.currentAnswer = value.toLowerCase();
            };
            tfDiv.appendChild(button);
        });
        
        container.appendChild(tfDiv);
    },
    
    /**
     * Render text input question
     */
    renderTextInput(question, container) {
        const textarea = document.createElement('textarea');
        textarea.className = 'text-input';
        textarea.placeholder = 'Type your answer here...';
        
        if (question.validation?.max_length) {
            textarea.maxLength = question.validation.max_length;
        }
        
        textarea.oninput = () => {
            this.currentAnswer = textarea.value;
            
            // Log text input changes (debounced)
            clearTimeout(this.textInputTimeout);
            this.textInputTimeout = setTimeout(() => {
                this.logEvent('text_input_change', {
                    question_id: question.id,
                    text_length: textarea.value.length
                });
            }, 1000);
        };
        
        container.appendChild(textarea);
    },
    
    /**
     * Render slider question
     */
    renderSlider(question, container) {
        const sliderDiv = document.createElement('div');
        sliderDiv.className = 'slider-container';
        
        const min = question.validation?.min_value || 0;
        const max = question.validation?.max_value || 10;
        const step = question.validation?.step || 1;
        const defaultValue = (min + max) / 2;
        
        // Labels
        const labelsDiv = document.createElement('div');
        labelsDiv.className = 'slider-labels';
        labelsDiv.innerHTML = `<span>${min}</span><span>${max}</span>`;
        sliderDiv.appendChild(labelsDiv);
        
        // Slider
        const slider = document.createElement('input');
        slider.type = 'range';
        slider.className = 'slider';
        slider.min = min;
        slider.max = max;
        slider.step = step;
        slider.value = defaultValue;
        
        // Value display
        const valueDiv = document.createElement('div');
        valueDiv.className = 'slider-value';
        valueDiv.textContent = defaultValue;
        
        slider.oninput = () => {
            valueDiv.textContent = slider.value;
            this.currentAnswer = parseFloat(slider.value);
            
            // Log slider change
            this.logEvent('slider_change', {
                question_id: question.id,
                value: this.currentAnswer
            });
        };
        
        sliderDiv.appendChild(slider);
        sliderDiv.appendChild(valueDiv);
        container.appendChild(sliderDiv);
        
        // Set initial answer
        this.currentAnswer = defaultValue;
    },
    
    /**
     * Render rating question
     */
    renderRating(question, container) {
        const ratingDiv = document.createElement('div');
        ratingDiv.className = 'rating-container';
        
        const min = question.validation?.min_value || 1;
        const max = question.validation?.max_value || 5;
        
        // Add option labels if provided
        if (question.options && question.options.length > 0) {
            const labelContainer = document.createElement('div');
            labelContainer.style.width = '100%';
            labelContainer.style.marginBottom = '1rem';
            
            question.options.forEach(option => {
                const label = document.createElement('div');
                label.style.textAlign = 'center';
                label.style.marginBottom = '0.5rem';
                label.innerHTML = `<strong>${option.value}:</strong> ${option.label}`;
                labelContainer.appendChild(label);
            });
            
            container.appendChild(labelContainer);
        }
        
        for (let i = min; i <= max; i++) {
            const button = document.createElement('button');
            button.className = 'rating-button';
            button.textContent = i;
            button.onclick = () => {
                // Log rating selection
                this.logEvent('rating_selected', {
                    question_id: question.id,
                    rating: i
                });
                
                ratingDiv.querySelectorAll('.rating-button').forEach(btn => 
                    btn.classList.remove('selected'));
                button.classList.add('selected');
                this.currentAnswer = i;
            };
            ratingDiv.appendChild(button);
        }
        
        container.appendChild(ratingDiv);
    },
    
    /**
     * Submit current answer
     */
    async submitAnswer() {
        if (this.currentAnswer === null && 
            this.currentTest.questions[this.currentQuestionIndex].required !== false) {
            alert('Please provide an answer before continuing.');
            return;
        }
        
        const timeTaken = (Date.now() - this.questionStartTime) / 1000;
        const question = this.currentTest.questions[this.currentQuestionIndex];
        
        // Log answer submission
        this.logEvent('answer_submitted', {
            question_id: question.id,
            question_index: this.currentQuestionIndex,
            answer: this.currentAnswer,
            time_taken: timeTaken
        });
        
        try {
            const response = await fetch(`/api/tests/session/${this.sessionId}/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question_id: question.id,
                    answer: this.currentAnswer,
                    time_taken: timeTaken,
                    video_session_id: this.videoSessionId,
                    events: this.getRecentEvents()
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                if (data.is_complete) {
                    this.completeTest();
                } else {
                    this.showQuestion(this.currentQuestionIndex + 1);
                }
            } else {
                this.showError('Failed to submit answer');
            }
        } catch (error) {
            console.error('[TestVideoSession] Error submitting answer:', error);
            this.showError('Failed to submit answer');
        }
    },
    
    /**
     * Skip current question
     */
    skipQuestion() {
        if (confirm('Are you sure you want to skip this question?')) {
            // Log question skip
            this.logEvent('question_skipped', {
                question_id: this.currentTest.questions[this.currentQuestionIndex].id,
                question_index: this.currentQuestionIndex
            });
            
            this.currentAnswer = null;
            this.submitAnswer();
        }
    },
    
    /**
     * Complete the test
     */
    async completeTest() {
        console.log('[TestVideoSession] Completing test...');
        
        // Log test completion
        this.logEvent('test_complete', {
            test_id: this.currentTest.test_id,
            total_time: (Date.now() - this.startTime) / 1000
        });
        
        // Stop video recording
        if (this.videoRecorder && this.videoRecorder.isRecording) {
            this.videoRecorder.stopRecording();
        }
        
        // Stop timers
        if (this.sessionTimer) clearInterval(this.sessionTimer);
        if (this.questionTimer) clearInterval(this.questionTimer);
        
        // Hide question card, show results
        document.getElementById('questionCard').style.display = 'none';
        document.getElementById('resultsCard').style.display = 'block';
        
        // Load results
        try {
            const response = await fetch(`/api/tests/session/${this.sessionId}/results`);
            const data = await response.json();
            
            if (data.status === 'success') {
                const results = data.results;
                const duration = Math.floor(results.duration_seconds / 60);
                
                document.getElementById('resultsMessage').textContent = 
                    `You completed ${results.questions_answered} out of ${results.total_questions} questions in ${duration} minutes.`;
                
                // Store results for detailed view
                sessionStorage.setItem('test_results', JSON.stringify(results));
            }
        } catch (error) {
            console.error('[TestVideoSession] Error loading results:', error);
        }
    },
    
    /**
     * View detailed results
     */
    viewDetailedResults() {
        window.location.href = `/tests/results?session=${this.sessionId}&video=${this.videoSessionId}`;
    },
    
    /**
     * Update progress bar
     */
    updateProgress() {
        const progress = (this.currentQuestionIndex / this.currentTest.questions.length) * 100;
        document.getElementById('progressFill').style.width = `${progress}%`;
        document.getElementById('progressText').textContent = 
            `${this.currentQuestionIndex} / ${this.currentTest.questions.length}`;
    },
    
    /**
     * Start session timer
     */
    startSessionTimer() {
        this.sessionTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            document.getElementById('sessionTimer').textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    },
    
    /**
     * Start question timer
     */
    startQuestionTimer(seconds) {
        if (this.questionTimer) clearInterval(this.questionTimer);
        
        let remaining = seconds;
        const timerElement = document.getElementById('questionTimer');
        
        const updateTimer = () => {
            if (remaining <= 0) {
                clearInterval(this.questionTimer);
                timerElement.textContent = 'Time\'s up!';
                this.submitAnswer();
            } else {
                timerElement.textContent = `${remaining}s remaining`;
                remaining--;
            }
        };
        
        updateTimer();
        this.questionTimer = setInterval(updateTimer, 1000);
    },
    
    /**
     * Log event for correlation with video
     */
    logEvent(eventType, data = {}) {
        const event = {
            type: eventType,
            timestamp: Date.now(),
            data: data,
            video_session_id: this.videoSessionId
        };
        
        this.events.push(event);
        console.log(`[TestVideoSession] Event logged:`, event);
        
        // Keep only recent events (last 100)
        if (this.events.length > 100) {
            this.events = this.events.slice(-100);
        }
    },
    
    /**
     * Get recent events for submission
     */
    getRecentEvents() {
        // Return events from the last minute
        const oneMinuteAgo = Date.now() - 60000;
        return this.events.filter(event => event.timestamp > oneMinuteAgo);
    },
    
    /**
     * Video recording event handlers
     */
    onVideoRecordingStart(videoSessionId, testSessionId) {
        this.videoSessionId = videoSessionId;
        console.log(`[TestVideoSession] Video recording started: ${videoSessionId}`);
        
        this.logEvent('video_recording_start', {
            video_session_id: videoSessionId,
            test_session_id: testSessionId
        });
    },
    
    onVideoRecordingStop(videoSessionId, testSessionId) {
        console.log(`[TestVideoSession] Video recording stopped: ${videoSessionId}`);
        
        this.logEvent('video_recording_stop', {
            video_session_id: videoSessionId,
            test_session_id: testSessionId
        });
    },
    
    onVideoError(errorType, error, context) {
        console.error(`[TestVideoSession] Video error (${errorType}):`, error);
        
        this.logEvent('video_error', {
            error_type: errorType,
            error_message: error.message || error.toString(),
            context: context
        });
    },
    
    onVideoChunkUploaded(chunkNumber, totalUploaded, testSessionId) {
        console.log(`[TestVideoSession] Video chunk ${chunkNumber} uploaded (${totalUploaded} total)`);
        
        this.logEvent('video_chunk_uploaded', {
            chunk_number: chunkNumber,
            total_uploaded: totalUploaded,
            test_session_id: testSessionId
        });
    },
    
    /**
     * Manual video recording controls (for buttons)
     */
    async startVideoRecording() {
        if (this.videoRecorder) {
            return await this.videoRecorder.startRecording(this.sessionId);
        }
        return false;
    },
    
    stopVideoRecording() {
        if (this.videoRecorder) {
            this.videoRecorder.stopRecording();
        }
    },
    
    /**
     * Show error message
     */
    showError(message) {
        const errorDiv = document.getElementById('errorDisplay');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        console.error(`[TestVideoSession] Error: ${message}`);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    TestVideoSession.init();
});

// Make available globally
window.TestVideoSession = TestVideoSession;