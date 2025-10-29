// Simple Baseline Capture JavaScript
// Implements face detection, quality metrics, and video recording

class SimpleBaselineCapture {
    constructor() {
        console.log('🚀 Initializing Simple Baseline Capture');
        
        // Quality thresholds
        this.thresholds = {
            lighting: 60,      // Minimum brightness percentage
            confidence: 80,    // Minimum face confidence percentage  
            positioning: true, // Face must be centered
            overallQuality: 75 // Minimum overall quality score
        };
        
        // Current metrics
        this.metrics = {
            lighting: 0,
            confidence: 0,
            position: false,
            qualityScore: 0
        };
        
        // MediaPipe and camera state
        this.faceMesh = null;
        this.videoStream = null;
        this.isMediaPipeReady = false;
        this.faceDetectionResults = null;
        this.lastFaceDetectionTime = null;
        
        // Canvas for overlay drawing
        this.canvas = null;
        this.ctx = null;
        
        // Recording state
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.isRecording = false;
        this.recordingTimer = null;
        
        // Initialize the system
        this.init();
    }
    
    async init() {
        try {
            console.log('🎯 Starting initialization sequence');
            
            // Get canvas context for drawing overlay
            this.setupCanvas();
            
            // Set up camera access
            await this.setupCamera();
            
            // Initialize MediaPipe Face Mesh
            await this.initializeMediaPipe();
            
            // Start real-time quality monitoring
            this.startQualityMonitoring();
            
            console.log('✅ Initialization complete');
            
        } catch (error) {
            console.error('❌ Initialization failed:', error);
            this.showStatus('Failed to initialize camera and face detection', 'error');
        }
    }
    
    setupCanvas() {
        console.log('🎨 Setting up canvas for overlay drawing');
        this.canvas = document.getElementById('overlayCanvas');
        this.ctx = this.canvas.getContext('2d');
    }
    
