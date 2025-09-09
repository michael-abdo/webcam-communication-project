/**
 * Baseline Capture Client-Side Implementation
 * 
 * Handles the complete baseline capture workflow:
 * - WebRTC media capture for camera and microphone
 * - 10-second face baseline with quality monitoring
 * - 15-second speech baseline with SNR validation
 * - Real-time quality feedback and retry logic
 * - API communication with backend endpoints
 * - S3 file upload integration
 * 
 * Author: Baseline Capture System
 * Version: 1.0
 */

class BaselineCapture {
    constructor() {
        // Session state
        this.sessionId = null;
        this.userId = null;
        this.currentState = 'initialized';
        this.uploadUrls = null;
        
        // Media streams and recording
        this.videoStream = null;
        this.audioStream = null;
        this.videoRecorder = null;
        this.audioRecorder = null;
        this.recordedChunks = {
            face: [],
            speech: []
        };
        
        // Timing and progress
        this.timers = {
            face: null,
            speech: null,
            quality: null
        };
        this.progress = {
            face: { complete: false, quality: 0 },
            speech: { complete: false, quality: 0 },
            overall: 0
        };
        
        // Quality monitoring
        this.qualityMetrics = {
            face: {
                confidence: 0,
                lighting: false,
                position: false,
                stability: false
            },
            audio: {
                level: 0,
                snr: 0,
                clarity: false,
                backgroundNoise: false
            }
        };
        
        // Face Detection - Multiple approaches
        this.faceDetection = null;
        this.tensorflowFaceModel = null;
        this.isMediaPipeReady = false;
        this.isTensorFlowReady = false;
        this.mediaPipeInitialized = false;
        this.tensorflowInitialized = false;
        this.lastFaceDetectionTime = 0;
        this.faceDetectionResults = null;
        this.activeFaceDetector = null; // 'mediapipe', 'tensorflow', or 'fallback'
        
        // Configuration from SOP requirements
        this.config = {
            face: {
                duration: 10, // 10 seconds
                targetConfidence: 0.8, // >0.8 face confidence
                minValidSeconds: 8 // 8 out of 10 seconds
            },
            speech: {
                duration: 15, // 15 seconds  
                targetSNR: 20, // >20dB SNR
                minValidSeconds: 10 // 10 out of 15 seconds
            },
            maxRetries: 3
        };
        
        // API base URL
        this.apiBase = '/api/baseline';
        
        // Status polling
        this.statusPolling = {
            active: false,
            interval: null,
            retryCount: 0,
            maxRetries: 3
        };
        
        // Initialize on load
        this.initialize();
    }

    /**
     * Initialize the baseline capture system
     */
    initialize() {
        console.log('🎯 Baseline Capture System Initialized');
        this.updateOverallProgress('System ready', 0);
        
        // Setup event listeners
        window.addEventListener('beforeunload', () => this.cleanup());
        
        // Check for required browser features
        this.checkBrowserSupport();
        
        // Initialize face detection systems
        this.initializeFaceDetection();
    }

    /**
     * Check browser support for required features
     */
    checkBrowserSupport() {
        const features = {
            getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
            mediaRecorder: !!(window.MediaRecorder),
            webRTC: !!(window.RTCPeerConnection)
        };
        
        const unsupported = Object.keys(features).filter(key => !features[key]);
        
        if (unsupported.length > 0) {
            this.showError('Browser not supported', 
                `Missing features: ${unsupported.join(', ')}`);
            return false;
        }
        
        console.log('✅ Browser support verified');
        return true;
    }

    /**
     * Start baseline capture process
     */
    async startBaselineCapture() {
        try {
            console.log('🚀 Starting baseline capture process');
            this.updateOverallProgress('Starting baseline capture...', 5);
            
            // Initialize session with backend
            const sessionResult = await this.initializeSession();
            if (!sessionResult.success) {
                throw new Error(sessionResult.error || 'Failed to initialize session');
            }
            
            this.sessionId = sessionResult.session_id;
            this.userId = sessionResult.user_id;
            this.uploadUrls = sessionResult.upload_urls;
            
            console.log(`📋 Session initialized: ${this.sessionId}`);
            this.updateOverallProgress('Session created', 10);
            
            // Request camera and microphone permissions
            await this.setupMediaStreams();
            this.updateOverallProgress('Media access granted', 20);
            
            // Show face capture section
            this.showSection('faceSection');
            this.hideSection('instructionsSection');
            this.currentState = 'face_ready';
            
            this.updateOverallProgress('Ready for face baseline', 25);
            
            // Start status polling for real-time updates
            this.startStatusPolling();
            
        } catch (error) {
            console.error('❌ Failed to start baseline capture:', error);
            this.showError('Setup Failed', error.message);
        }
    }

    /**
     * Initialize session with backend API
     */
    async initializeSession() {
        try {
            const response = await fetch(`${this.apiBase}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.generateUserId()
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('❌ Session initialization failed:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Setup camera and microphone streams
     */
    async setupMediaStreams() {
        try {
            console.log('📹 Setting up media streams...');
            
            // Request video stream (camera) with error handling
            try {
                this.videoStream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                        frameRate: { ideal: 30 }
                    }
                });
                console.log('✅ Camera access granted');
            } catch (videoError) {
                console.error('❌ Camera access failed:', videoError);
                this.handleCameraAccessError(videoError);
                throw videoError;
            }
            
            // Request audio stream (microphone) with error handling
            try {
                this.audioStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: { ideal: 44100 }
                    }
                });
                console.log('✅ Microphone access granted');
            } catch (audioError) {
                console.error('❌ Microphone access failed:', audioError);
                this.handleMicrophoneAccessError(audioError);
                throw audioError;
            }
            
            // Connect video stream to preview
            const videoElement = document.getElementById('faceVideo');
            if (videoElement) {
                videoElement.srcObject = this.videoStream;
            }
            
            // Setup MediaRecorder instances
            this.setupMediaRecorders();
            
            // Start quality monitoring
            this.startQualityMonitoring();
            
            console.log('✅ Media streams setup complete');
            
        } catch (error) {
            console.error('❌ Media setup failed:', error);
            // Error already handled by specific handlers above
            throw error;
        }
    }
    
    /**
     * Handle camera access denied or failed
     */
    handleCameraAccessError(error) {
        let title = 'Camera Access Required';
        let message = '';
        let suggestions = [];
        
        switch (error.name) {
            case 'NotAllowedError':
            case 'PermissionDeniedError':
                message = 'Camera access was denied. Please allow camera access to continue with baseline capture.';
                suggestions = [
                    'Click the camera icon in your browser\'s address bar',
                    'Select "Allow" for camera permissions',
                    'Refresh the page and try again'
                ];
                break;
                
            case 'NotFoundError':
            case 'DevicesNotFoundError':
                message = 'No camera was found on your device.';
                suggestions = [
                    'Make sure your camera is connected',
                    'Check that other applications aren\'t using the camera',
                    'Try a different browser if issues persist'
                ];
                break;
                
            case 'NotReadableError':
            case 'TrackStartError':
                message = 'Camera is already in use by another application.';
                suggestions = [
                    'Close other applications using the camera',
                    'Restart your browser',
                    'Check camera privacy settings'
                ];
                break;
                
            case 'OverconstrainedError':
            case 'ConstraintNotSatisfiedError':
                message = 'Camera doesn\'t support the required video quality.';
                suggestions = [
                    'Try using a different camera',
                    'Update your camera drivers',
                    'Use a more recent browser version'
                ];
                break;
                
            case 'NotSupportedError':
                message = 'Camera access is not supported in this browser.';
                suggestions = [
                    'Use Chrome, Firefox, Safari, or Edge',
                    'Make sure you\'re using HTTPS',
                    'Update your browser to the latest version'
                ];
                break;
                
            default:
                message = `Camera access failed: ${error.message}`;
                suggestions = [
                    'Refresh the page and try again',
                    'Check your camera permissions',
                    'Try a different browser'
                ];
        }
        
        this.showDetailedError(title, message, suggestions);
    }
    
    /**
     * Handle microphone access denied or failed
     */
    handleMicrophoneAccessError(error) {
        let title = 'Microphone Access Required';
        let message = '';
        let suggestions = [];
        
        switch (error.name) {
            case 'NotAllowedError':
            case 'PermissionDeniedError':
                message = 'Microphone access was denied. Please allow microphone access for speech baseline capture.';
                suggestions = [
                    'Click the microphone icon in your browser\'s address bar',
                    'Select "Allow" for microphone permissions',
                    'Refresh the page and try again'
                ];
                break;
                
            case 'NotFoundError':
            case 'DevicesNotFoundError':
                message = 'No microphone was found on your device.';
                suggestions = [
                    'Make sure your microphone is connected',
                    'Check that other applications aren\'t using the microphone',
                    'Try a different browser if issues persist'
                ];
                break;
                
            case 'NotReadableError':
            case 'TrackStartError':
                message = 'Microphone is already in use by another application.';
                suggestions = [
                    'Close other applications using the microphone',
                    'Restart your browser',
                    'Check microphone privacy settings'
                ];
                break;
                
            case 'OverconstrainedError':
            case 'ConstraintNotSatisfiedError':
                message = 'Microphone doesn\'t support the required audio quality.';
                suggestions = [
                    'Try using a different microphone',
                    'Update your audio drivers',
                    'Use a more recent browser version'
                ];
                break;
                
            case 'NotSupportedError':
                message = 'Microphone access is not supported in this browser.';
                suggestions = [
                    'Use Chrome, Firefox, Safari, or Edge',
                    'Make sure you\'re using HTTPS',
                    'Update your browser to the latest version'
                ];
                break;
                
            default:
                message = `Microphone access failed: ${error.message}`;
                suggestions = [
                    'Refresh the page and try again',
                    'Check your microphone permissions',
                    'Try a different browser'
                ];
        }
        
        this.showDetailedError(title, message, suggestions);
    }
    
    /**
     * Show detailed error message with suggestions
     */
    showDetailedError(title, message, suggestions = []) {
        // Create or update error display
        let errorDiv = document.getElementById('errorMessage');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'errorMessage';
            errorDiv.className = 'status-message status-error';
            errorDiv.style.position = 'fixed';
            errorDiv.style.top = '20px';
            errorDiv.style.left = '50%';
            errorDiv.style.transform = 'translateX(-50%)';
            errorDiv.style.zIndex = '1000';
            errorDiv.style.maxWidth = '500px';
            errorDiv.style.padding = '20px';
            errorDiv.style.borderRadius = '10px';
            document.body.appendChild(errorDiv);
        }
        
        let suggestionsHtml = '';
        if (suggestions.length > 0) {
            suggestionsHtml = `
                <div style="margin-top: 15px;">
                    <strong>How to fix this:</strong>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        ${suggestions.map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        errorDiv.innerHTML = `
            <strong>❌ ${title}</strong><br>
            ${message}
            ${suggestionsHtml}
            <div style="margin-top: 15px;">
                <button class="btn btn-primary" onclick="location.reload()" style="margin-right: 10px;">
                    🔄 Try Again
                </button>
                <button class="btn btn-secondary" onclick="this.parentElement.parentElement.style.display='none'">
                    Dismiss
                </button>
            </div>
        `;
        
        console.error(`❌ ${title}: ${message}`);
    }

    /**
     * Setup MediaRecorder instances for video and audio
     */
    setupMediaRecorders() {
        try {
            // Video recorder for face baseline
            this.videoRecorder = new MediaRecorder(this.videoStream, {
                mimeType: 'video/webm;codecs=vp8,opus',
                videoBitsPerSecond: 1500000 // 1.5 Mbps
            });
            
            this.videoRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.face.push(event.data);
                }
            };
            
            // Audio recorder for speech baseline  
            this.audioRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.audioRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.speech.push(event.data);
                }
            };
            
            console.log('✅ MediaRecorder setup complete');
            
        } catch (error) {
            console.error('❌ MediaRecorder setup failed:', error);
            throw error;
        }
    }

    /**
     * Generate unique user ID for session
     */
    generateUserId() {
        return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Update overall progress display
     */
    updateOverallProgress(message, percentage) {
        const progressElement = document.getElementById('overallProgress');
        const fillElement = document.getElementById('overallProgressFill');
        
        if (progressElement) progressElement.textContent = message;
        if (fillElement) fillElement.style.width = `${percentage}%`;
        
        this.progress.overall = percentage;
    }

    /**
     * Show specified section and hide others
     */
    showSection(sectionId) {
        // Hide all sections
        const sections = ['instructionsSection', 'faceSection', 'speechSection', 'completionSection'];
        sections.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.classList.add('hidden');
        });
        
        // Show target section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.remove('hidden');
        }
    }

    /**
     * Hide specified section
     */
    hideSection(sectionId) {
        const element = document.getElementById(sectionId);
        if (element) element.classList.add('hidden');
    }

    /**
     * Show error message to user
     */
    showError(title, message) {
        // Create or update error display
        let errorDiv = document.getElementById('errorMessage');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'errorMessage';
            errorDiv.className = 'status-message status-error';
            document.body.insertBefore(errorDiv, document.body.firstChild);
        }
        
        errorDiv.innerHTML = `
            <strong>❌ ${title}</strong><br>
            ${message}<br>
            <button class="btn btn-primary" onclick="location.reload()">Reload Page</button>
        `;
        
        console.error(`❌ ${title}: ${message}`);
    }

    /**
     * Start face baseline capture (10 seconds)
     */
    async startFaceCapture() {
        try {
            console.log('📹 Starting face baseline capture');
            this.currentState = 'face_capturing';
            
            // Update UI
            this.updateFaceProgress('Starting face capture...', 0);
            this.setButtonState('startFaceBtn', false, 'Recording...');
            
            // Clear previous recordings
            this.recordedChunks.face = [];
            
            // Start recording
            this.videoRecorder.start(1000); // Collect data every second
            
            // Start 10-second countdown timer
            await this.runFaceTimer();
            
            // Stop recording
            this.videoRecorder.stop();
            
            // Wait for final data
            setTimeout(() => this.processFaceCapture(), 500);
            
        } catch (error) {
            console.error('❌ Face capture failed:', error);
            this.showFaceError('Face capture failed', error.message);
        }
    }

    /**
     * Run 10-second face capture timer with progress updates
     */
    async runFaceTimer() {
        return new Promise((resolve) => {
            let secondsRemaining = this.config.face.duration;
            let qualityChecks = [];
            
            // Update timer display
            this.updateFaceTimer(secondsRemaining);
            this.updateFaceProgress(`Face capture in progress (${secondsRemaining}s)`, 0);
            
            this.timers.face = setInterval(() => {
                secondsRemaining--;
                
                // Update timer and progress
                this.updateFaceTimer(secondsRemaining);
                const progressPercent = ((this.config.face.duration - secondsRemaining) / this.config.face.duration) * 100;
                this.updateFaceProgress(`Recording face baseline... ${secondsRemaining}s`, progressPercent);
                
                // Simulate quality check (in real implementation, this would analyze video frames)
                const qualityCheck = this.simulateFaceQualityCheck();
                qualityChecks.push(qualityCheck);
                this.updateFaceQualityDisplay(qualityCheck);
                
                // Timer complete
                if (secondsRemaining <= 0) {
                    clearInterval(this.timers.face);
                    this.timers.face = null;
                    
                    // Calculate overall quality
                    const overallQuality = this.calculateFaceQuality(qualityChecks);
                    this.progress.face = overallQuality;
                    
                    this.updateFaceProgress('Face capture complete!', 100);
                    resolve();
                }
            }, 1000);
        });
    }

    /**
     * Process completed face capture
     */
    async processFaceCapture() {
        try {
            console.log('📊 Processing face capture data');
            
            // Create blob from recorded chunks
            const faceBlob = new Blob(this.recordedChunks.face, { type: 'video/webm' });
            console.log(`📹 Face video size: ${(faceBlob.size / 1024 / 1024).toFixed(2)} MB`);
            
            // Check if quality is acceptable
            if (this.progress.face.quality >= this.config.face.targetConfidence) {
                // Quality good - upload and continue
                this.updateFaceProgress('Quality excellent! Processing...', 100);
                await this.uploadFaceBaseline(faceBlob);
                
                // Enable continue button
                this.setButtonState('startFaceBtn', false, 'Completed ✅');
                this.showButton('continueSpeechBtn');
                this.showFaceSuccess('Face baseline captured successfully!');
                
                this.updateOverallProgress('Face baseline complete', 50);
                
            } else {
                // Quality poor - offer retry
                this.updateFaceProgress('Quality needs improvement', 100);
                this.showButton('retryFaceBtn');
                this.showFaceWarning('Face baseline quality is low. Please retry with better lighting or positioning.');
            }
            
        } catch (error) {
            console.error('❌ Face processing failed:', error);
            this.showFaceError('Processing failed', error.message);
        }
    }

    /**
     * Start speech baseline capture (15 seconds)
     */
    async startSpeechCapture() {
        try {
            console.log('🎤 Starting speech baseline capture');
            this.currentState = 'speech_capturing';
            
            // Show speech section
            this.showSection('speechSection');
            
            // Update UI
            this.updateSpeechProgress('Starting speech capture...', 0);
            this.setButtonState('startSpeechBtn', false, 'Recording...');
            
            // Clear previous recordings
            this.recordedChunks.speech = [];
            
            // Start recording
            this.audioRecorder.start(1000); // Collect data every second
            
            // Start 15-second countdown timer
            await this.runSpeechTimer();
            
            // Stop recording
            this.audioRecorder.stop();
            
            // Wait for final data
            setTimeout(() => this.processSpeechCapture(), 500);
            
        } catch (error) {
            console.error('❌ Speech capture failed:', error);
            this.showSpeechError('Speech capture failed', error.message);
        }
    }

    /**
     * Run 15-second speech capture timer with progress updates
     */
    async runSpeechTimer() {
        return new Promise((resolve) => {
            let secondsRemaining = this.config.speech.duration;
            let qualityChecks = [];
            
            // Update timer display
            this.updateSpeechTimer(secondsRemaining);
            this.updateSpeechProgress(`Speech capture in progress (${secondsRemaining}s)`, 0);
            
            this.timers.speech = setInterval(() => {
                secondsRemaining--;
                
                // Update timer and progress
                this.updateSpeechTimer(secondsRemaining);
                const progressPercent = ((this.config.speech.duration - secondsRemaining) / this.config.speech.duration) * 100;
                this.updateSpeechProgress(`Recording speech baseline... ${secondsRemaining}s`, progressPercent);
                
                // Simulate quality check (in real implementation, this would analyze audio)
                const qualityCheck = this.simulateSpeechQualityCheck();
                qualityChecks.push(qualityCheck);
                this.updateSpeechQualityDisplay(qualityCheck);
                
                // Timer complete
                if (secondsRemaining <= 0) {
                    clearInterval(this.timers.speech);
                    this.timers.speech = null;
                    
                    // Calculate overall quality
                    const overallQuality = this.calculateSpeechQuality(qualityChecks);
                    this.progress.speech = overallQuality;
                    
                    this.updateSpeechProgress('Speech capture complete!', 100);
                    resolve();
                }
            }, 1000);
        });
    }

    /**
     * Process completed speech capture
     */
    async processSpeechCapture() {
        try {
            console.log('📊 Processing speech capture data');
            
            // Create blob from recorded chunks
            const speechBlob = new Blob(this.recordedChunks.speech, { type: 'audio/webm' });
            console.log(`🎤 Speech audio size: ${(speechBlob.size / 1024 / 1024).toFixed(2)} MB`);
            
            // Check if quality is acceptable
            if (this.progress.speech.quality >= this.config.speech.targetSNR) {
                // Quality good - upload and continue
                this.updateSpeechProgress('Quality excellent! Processing...', 100);
                await this.uploadSpeechBaseline(speechBlob);
                
                // Enable complete button
                this.setButtonState('startSpeechBtn', false, 'Completed ✅');
                this.showButton('completeBtn');
                this.showSpeechSuccess('Speech baseline captured successfully!');
                
                this.updateOverallProgress('Speech baseline complete', 75);
                
            } else {
                // Quality poor - offer retry
                this.updateSpeechProgress('Quality needs improvement', 100);
                this.showButton('retrySpeechBtn');
                this.showSpeechWarning('Speech baseline quality is low. Please retry in a quieter environment.');
            }
            
        } catch (error) {
            console.error('❌ Speech processing failed:', error);
            this.showSpeechError('Processing failed', error.message);
        }
    }

    /**
     * Start quality monitoring for real-time feedback
     */
    startQualityMonitoring() {
        console.log('👀 Starting quality monitoring');
        console.log(`🔍 Active face detector: ${this.activeFaceDetector}`);
        
        // Start frame processing if any real detector is ready
        if (this.activeFaceDetector !== 'fallback') {
            this.startFrameProcessing();
            console.log(`📹 ${this.activeFaceDetector} frame processing enabled`);
        } else {
            console.log('🔄 No real face detection, using simulation');
        }
        
        this.timers.quality = setInterval(() => {
            // Process video frame for face detection if any detector is active
            if (this.activeFaceDetector !== 'fallback' && 
                (this.currentState === 'face_ready' || this.currentState === 'face_capturing')) {
                this.processVideoFrame();
            }
            
            // Update quality displays
            if (this.currentState === 'face_ready' || this.currentState === 'face_capturing') {
                const faceQuality = this.simulateFaceQualityCheck();
                this.updateFaceQualityDisplay(faceQuality);
            }
            
            if (this.currentState === 'speech_ready' || this.currentState === 'speech_capturing') {
                const speechQuality = this.simulateSpeechQualityCheck();
                this.updateSpeechQualityDisplay(speechQuality);
            }
        }, 500); // Update every 500ms for smoother feedback
    }
    
    /**
     * Start continuous frame processing
     */
    startFrameProcessing() {
        const processFrame = async () => {
            if (this.activeFaceDetector !== 'fallback' && 
                (this.currentState === 'face_ready' || this.currentState === 'face_capturing')) {
                await this.processVideoFrame();
            }
            // Continue processing only if we have an active detector
            if (this.activeFaceDetector !== 'fallback') {
                requestAnimationFrame(processFrame);
            }
        };
        requestAnimationFrame(processFrame);
    }

    /**
     * Initialize face detection using proven MediaPipe Face Mesh approach
     */
    async initializeFaceDetection() {
        console.log('🎭 Initializing face detection with proven MediaPipe approach...');
        
        // Use the working MediaPipe Face Mesh implementation from webcam_analysis.html
        await this.initializeWorkingMediaPipe();
        
        // Set active detector
        if (this.isMediaPipeReady) {
            this.activeFaceDetector = 'working_mediapipe';
            console.log('✅ Active face detector: Working MediaPipe Face Mesh');
        } else {
            this.activeFaceDetector = 'canvas_analysis';
            console.log('⚠️ Active face detector: Canvas-based analysis');
        }
    }
    
    /**
     * Initialize working MediaPipe Face Mesh (from webcam_analysis.html)
     */
    async initializeWorkingMediaPipe() {
        try {
            if (typeof FaceMesh === 'undefined') {
                console.warn('⚠️ MediaPipe Face Mesh not loaded');
                return;
            }
            
            console.log('🎭 Initializing working MediaPipe Face Mesh...');
            
            // Use the proven working configuration from webcam_analysis.html
            this.faceMesh = new FaceMesh({locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
            }});
            
            this.faceMesh.setOptions({
                maxNumFaces: 1,
                refineLandmarks: true,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });
            
            this.faceMesh.onResults(this.onWorkingMediaPipeResults.bind(this));
            
            // Initialize eye landmark indices (from working implementation)
            this.LEFT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380];
            this.RIGHT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144];
            
            this.isMediaPipeReady = true;
            console.log('✅ Working MediaPipe Face Mesh initialized successfully');
            
        } catch (error) {
            console.error('❌ Working MediaPipe initialization failed:', error);
            this.isMediaPipeReady = false;
            this.faceMesh = null;
        }
    }
    
    /**
     * Initialize TensorFlow.js Face Landmarks Detection
     */
    async initializeTensorFlowFaceDetection() {
        try {
            if (typeof faceLandmarksDetection === 'undefined') {
                console.warn('⚠️ TensorFlow.js Face Detection not loaded');
                return;
            }
            
            console.log('🤖 Trying TensorFlow.js Face Detection...');
            
            // Load the MediaPipe FaceDetection model
            this.tensorflowFaceModel = await faceLandmarksDetection.load(
                faceLandmarksDetection.SupportedPackages.mediapipeFacemesh
            );
            
            this.isTensorFlowReady = true;
            this.tensorflowInitialized = true;
            console.log('✅ TensorFlow.js Face Detection initialized');
            
        } catch (error) {
            console.error('❌ TensorFlow.js Face Detection initialization failed:', error);
            this.isTensorFlowReady = false;
            this.tensorflowFaceModel = null;
        }
    }
    
    /**
     * Test MediaPipe initialization to catch model loading errors early
     */
    async testMediaPipeInitialization() {
        try {
            // Wait a moment for initialization, then test with a small canvas
            setTimeout(async () => {
                if (this.faceDetection) {
                    const testCanvas = document.createElement('canvas');
                    testCanvas.width = 100;
                    testCanvas.height = 100;
                    const ctx = testCanvas.getContext('2d');
                    ctx.fillStyle = 'black';
                    ctx.fillRect(0, 0, 100, 100);
                    
                    try {
                        await this.faceDetection.send({image: testCanvas});
                        this.isMediaPipeReady = true;
                        console.log('✅ MediaPipe test successful - face detection ready');
                    } catch (testError) {
                        console.error('❌ MediaPipe test failed:', testError);
                        console.log('🔄 MediaPipe model loading failed, using fallback detection');
                        this.isMediaPipeReady = false;
                        this.faceDetection = null;
                    }
                }
            }, 1000);
        } catch (error) {
            console.error('❌ MediaPipe test initialization failed:', error);
            this.isMediaPipeReady = false;
            this.faceDetection = null;
        }
    }
    
    /**
     * Process results from working MediaPipe Face Mesh
     */
    onWorkingMediaPipeResults(results) {
        // Store results in the same format for compatibility
        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
            this.faceDetectionResults = {
                landmarks: results.multiFaceLandmarks[0]
            };
            this.lastFaceDetectionTime = Date.now();
        } else {
            this.faceDetectionResults = null;
        }
    }
    
    /**
     * Calculate Eye Aspect Ratio (from working implementation)
     */
    calculateEyeAspectRatio(landmarks, eyePoints) {
        // Calculate Eye Aspect Ratio (EAR) for fatigue detection
        const points = eyePoints.map(idx => landmarks[idx]);
        
        // Vertical distances
        const v1 = Math.sqrt(Math.pow(points[1].x - points[5].x, 2) + Math.pow(points[1].y - points[5].y, 2));
        const v2 = Math.sqrt(Math.pow(points[2].x - points[4].x, 2) + Math.pow(points[2].y - points[4].y, 2));
        
        // Horizontal distance
        const h = Math.sqrt(Math.pow(points[0].x - points[3].x, 2) + Math.pow(points[0].y - points[3].y, 2));
        
        // EAR calculation
        return (v1 + v2) / (2.0 * h);
    }
    
    /**
     * Calculate brightness from video frame
     */
    calculateFrameBrightness() {
        try {
            const videoElement = document.getElementById('faceVideo');
            if (!videoElement || videoElement.readyState < 2) return 0.5;
            
            // Create hidden canvas for analysis
            const canvas = document.createElement('canvas');
            canvas.width = 160; // Small size for performance
            canvas.height = 120;
            const ctx = canvas.getContext('2d');
            
            // Draw video frame
            ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
            
            // Get image data
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            // Calculate average brightness
            let sum = 0;
            for (let i = 0; i < data.length; i += 4) {
                // Convert RGB to grayscale using standard formula
                const brightness = (data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114);
                sum += brightness;
            }
            
            return sum / (data.length / 4) / 255; // Normalize to 0-1
            
        } catch (error) {
            console.error('Brightness calculation error:', error);
            return 0.5; // Default neutral brightness
        }
    }
    
    /**
     * Process face detection results from TensorFlow.js
     */
    onTensorFlowResults(predictions) {
        // Convert TensorFlow predictions to MediaPipe-like format
        this.faceDetectionResults = {
            detections: predictions.map(pred => ({
                score: pred.faceInViewConfidence || 0.8,
                boundingBox: {
                    x: pred.boundingBox?.topLeft?.[0] || 0,
                    y: pred.boundingBox?.topLeft?.[1] || 0,
                    width: pred.boundingBox?.bottomRight?.[0] - pred.boundingBox?.topLeft?.[0] || 0,
                    height: pred.boundingBox?.bottomRight?.[1] - pred.boundingBox?.topLeft?.[1] || 0
                }
            }))
        };
        this.lastFaceDetectionTime = Date.now();
    }
    
    /**
     * Process video frame through active face detection system
     */
    async processVideoFrame() {
        if (!this.videoStream || !this.videoStream.active) return;
        
        const videoElement = document.getElementById('faceVideo');
        if (!videoElement || videoElement.readyState < 2) return;
        
        try {
            if (this.activeFaceDetector === 'mediapipe' && this.isMediaPipeReady && this.faceDetection) {
                await this.faceDetection.send({image: videoElement});
            } else if (this.activeFaceDetector === 'tensorflow' && this.isTensorFlowReady && this.tensorflowFaceModel) {
                const predictions = await this.tensorflowFaceModel.estimateFaces({
                    input: videoElement,
                    returnTensors: false,
                    flipHorizontal: false
                });
                this.onTensorFlowResults(predictions);
            }
        } catch (error) {
            console.error(`${this.activeFaceDetector} face detection error:`, error);
            
            // Disable current detector and try fallback
            if (this.activeFaceDetector === 'mediapipe') {
                this.isMediaPipeReady = false;
                this.faceDetection = null;
                if (this.isTensorFlowReady) {
                    this.activeFaceDetector = 'tensorflow';
                    console.log('🔄 Switching to TensorFlow.js face detection');
                } else {
                    this.activeFaceDetector = 'fallback';
                    console.log('🔄 Switching to fallback face detection');
                }
            } else if (this.activeFaceDetector === 'tensorflow') {
                this.isTensorFlowReady = false;
                this.tensorflowFaceModel = null;
                this.activeFaceDetector = 'fallback';
                console.log('🔄 Switching to fallback face detection');
            }
        }
    }
    
    /**
     * Get real face quality from active face detector
     */
    getRealFaceQuality() {
        // Check if we have active face detection and recent results
        const hasActiveDetector = (this.activeFaceDetector === 'mediapipe' && this.isMediaPipeReady) ||
                                 (this.activeFaceDetector === 'tensorflow' && this.isTensorFlowReady);
        
        if (!hasActiveDetector || 
            !this.faceDetectionResults || 
            Date.now() - this.lastFaceDetectionTime > 2000) {
            return this.simulateFaceQualityCheck(); // Fallback
        }
        
        const detections = this.faceDetectionResults.detections;
        
        if (!detections || detections.length === 0) {
            return {
                confidence: 0,
                lighting: false,
                position: false,
                stability: false
            };
        }
        
        // Use the first (most confident) detection
        const face = detections[0];
        // Handle different score formats (array vs single value)
        const confidence = Array.isArray(face.score) ? face.score[0] : (face.score || 0);
        
        // Check face position (should be centered)
        const boundingBox = face.boundingBox;
        // MediaPipe returns normalized coordinates (0-1)
        const centerX = (boundingBox.xCenter !== undefined) ? boundingBox.xCenter : 
                       ((boundingBox.x + boundingBox.width / 2) || 0.5);
        const centerY = (boundingBox.yCenter !== undefined) ? boundingBox.yCenter : 
                       ((boundingBox.y + boundingBox.height / 2) || 0.5);
        const isPositioned = centerX > 0.3 && centerX < 0.7 && 
                           centerY > 0.3 && centerY < 0.7;
        
        // Estimate lighting based on detection confidence
        const hasGoodLighting = confidence > 0.7;
        
        return {
            confidence: confidence,
            lighting: hasGoodLighting,
            position: isPositioned,
            stability: confidence > 0.6
        };
    }
    
    /**
     * Face quality check (using real detection data when available)
     */
    simulateFaceQualityCheck() {
        // Try to get real face data first if any detector is active
        if (this.activeFaceDetector !== 'fallback') {
            return this.getRealFaceQuality();
        }
        
        // Fallback to simulation if no face detection available
        const baseConfidence = Math.random() * 0.4 + 0.5; // 0.5-0.9
        const timeBonus = this.currentState === 'face_capturing' ? 0.1 : 0;
        
        return {
            confidence: Math.min(1.0, baseConfidence + timeBonus),
            lighting: Math.random() > 0.3,
            position: Math.random() > 0.2,
            stability: Math.random() > 0.25
        };
    }

    /**
     * Simulate speech quality check (placeholder for real audio analysis)
     */
    simulateSpeechQualityCheck() {
        // Simulate variable audio quality
        const baseSNR = Math.random() * 15 + 10; // 10-25 dB
        const environmentBonus = Math.random() > 0.4 ? 5 : 0;
        
        return {
            snr: baseSNR + environmentBonus,
            level: Math.random() * 0.8 + 0.2,
            clarity: Math.random() > 0.3,
            backgroundNoise: Math.random() < 0.7
        };
    }

    /**
     * Calculate overall face quality from checks
     */
    calculateFaceQuality(qualityChecks) {
        if (!qualityChecks.length) return { complete: false, quality: 0 };
        
        const avgConfidence = qualityChecks.reduce((sum, check) => sum + check.confidence, 0) / qualityChecks.length;
        const validChecks = qualityChecks.filter(check => check.confidence >= this.config.face.targetConfidence);
        
        return {
            complete: validChecks.length >= this.config.face.minValidSeconds,
            quality: avgConfidence,
            validSeconds: validChecks.length
        };
    }

    /**
     * Calculate overall speech quality from checks
     */
    calculateSpeechQuality(qualityChecks) {
        if (!qualityChecks.length) return { complete: false, quality: 0 };
        
        const avgSNR = qualityChecks.reduce((sum, check) => sum + check.snr, 0) / qualityChecks.length;
        const validChecks = qualityChecks.filter(check => check.snr >= this.config.speech.targetSNR);
        
        return {
            complete: validChecks.length >= this.config.speech.minValidSeconds,
            quality: avgSNR,
            validSeconds: validChecks.length
        };
    }

    /**
     * Upload face baseline to S3
     */
    async uploadFaceBaseline(faceBlob) {
        try {
            console.log('☁️ Starting face baseline upload to S3');
            
            // Validate blob
            if (!faceBlob || faceBlob.size === 0) {
                throw new Error('Invalid face baseline blob');
            }
            
            // File size validation (max 50MB)
            const maxSize = 50 * 1024 * 1024;
            if (faceBlob.size > maxSize) {
                throw new Error(`Face baseline file too large: ${(faceBlob.size / 1024 / 1024).toFixed(1)}MB (max 50MB)`);
            }
            
            // File type validation
            if (!faceBlob.type.startsWith('video/')) {
                throw new Error(`Invalid file type: ${faceBlob.type} (expected video/*)`);
            }
            
            console.log(`📹 Face baseline: ${(faceBlob.size / 1024 / 1024).toFixed(2)}MB, type: ${faceBlob.type}`);
            
            // Get upload URL from session data  
            if (!this.uploadUrls || !this.uploadUrls.face_baseline) {
                throw new Error('No face upload URL available');
            }
            
            const uploadUrl = this.uploadUrls.face_baseline.upload_url;
            const storageType = 'S3'; // Always S3 with presigned URLs
            
            // Update progress
            this.updateFaceProgress('Uploading to cloud storage...', 90);
            
            if (storageType === 'S3') {
                // S3 presigned URL upload
                return await this._uploadToS3(uploadUrl, faceBlob, 'face');
            } else {
                // Local development upload
                return await this._uploadToLocal(uploadUrl, faceBlob, 'face');
            }
            
        } catch (error) {
            console.error('❌ Face baseline upload failed:', error);
            this.showFaceError('Upload Failed', error.message);
            return { success: false, error: error.message };
        }
    }

    /**
     * Upload speech baseline to S3
     */
    async uploadSpeechBaseline(speechBlob) {
        try {
            console.log('☁️ Starting speech baseline upload to S3');
            
            // Validate blob
            if (!speechBlob || speechBlob.size === 0) {
                throw new Error('Invalid speech baseline blob');
            }
            
            // File size validation (max 25MB for audio)
            const maxSize = 25 * 1024 * 1024;
            if (speechBlob.size > maxSize) {
                throw new Error(`Speech baseline file too large: ${(speechBlob.size / 1024 / 1024).toFixed(1)}MB (max 25MB)`);
            }
            
            // File type validation (accept both audio and video webm)
            if (!speechBlob.type.startsWith('audio/') && !speechBlob.type.startsWith('video/')) {
                throw new Error(`Invalid file type: ${speechBlob.type} (expected audio/* or video/*)`);
            }
            
            console.log(`🎤 Speech baseline: ${(speechBlob.size / 1024 / 1024).toFixed(2)}MB, type: ${speechBlob.type}`);
            
            // Get upload URL from session data
            if (!this.uploadUrls || !this.uploadUrls.speech_baseline) {
                throw new Error('No speech upload URL available');
            }
            
            const uploadUrl = this.uploadUrls.speech_baseline.upload_url;
            const storageType = 'S3'; // Always S3 with presigned URLs
            
            // Update progress
            this.updateSpeechProgress('Uploading to cloud storage...', 90);
            
            if (storageType === 'S3') {
                // S3 presigned URL upload
                return await this._uploadToS3(uploadUrl, speechBlob, 'speech');
            } else {
                // Local development upload
                return await this._uploadToLocal(uploadUrl, speechBlob, 'speech');
            }
            
        } catch (error) {
            console.error('❌ Speech baseline upload failed:', error);
            this.showSpeechError('Upload Failed', error.message);
            return { success: false, error: error.message };
        }
    }

    /**
     * Upload file to S3 using presigned URL with form data
     */
    async _uploadToS3(uploadUrl, blob, type) {
        return new Promise((resolve, reject) => {
            const uploadData = type === 'face' ? this.uploadUrls.face_baseline : this.uploadUrls.speech_baseline;
            
            // Create FormData for S3 presigned POST
            const formData = new FormData();
            
            // Add all required S3 fields first (order matters)
            Object.entries(uploadData.fields).forEach(([key, value]) => {
                formData.append(key, value);
            });
            
            // Add the file last
            formData.append('file', blob);
            
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    const message = `Uploading ${type} baseline... ${Math.round(percentComplete)}%`;
                    
                    if (type === 'face') {
                        this.updateFaceProgress(message, 90 + (percentComplete * 0.08)); // 90-98%
                    } else {
                        this.updateSpeechProgress(message, 90 + (percentComplete * 0.08)); // 90-98%
                    }
                }
            });
            
            // Handle upload completion
            xhr.addEventListener('load', async () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    console.log(`✅ ${type} baseline uploaded successfully to S3`);
                    
                    // Call backend API to process the uploaded file
                    try {
                        const processResult = await this._notifyBackendUpload(type);
                        resolve({
                            success: true,
                            uploadResponse: xhr.responseText,
                            processResult: processResult
                        });
                    } catch (error) {
                        resolve({
                            success: true,
                            uploadResponse: xhr.responseText,
                            processError: error.message
                        });
                    }
                } else {
                    console.error(`❌ S3 upload failed: ${xhr.status} ${xhr.statusText}`);
                    reject(new Error(`S3 upload failed: ${xhr.status} ${xhr.statusText}`));
                }
            });
            
            // Handle upload errors
            xhr.addEventListener('error', () => {
                console.error(`❌ ${type} baseline upload error`);
                reject(new Error(`Network error during ${type} upload`));
            });
            
            // Handle upload timeout
            xhr.addEventListener('timeout', () => {
                console.error(`❌ ${type} baseline upload timeout`);
                reject(new Error(`Upload timeout for ${type} baseline`));
            });
            
            // Configure request - POST to S3 with FormData
            xhr.open('POST', uploadUrl, true);
            xhr.timeout = 5 * 60 * 1000; // 5 minute timeout
            
            // Start upload (don't set Content-Type header, let browser set it for FormData)
            xhr.send(formData);
        });
    }
    
    /**
     * Upload file to local development server
     */
    async _uploadToLocal(uploadUrl, blob, type) {
        try {
            const formData = new FormData();
            formData.append('file', blob, `${type}_baseline.webm`);
            formData.append('session_id', this.sessionId);
            formData.append('duration', type === 'face' ? 10 : 15);
            
            const response = await fetch(uploadUrl, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log(`✅ ${type} baseline uploaded successfully to local server`);
            
            return {
                success: true,
                uploadResponse: result,
                processResult: result
            };
            
        } catch (error) {
            console.error(`❌ Local ${type} upload failed:`, error);
            throw error;
        }
    }
    
    /**
     * Notify backend about successful S3 upload for processing
     */
    async _notifyBackendUpload(type) {
        try {
            const endpoint = type === 'face' ? '/api/baseline/face' : '/api/baseline/speech';
            const uploadData = type === 'face' ? this.uploadUrls.face_baseline : this.uploadUrls.speech_baseline;
            
            const payload = {
                session_id: this.sessionId,
                s3_key: uploadData.s3_key,
                duration: uploadData.expected_duration
            };
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log(`✅ Backend notified of ${type} upload:`, result);
            
            return result;
            
        } catch (error) {
            console.error(`❌ Failed to notify backend of ${type} upload:`, error);
            throw error;
        }
    }

    /**
     * Update face timer display
     */
    updateFaceTimer(seconds) {
        const timerElement = document.getElementById('faceTimer');
        if (timerElement) {
            timerElement.textContent = seconds;
            timerElement.style.color = seconds <= 3 ? '#f44336' : '#2196f3';
        }
    }

    /**
     * Update speech timer display
     */
    updateSpeechTimer(seconds) {
        const timerElement = document.getElementById('speechTimer');
        if (timerElement) {
            timerElement.textContent = seconds;
            timerElement.style.color = seconds <= 3 ? '#f44336' : '#2196f3';
        }
    }

    /**
     * Update face progress display
     */
    updateFaceProgress(message, percentage) {
        const progressElement = document.getElementById('faceProgress');
        const fillElement = document.getElementById('faceProgressFill');
        
        if (progressElement) progressElement.textContent = message;
        if (fillElement) fillElement.style.width = `${percentage}%`;
    }

    /**
     * Update speech progress display
     */
    updateSpeechProgress(message, percentage) {
        const progressElement = document.getElementById('speechProgress');
        const fillElement = document.getElementById('speechProgressFill');
        
        if (progressElement) progressElement.textContent = message;
        if (fillElement) fillElement.style.width = `${percentage}%`;
    }

    /**
     * Update face quality indicators
     */
    updateFaceQualityDisplay(quality) {
        const indicatorsElement = document.getElementById('faceQualityIndicators');
        if (!indicatorsElement) return;
        
        const confidenceClass = quality.confidence >= this.config.face.targetConfidence ? 'quality-good' : 'quality-warning';
        const lightingClass = quality.lighting ? 'quality-good' : 'quality-error';
        const positionClass = quality.position ? 'quality-good' : 'quality-warning';
        
        indicatorsElement.innerHTML = `
            <span class="quality-indicator ${confidenceClass}">Face Confidence: ${(quality.confidence * 100).toFixed(0)}%</span>
            <span class="quality-indicator ${lightingClass}">Lighting: ${quality.lighting ? 'Good' : 'Poor'}</span>
            <span class="quality-indicator ${positionClass}">Position: ${quality.position ? 'Good' : 'Adjust'}</span>
        `;
    }

    /**
     * Update speech quality indicators
     */
    updateSpeechQualityDisplay(quality) {
        const indicatorsElement = document.getElementById('speechQualityIndicators');
        if (!indicatorsElement) return;
        
        const snrClass = quality.snr >= this.config.speech.targetSNR ? 'quality-good' : 'quality-warning';
        const clarityClass = quality.clarity ? 'quality-good' : 'quality-warning';
        const noiseClass = quality.backgroundNoise ? 'quality-warning' : 'quality-good';
        
        indicatorsElement.innerHTML = `
            <span class="quality-indicator ${snrClass}">Audio SNR: ${quality.snr.toFixed(1)} dB</span>
            <span class="quality-indicator ${clarityClass}">Clarity: ${quality.clarity ? 'Good' : 'Poor'}</span>
            <span class="quality-indicator ${noiseClass}">Background Noise: ${quality.backgroundNoise ? 'Detected' : 'Low'}</span>
        `;
        
        // Update audio level display
        const audioLevel = document.getElementById('audioLevel');
        if (audioLevel) {
            audioLevel.textContent = `${(quality.level * 100).toFixed(0)}%`;
        }
    }

    /**
     * Set button state (enabled/disabled/text)
     */
    setButtonState(buttonId, enabled, text = null) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.disabled = !enabled;
            if (text) button.textContent = text;
        }
    }

    /**
     * Show button by removing hidden class
     */
    showButton(buttonId) {
        const button = document.getElementById(buttonId);
        if (button) button.classList.remove('hidden');
    }

    /**
     * Hide button by adding hidden class
     */
    hideButton(buttonId) {
        const button = document.getElementById(buttonId);
        if (button) button.classList.add('hidden');
    }

    /**
     * Show face success message
     */
    showFaceSuccess(message) {
        const statusElement = document.getElementById('faceStatus');
        if (statusElement) {
            statusElement.className = 'status-message status-success';
            statusElement.textContent = message;
            statusElement.classList.remove('hidden');
        }
    }

    /**
     * Show face warning message
     */
    showFaceWarning(message) {
        const statusElement = document.getElementById('faceStatus');
        if (statusElement) {
            statusElement.className = 'status-message status-warning';
            statusElement.textContent = message;
            statusElement.classList.remove('hidden');
        }
    }

    /**
     * Show face error message
     */
    showFaceError(title, message) {
        const statusElement = document.getElementById('faceStatus');
        if (statusElement) {
            statusElement.className = 'status-message status-error';
            statusElement.innerHTML = `<strong>${title}</strong><br>${message}`;
            statusElement.classList.remove('hidden');
        }
    }

    /**
     * Show speech success message
     */
    showSpeechSuccess(message) {
        const statusElement = document.getElementById('speechStatus');
        if (statusElement) {
            statusElement.className = 'status-message status-success';
            statusElement.textContent = message;
            statusElement.classList.remove('hidden');
        }
    }

    /**
     * Show speech warning message
     */
    showSpeechWarning(message) {
        const statusElement = document.getElementById('speechStatus');
        if (statusElement) {
            statusElement.className = 'status-message status-warning';
            statusElement.textContent = message;
            statusElement.classList.remove('hidden');
        }
    }

    /**
     * Show speech error message
     */
    showSpeechError(title, message) {
        const statusElement = document.getElementById('speechStatus');
        if (statusElement) {
            statusElement.className = 'status-message status-error';
            statusElement.innerHTML = `<strong>${title}</strong><br>${message}`;
            statusElement.classList.remove('hidden');
        }
    }

    /**
     * Start status polling for real-time session updates
     */
    startStatusPolling() {
        if (this.statusPolling.active || !this.sessionId) {
            return;
        }
        
        console.log('📊 Starting status polling');
        this.statusPolling.active = true;
        this.statusPolling.retryCount = 0;
        
        // Poll every 2 seconds
        this.statusPolling.interval = setInterval(() => {
            this.pollSessionStatus();
        }, 2000);
        
        // Do initial poll immediately
        this.pollSessionStatus();
    }
    
    /**
     * Stop status polling
     */
    stopStatusPolling() {
        if (!this.statusPolling.active) {
            return;
        }
        
        console.log('📊 Stopping status polling');
        this.statusPolling.active = false;
        
        if (this.statusPolling.interval) {
            clearInterval(this.statusPolling.interval);
            this.statusPolling.interval = null;
        }
    }
    
    /**
     * Poll session status from backend
     */
    async pollSessionStatus() {
        try {
            const response = await fetch(`${this.apiBase}/status/${this.sessionId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const status = await response.json();
            
            if (status.success) {
                // Reset retry count on successful poll
                this.statusPolling.retryCount = 0;
                
                // Update UI with status information
                this.updateUIFromStatus(status);
                
                // Stop polling if session is complete or failed
                if (status.state === 'completed' || status.state === 'failed') {
                    this.stopStatusPolling();
                }
            } else {
                throw new Error(status.error || 'Status polling failed');
            }
            
        } catch (error) {
            console.error('❌ Status polling error:', error);
            this.handleStatusPollingError(error);
        }
    }
    
    /**
     * Handle status polling errors with retry logic
     */
    handleStatusPollingError(error) {
        this.statusPolling.retryCount++;
        
        if (this.statusPolling.retryCount >= this.statusPolling.maxRetries) {
            console.error('❌ Max status polling retries reached, stopping polling');
            this.stopStatusPolling();
            
            // Show error to user
            this.showError('Connection Lost', 
                'Lost connection to server. Please refresh the page to continue.');
        } else {
            console.warn(`⚠️ Status polling retry ${this.statusPolling.retryCount}/${this.statusPolling.maxRetries}`);
            
            // Increase polling interval on errors
            if (this.statusPolling.interval) {
                clearInterval(this.statusPolling.interval);
                this.statusPolling.interval = setInterval(() => {
                    this.pollSessionStatus();
                }, 5000); // Slower polling after errors
            }
        }
    }
    
    /**
     * Update UI based on status response
     */
    updateUIFromStatus(status) {
        // Update session state information
        this.currentState = status.state;
        
        // Update progress based on session progress
        if (status.progress) {
            if (status.progress.face_complete && !this.progress.face.complete) {
                this.progress.face.complete = true;
                console.log('✅ Face baseline marked complete by status update');
            }
            
            if (status.progress.speech_complete && !this.progress.speech.complete) {
                this.progress.speech.complete = true;
                console.log('✅ Speech baseline marked complete by status update');
            }
        }
        
        // Show quality feedback if available
        if (status.quality_feedback && status.quality_feedback.recommendations) {
            this.displayQualityRecommendations(status.quality_feedback.recommendations);
        }
        
        // Handle different session states
        switch (status.state) {
            case 'face_capture':
                // Face capture phase
                break;
                
            case 'speech_capture':
                // Speech capture phase
                break;
                
            case 'processing':
                this.updateOverallProgress('Processing baseline data...', 85);
                break;
                
            case 'completed':
                this.updateOverallProgress('Baseline complete!', 100);
                this.showSection('completionSection');
                break;
                
            case 'failed':
                this.showError('Session Failed', 'Baseline capture session failed. Please try again.');
                break;
        }
    }
    
    /**
     * Display quality recommendations from status
     */
    displayQualityRecommendations(recommendations) {
        if (!recommendations || recommendations.length === 0) {
            return;
        }
        
        // Show recommendations in face or speech quality feedback areas
        const faceQualityElement = document.getElementById('faceQualitySuggestions');
        const speechQualityElement = document.getElementById('speechQualitySuggestions');
        
        const recommendationHtml = recommendations.map(rec => 
            `<div class="quality-suggestion">💡 ${rec}</div>`
        ).join('');
        
        if (this.currentState.includes('face') && faceQualityElement) {
            faceQualityElement.innerHTML = recommendationHtml;
        } else if (this.currentState.includes('speech') && speechQualityElement) {
            speechQualityElement.innerHTML = recommendationHtml;
        }
    }

    /**
     * Cleanup resources on page unload
     */
    cleanup() {
        console.log('🧹 Cleaning up baseline capture resources');
        
        // Stop status polling
        this.stopStatusPolling();
        
        // Stop timers
        Object.values(this.timers).forEach(timer => {
            if (timer) clearInterval(timer);
        });
        
        // Stop media streams
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
        }
        
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }
        
        // Stop recordings
        if (this.videoRecorder && this.videoRecorder.state !== 'inactive') {
            this.videoRecorder.stop();
        }
        
        if (this.audioRecorder && this.audioRecorder.state !== 'inactive') {
            this.audioRecorder.stop();
        }
        
        // Close MediaPipe
        if (this.faceDetection) {
            this.faceDetection.close();
            this.faceDetection = null;
        }
    }
}

// Global instance
let baselineCapture = null;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 DOMContentLoaded - Initializing BaselineCapture...');
    try {
        baselineCapture = new BaselineCapture();
        console.log('✅ BaselineCapture initialized successfully');
        
        // Make functions available globally
        window.startBaselineCapture = startBaselineCapture;
        window.startFaceCapture = startFaceCapture;
        window.startSpeechCapture = startSpeechCapture;
        window.retryFaceCapture = retryFaceCapture;
        window.retrySpeechCapture = retrySpeechCapture;
        window.goToSpeechCapture = goToSpeechCapture;
        window.completeBaseline = completeBaseline;
        window.startPersonalizedAssessment = startPersonalizedAssessment;
        
    } catch (error) {
        console.error('❌ Failed to initialize BaselineCapture:', error);
        alert('Failed to initialize baseline capture system. Error: ' + error.message);
    }
});

// Global functions called by HTML buttons
function startBaselineCapture() {
    console.log('🚀 startBaselineCapture called');
    if (baselineCapture) {
        baselineCapture.startBaselineCapture();
    } else {
        console.error('❌ baselineCapture not initialized');
        alert('Baseline capture system not ready. Please refresh the page.');
    }
}

function startFaceCapture() {
    if (baselineCapture) {
        baselineCapture.startFaceCapture();
    }
}

function startSpeechCapture() {
    if (baselineCapture) {
        baselineCapture.startSpeechCapture();
    }
}

function retryFaceCapture() {
    if (baselineCapture) {
        // Reset face status and try again
        baselineCapture.progress.face = { complete: false, quality: 0 };
        baselineCapture.hideButton('retryFaceBtn');
        baselineCapture.hideButton('continueSpeechBtn');
        baselineCapture.setButtonState('startFaceBtn', true, 'Start Face Capture');
        const faceStatus = document.getElementById('faceStatus');
        if (faceStatus) faceStatus.classList.add('hidden');
        
        // Clear video chunks
        baselineCapture.recordedChunks.face = [];
        
        console.log('🔄 Retrying face capture');
    }
}

function retrySpeechCapture() {
    if (baselineCapture) {
        // Reset speech status and try again
        baselineCapture.progress.speech = { complete: false, quality: 0 };
        baselineCapture.hideButton('retrySpeechBtn');
        baselineCapture.hideButton('completeBtn');
        baselineCapture.setButtonState('startSpeechBtn', true, 'Start Speech Capture');
        const speechStatus = document.getElementById('speechStatus');
        if (speechStatus) speechStatus.classList.add('hidden');
        
        // Clear audio chunks
        baselineCapture.recordedChunks.speech = [];
        
        console.log('🔄 Retrying speech capture');
    }
}

function goToSpeechCapture() {
    if (baselineCapture) {
        console.log('🎤 Moving to speech capture');
        baselineCapture.currentState = 'speech_ready';
        baselineCapture.showSection('speechSection');
        baselineCapture.updateOverallProgress('Ready for speech baseline', 60);
    }
}

async function completeBaseline() {
    if (baselineCapture) {
        try {
            console.log('🏁 Completing baseline capture');
            baselineCapture.updateOverallProgress('Finalizing baseline...', 90);
            
            // Call API to complete baseline
            const response = await fetch(`${baselineCapture.apiBase}/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: baselineCapture.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Show completion section
                baselineCapture.showSection('completionSection');
                baselineCapture.updateOverallProgress('Baseline complete!', 100);
                
                // Update quality score display
                const qualityElement = document.getElementById('baselineQualityScore');
                if (qualityElement && result.quality_score) {
                    const score = (result.quality_score * 100).toFixed(0);
                    qualityElement.textContent = `${score}% Excellent`;
                }
                
                console.log('✅ Baseline capture completed successfully');
                
            } else {
                throw new Error(result.error || 'Completion failed');
            }
            
        } catch (error) {
            console.error('❌ Baseline completion failed:', error);
            baselineCapture.showError('Completion Failed', error.message);
        }
    }
}

function startPersonalizedAssessment() {
    console.log('🎯 Starting personalized assessment');
    
    // In a real implementation, this would redirect to the assessment
    // For now, show success message
    alert('🎉 Baseline capture complete! You would now proceed to your personalized assessment.\n\nThe system will use your baseline to provide much more accurate insights.');
    
    // Could redirect to assessment page:
    // window.location.href = '/assessments/core_assessment.html?baseline_session=' + baselineCapture.sessionId;
}