    async setupCamera() {
        console.log('📹 Setting up camera access');
        
        try {
            this.videoStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 30 }
                }
            });
            
            const videoElement = document.getElementById('videoElement');
            videoElement.srcObject = this.videoStream;
            
            console.log('✅ Camera access granted');
            this.showStatus('Camera initialized successfully', 'success');
            
        } catch (error) {
            console.error('❌ Camera access failed:', error);
            this.showStatus('Failed to access camera. Please allow camera permissions.', 'error');
            throw error;
        }
    }
    
    async initializeMediaPipe() {
        console.log('🎭 Initializing MediaPipe Face Mesh');
        
        try {
            if (typeof FaceMesh === 'undefined') {
                throw new Error('MediaPipe Face Mesh not loaded');
            }
            
            this.faceMesh = new FaceMesh({
                locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
            });
            
            this.faceMesh.setOptions({
                maxNumFaces: 1,
                refineLandmarks: true,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });
            
            this.faceMesh.onResults(this.onFaceDetectionResults.bind(this));
            
            this.isMediaPipeReady = true;
            console.log('✅ MediaPipe Face Mesh initialized');
            
        } catch (error) {
            console.error('❌ MediaPipe initialization failed:', error);
            this.showStatus('Face detection initialization failed', 'error');
            throw error;
        }
    }
    
    onFaceDetectionResults(results) {
        console.log('👤 Processing face detection results');
        
        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
            // Store face detection data
            this.faceDetectionResults = {
                landmarks: results.multiFaceLandmarks[0],
                confidence: this.calculateFaceConfidence(results.multiFaceLandmarks[0])
            };
            this.lastFaceDetectionTime = Date.now();
            
            // Calculate face bounding box for overlay
            const boundingBox = this.calculateFaceBoundingBox(this.faceDetectionResults.landmarks);
            this.drawFaceOverlay(boundingBox);
            
        } else {
            this.faceDetectionResults = null;
            this.clearOverlay();
        }
    }
    
    calculateFaceConfidence(landmarks) {
        // Calculate confidence based on landmark count and consistency
        const expectedCount = 468;
        const actualCount = landmarks.length;
        return Math.min(100, (actualCount / expectedCount) * 100);
    }
    
    calculateFaceBoundingBox(landmarks) {
        if (!landmarks || landmarks.length === 0) return null;
        
        let minX = 1, minY = 1, maxX = 0, maxY = 0;
        
        landmarks.forEach(landmark => {
            minX = Math.min(minX, landmark.x);
            minY = Math.min(minY, landmark.y);
            maxX = Math.max(maxX, landmark.x);
            maxY = Math.max(maxY, landmark.y);
        });
        
        return {
            x: minX * this.canvas.width,
            y: minY * this.canvas.height,
            width: (maxX - minX) * this.canvas.width,
            height: (maxY - minY) * this.canvas.height
        };
    }
    
    drawFaceOverlay(boundingBox) {
        this.clearOverlay();
        
        if (!boundingBox) return;
        
        // Color-code rectangle based on overall quality
        const color = this.metrics.qualityScore >= this.thresholds.overallQuality ? '#4caf50' : '#f44336';
        
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 3;
        this.ctx.strokeRect(boundingBox.x, boundingBox.y, boundingBox.width, boundingBox.height);
    }
    
    clearOverlay() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    calculateFrameBrightness() {
        try {
            const videoElement = document.getElementById('videoElement');
            if (!videoElement || videoElement.readyState < 2) return 50;
            
            // Create hidden canvas for analysis
            const analysisCanvas = document.createElement('canvas');
            analysisCanvas.width = 160;
            analysisCanvas.height = 120;
            const ctx = analysisCanvas.getContext('2d');
            
            // Draw video frame
            ctx.drawImage(videoElement, 0, 0, analysisCanvas.width, analysisCanvas.height);
            
            // Get image data
            const imageData = ctx.getImageData(0, 0, analysisCanvas.width, analysisCanvas.height);
            const data = imageData.data;
            
            // Calculate average brightness
            let sum = 0;
            for (let i = 0; i < data.length; i += 4) {
                const brightness = (data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114);
                sum += brightness;
            }
            
            const avgBrightness = sum / (data.length / 4);
            const brightnessPercent = (avgBrightness / 255) * 100;
            
            console.log('🔆 Brightness calculated:', brightnessPercent.toFixed(1) + '%');
            return brightnessPercent;
            
        } catch (error) {
            console.error('❌ Brightness calculation error:', error);
            return 50;
        }
    }
    
    calculateLighting() {
        const brightness = this.calculateFrameBrightness();
        
        if (brightness < 30) {
            return { level: 'Too Dark', percent: brightness, good: false };
        } else if (brightness < 60) {
            return { level: 'Low', percent: brightness, good: false };
        } else if (brightness > 85) {
            return { level: 'Too Bright', percent: brightness, good: false };
        } else {
            return { level: 'Good', percent: brightness, good: true };
        }
    }
    
    validateFacePosition(landmarks) {
        if (!landmarks || landmarks.length < 2) return false;
        
        // Use nose tip (landmark index 1) to check centering
        const noseTip = landmarks[1];
        if (!noseTip) return false;
        
        const centerX = noseTip.x;
        const centerY = noseTip.y;
        
        // Check if face is within center bounds
        return centerX > 0.35 && centerX < 0.65 && centerY > 0.35 && centerY < 0.65;
    }
    
    calculateOverallQualityScore() {
        const weights = {
            lighting: 0.3,
            confidence: 0.4,
            position: 0.3
        };
        
        let score = 0;
        score += (this.metrics.lighting / 100) * weights.lighting * 100;
        score += (this.metrics.confidence / 100) * weights.confidence * 100;
        score += (this.metrics.position ? 1 : 0) * weights.position * 100;
        
        return Math.round(score);
    }
    
    updateMetrics() {
        // Update lighting metric
        const lightingResult = this.calculateLighting();
        this.metrics.lighting = lightingResult.percent;
        
        // Update face confidence and position if face detected
        if (this.faceDetectionResults && Date.now() - this.lastFaceDetectionTime < 2000) {
            this.metrics.confidence = this.faceDetectionResults.confidence;
            this.metrics.position = this.validateFacePosition(this.faceDetectionResults.landmarks);
        } else {
            this.metrics.confidence = 0;
            this.metrics.position = false;
        }
        
        // Calculate overall quality score
        this.metrics.qualityScore = this.calculateOverallQualityScore();
    }
    
    updateUI() {
        // Update lighting metric display
        const lightingResult = this.calculateLighting();
        const lightingElement = document.getElementById('lightingMetric');
        lightingElement.textContent = `Lighting: ${lightingResult.level} (${Math.round(lightingResult.percent)}%)`;
        lightingElement.className = `metric-item ${lightingResult.good ? 'metric-good' : 'metric-error'}`;
        
        // Update confidence metric
        const confidenceElement = document.getElementById('confidenceMetric');
        confidenceElement.textContent = `Face Confidence: ${Math.round(this.metrics.confidence)}%`;
        confidenceElement.className = `metric-item ${this.metrics.confidence >= this.thresholds.confidence ? 'metric-good' : 'metric-warning'}`;
        
        // Update position metric
        const positionElement = document.getElementById('positionMetric');
        positionElement.textContent = `Position: ${this.metrics.position ? 'Centered' : 'Adjust Position'}`;
        positionElement.className = `metric-item ${this.metrics.position ? 'metric-good' : 'metric-warning'}`;
        
        // Update overall quality score
        const qualityElement = document.getElementById('qualityScoreMetric');
        qualityElement.textContent = `Overall Quality: ${this.metrics.qualityScore}%`;
        qualityElement.className = `metric-item ${this.metrics.qualityScore >= this.thresholds.overallQuality ? 'metric-good' : 'metric-warning'}`;
        
        // Update guidance
        this.updateGuidance();
        
        // Update start button state
        this.updateStartButton();
    }
    
    updateGuidance() {
        const guidanceElement = document.getElementById('guidanceText');
        const suggestions = [];
        
        if (this.metrics.lighting < this.thresholds.lighting) {
            if (this.metrics.lighting < 30) {
                suggestions.push('Turn on more lights - room is too dark');
            } else {
                suggestions.push('Improve lighting - add more ambient light');
            }
        }
        
        if (this.metrics.confidence < this.thresholds.confidence) {
            suggestions.push('Ensure your face is clearly visible to camera');
        }
        
        if (!this.metrics.position) {
            suggestions.push('Center your face in the camera view');
        }
        
        if (suggestions.length === 0) {
            guidanceElement.textContent = '✅ All quality metrics are good! Ready to capture.';
        } else {
            guidanceElement.innerHTML = suggestions.map(s => `• ${s}`).join('<br>');
        }
    }
    
    updateStartButton() {
        const startButton = document.getElementById('startButton');
        const allQualityGood = 
            this.metrics.lighting >= this.thresholds.lighting &&
            this.metrics.confidence >= this.thresholds.confidence &&
            this.metrics.position &&
            this.metrics.qualityScore >= this.thresholds.overallQuality;
        
        startButton.disabled = !allQualityGood || this.isRecording;
        
        if (allQualityGood && !this.isRecording) {
            this.showStatus('Ready to capture! Click "Start Capture" to begin 10-second recording.', 'success');
        } else if (this.isRecording) {
            this.showStatus('Recording in progress...', 'info');
        } else {
            this.showStatus('Adjust your setup until all quality metrics are good', 'info');
        }
    }
    
    startQualityMonitoring() {
        console.log('👀 Starting quality monitoring');
        
        // Process MediaPipe frames
        setInterval(() => {
            if (this.isMediaPipeReady && this.faceMesh) {
                const videoElement = document.getElementById('videoElement');
                if (videoElement && videoElement.readyState >= 2) {
                    this.faceMesh.send({image: videoElement});
                }
            }
        }, 100); // 10 FPS for MediaPipe processing
        
        // Update metrics and UI
        setInterval(() => {
            this.updateMetrics();
            this.updateUI();
        }, 500); // Update UI every 500ms
    }
    
    async startCapture() {
        try {
            console.log('🎬 Starting video capture');
            this.isRecording = true;
            
            // Initialize MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.videoStream, {
                mimeType: 'video/webm;codecs=vp9'
            });
            
            this.recordedChunks = [];
            
            // Set up recording event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.onRecordingComplete();
            };
            
            this.mediaRecorder.onerror = (error) => {
                console.error('❌ Recording error:', error);
                this.showStatus('Recording failed', 'error');
                this.isRecording = false;
            };
            
            // Show countdown and progress
            await this.startCountdown();
            
            // Start recording
            this.mediaRecorder.start(250); // Collect data every 250ms
            
            // Start 10-second recording timer
            this.startRecordingTimer();
            
        } catch (error) {
            console.error('❌ Failed to start capture:', error);
            this.showStatus('Failed to start recording', 'error');
            this.isRecording = false;
        }
    }
    
    async startCountdown() {
        const statusElement = document.getElementById('statusMessage');
        
        for (let i = 3; i > 0; i--) {
            statusElement.textContent = `Starting recording in ${i}...`;
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    
    startRecordingTimer() {
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        progressContainer.style.display = 'block';
        
        let secondsElapsed = 0;
        const totalSeconds = 10;
        
        this.recordingTimer = setInterval(() => {
            secondsElapsed++;
            const progress = (secondsElapsed / totalSeconds) * 100;
            
            progressFill.style.width = progress + '%';
            progressText.textContent = `Recording: ${secondsElapsed}/${totalSeconds} seconds`;
            
            if (secondsElapsed >= totalSeconds) {
                clearInterval(this.recordingTimer);
                this.stopRecording();
            }
        }, 1000);
    }
    
    stopRecording() {
        console.log('⏹️ Stopping recording');
        
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }
    
    onRecordingComplete() {
        console.log('✅ Recording complete');
        
        // Create blob from recorded chunks
        const recordedBlob = new Blob(this.recordedChunks, { type: 'video/webm' });
        
        // Upload to server
        this.uploadRecording(recordedBlob);
        
        // Reset UI
        document.getElementById('progressContainer').style.display = 'none';
        this.isRecording = false;
    }
    
    async uploadRecording(videoBlob) {
        try {
            console.log('📤 Uploading recording to server');
            this.showStatus('Uploading recording...', 'info');
            
            // Create FormData for upload
            const formData = new FormData();
            formData.append('video', videoBlob, `baseline_capture_${Date.now()}.webm`);
            formData.append('metrics', JSON.stringify(this.metrics));
            
            // Upload to server
            const response = await fetch('/api/upload_baseline', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Upload successful:', result);
                this.showStatus('Recording uploaded successfully!', 'success');
                
                // Reset for next capture
                setTimeout(() => {
                    this.resetUI();
                }, 2000);
                
            } else {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            
        } catch (error) {
            console.error('❌ Upload failed:', error);
            this.showStatus('Upload failed. Please try again.', 'error');
            
            // Retry logic
            setTimeout(() => {
                if (confirm('Upload failed. Would you like to retry?')) {
                    this.uploadRecording(videoBlob);
                } else {
                    this.resetUI();
                }
            }, 1000);
        }
    }
    
    resetUI() {
        console.log('🔄 Resetting UI for next capture');
        this.showStatus('Ready for next capture', 'info');
        document.getElementById('progressContainer').style.display = 'none';
        this.isRecording = false;
    }
    
    showStatus(message, type = 'info') {
        const statusElement = document.getElementById('statusMessage');
        statusElement.textContent = message;
        statusElement.className = `status-message status-${type}`;
    }
}

// Global function for button onclick
function startCapture() {
    if (window.simpleBaselineCapture) {
        window.simpleBaselineCapture.startCapture();
    } else {
        console.error('❌ Simple baseline capture not initialized');
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM loaded, initializing Simple Baseline Capture');
    window.simpleBaselineCapture = new SimpleBaselineCapture();
});