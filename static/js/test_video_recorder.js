/**
 * Test Video Recorder - Modular video/audio recording component for tests
 * Handles MediaRecorder, chunking, and S3 uploads during test sessions
 */

class VideoRecorder {
    constructor(options = {}) {
        // Configuration
        this.CHUNK_DURATION_MS = options.chunkDuration || 5000; // 5 seconds
        this.MIME_TYPE = options.mimeType || 'video/webm;codecs=vp8,opus';
        
        // DOM elements
        this.videoElement = options.videoElement || document.getElementById('videoPreview');
        this.statusElement = options.statusElement || document.getElementById('recordingStatus');
        this.sessionIdElement = options.sessionIdElement || document.getElementById('videoSessionId');
        this.durationElement = options.durationElement || document.getElementById('videoDuration');
        this.chunksElement = options.chunksElement || document.getElementById('chunksRecorded');
        this.recordBtn = options.recordBtn || document.getElementById('recordBtn');
        this.stopBtn = options.stopBtn || document.getElementById('stopBtn');
        
        // State
        this.mediaStream = null;
        this.mediaRecorder = null;
        this.isRecording = false;
        this.recordingStartTime = null;
        this.sessionId = null;
        this.chunkNumber = 0;
        this.chunksRecorded = 0;
        this.chunksUploaded = 0;
        this.uploadQueue = [];
        this.durationInterval = null;
        this.chunkInterval = null; // Timer for chunking
        this.currentChunkData = []; // Accumulate data for current chunk
        this.testSessionId = null; // Link to test session
        
        // Callbacks
        this.onRecordingStart = options.onRecordingStart || null;
        this.onRecordingStop = options.onRecordingStop || null;
        this.onError = options.onError || null;
        this.onChunkUploaded = options.onChunkUploaded || null;
    }
    
    /**
     * Initialize camera and microphone access
     */
    async initializeCamera() {
        try {
            console.log('[VideoRecorder] Initializing camera...');
            
            // Request camera and microphone permissions
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Display video preview
            if (this.videoElement) {
                this.videoElement.srcObject = this.mediaStream;
            }
            
            // Enable record button
            if (this.recordBtn) {
                this.recordBtn.disabled = false;
            }
            
            this.updateStatus('Ready', 'info');
            console.log('[VideoRecorder] Camera initialized successfully');
            return true;
            
        } catch (error) {
            console.error('[VideoRecorder] Error accessing camera:', error);
            this.showError('Failed to access camera/microphone. Please check permissions.');
            
            if (this.recordBtn) {
                this.recordBtn.disabled = true;
            }
            
            if (this.onError) {
                this.onError('camera_init_failed', error);
            }
            
            return false;
        }
    }
    
    /**
     * Start recording with optional test session linking
     */
    async startRecording(testSessionId = null) {
        if (!this.mediaStream) {
            this.showError('No media stream available');
            return false;
        }
        
        try {
            console.log('[VideoRecorder] Starting recording...');
            
            // Store test session link
            this.testSessionId = testSessionId;
            
            // Generate new video session ID
            this.sessionId = this.generateSessionId();
            
            if (this.sessionIdElement) {
                this.sessionIdElement.textContent = this.sessionId;
            }
            
            // Reset counters
            this.chunkNumber = 0;
            this.chunksRecorded = 0;
            this.chunksUploaded = 0;
            this.uploadQueue = [];
            
            // Detect supported MIME type
            const selectedMimeType = this.detectSupportedMimeType();
            if (!selectedMimeType) {
                this.showError('No compatible video recording format found in this browser');
                return false;
            }
            
            console.log(`[VideoRecorder] Using MIME type: ${selectedMimeType}`);
            
            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.mediaStream, {
                mimeType: selectedMimeType,
                videoBitsPerSecond: 1000000, // 1 Mbps
                audioBitsPerSecond: 128000   // 128 kbps
            });
            
            // Set up event handlers
            this.setupMediaRecorderEvents();
            
            // Start recording without timeslice to ensure complete files
            this.mediaRecorder.start();
            
            // Set up chunking timer
            this.startChunkTimer();
            
            // Update state and UI
            this.isRecording = true;
            this.recordingStartTime = Date.now();
            
            if (this.recordBtn) this.recordBtn.disabled = true;
            if (this.stopBtn) this.stopBtn.disabled = false;
            
            this.updateStatus('Recording', 'recording');
            
            // Start duration timer
            this.startDurationTimer();
            
            // Trigger callback
            if (this.onRecordingStart) {
                this.onRecordingStart(this.sessionId, this.testSessionId);
            }
            
            console.log('[VideoRecorder] Recording started successfully');
            return true;
            
        } catch (error) {
            console.error('[VideoRecorder] Error starting recording:', error);
            this.showError('Failed to start recording: ' + error.message);
            
            if (this.onError) {
                this.onError('recording_start_failed', error);
            }
            
            return false;
        }
    }
    
    /**
     * Stop recording
     */
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            console.log('[VideoRecorder] Stopping recording...');
            
            // Stop chunk timer first
            if (this.chunkInterval) {
                clearInterval(this.chunkInterval);
                this.chunkInterval = null;
            }
            
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Update UI
            if (this.recordBtn) this.recordBtn.disabled = false;
            if (this.stopBtn) this.stopBtn.disabled = true;
            
            this.updateStatus('Stopped', 'stopped');
            
            // Stop duration timer
            if (this.durationInterval) {
                clearInterval(this.durationInterval);
                this.durationInterval = null;
            }
            
            // Trigger callback
            if (this.onRecordingStop) {
                this.onRecordingStop(this.sessionId, this.testSessionId);
            }
            
            console.log('[VideoRecorder] Recording stopped');
        }
    }
    
    /**
     * Detect supported MIME type for MediaRecorder
     */
    detectSupportedMimeType() {
        const supportedTypes = [
            'video/webm',
            'video/webm;codecs=vp8',
            'video/webm;codecs=vp9',
            'video/webm;codecs=h264',
            'video/mp4'
        ];
        
        for (const type of supportedTypes) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        
        return null;
    }
    
    /**
     * Set up MediaRecorder event handlers
     */
    setupMediaRecorderEvents() {
        this.mediaRecorder.ondataavailable = (event) => {
            this.handleDataAvailable(event);
        };
        
        this.mediaRecorder.onstop = () => {
            console.log('[VideoRecorder] MediaRecorder stopped');
        };
        
        this.mediaRecorder.onstart = () => {
            console.log('[VideoRecorder] MediaRecorder started');
        };
        
        this.mediaRecorder.onerror = (event) => {
            console.error('[VideoRecorder] MediaRecorder error:', event);
            this.showError('Recording error: ' + event.error);
            
            if (this.onError) {
                this.onError('mediarecorder_error', event.error);
            }
        };
    }
    
    /**
     * Handle data available from MediaRecorder
     */
    handleDataAvailable(event) {
        if (event.data && event.data.size > 0) {
            console.log(`[VideoRecorder] Data received: ${event.data.size} bytes, type: ${event.data.type}`);
            
            // When MediaRecorder stops, it provides the complete recording
            const chunk = {
                data: event.data,
                number: this.chunkNumber++,
                timestamp: Date.now(),
                testSessionId: this.testSessionId
            };
            
            this.chunksRecorded++;
            
            if (this.chunksElement) {
                this.chunksElement.textContent = this.chunksRecorded;
            }
            
            // Add to upload queue
            this.uploadQueue.push(chunk);
            this.processUploadQueue();
        }
    }
    
    /**
     * Start chunk timer to create complete video files
     */
    startChunkTimer() {
        this.chunkInterval = setInterval(() => {
            if (this.isRecording && this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                console.log('[VideoRecorder] Creating chunk by restarting recorder...');
                
                // Stop current recording to get complete chunk
                this.mediaRecorder.stop();
                
                // Wait a bit for the stop event to process, then restart
                setTimeout(() => {
                    if (this.isRecording && this.mediaStream) {
                        try {
                            // Create new MediaRecorder for next chunk
                            const selectedMimeType = this.detectSupportedMimeType();
                            this.mediaRecorder = new MediaRecorder(this.mediaStream, {
                                mimeType: selectedMimeType,
                                videoBitsPerSecond: 1000000,
                                audioBitsPerSecond: 128000
                            });
                            
                            // Set up event handlers
                            this.setupMediaRecorderEvents();
                            
                            // Start recording next chunk
                            this.mediaRecorder.start();
                            console.log('[VideoRecorder] Started recording next chunk');
                        } catch (error) {
                            console.error('[VideoRecorder] Error restarting recorder:', error);
                            if (this.onError) {
                                this.onError('chunk_restart_failed', error);
                            }
                        }
                    }
                }, 100);
            }
        }, this.CHUNK_DURATION_MS);
    }
    
    /**
     * Process upload queue
     */
    async processUploadQueue() {
        if (this.uploadQueue.length === 0) return;
        
        const chunk = this.uploadQueue.shift();
        
        try {
            console.log(`[VideoRecorder] Uploading chunk ${chunk.number}...`);
            
            // Get presigned URL
            const presignedData = await this.getPresignedUrl(chunk.number, chunk.testSessionId);
            
            if (!presignedData) {
                throw new Error('Failed to get presigned URL');
            }
            
            // Upload to S3
            await this.uploadToS3(chunk.data, presignedData);
            
            this.chunksUploaded++;
            console.log(`[VideoRecorder] Chunk ${chunk.number} uploaded successfully`);
            
            // Trigger callback
            if (this.onChunkUploaded) {
                this.onChunkUploaded(chunk.number, this.chunksUploaded, chunk.testSessionId);
            }
            
            // Process next chunk if available
            if (this.uploadQueue.length > 0) {
                setTimeout(() => this.processUploadQueue(), 100);
            }
            
        } catch (error) {
            console.error(`[VideoRecorder] Upload error for chunk ${chunk.number}:`, error);
            
            // Retry after delay
            setTimeout(() => {
                this.uploadQueue.unshift(chunk);
                this.processUploadQueue();
            }, 5000);
            
            if (this.onError) {
                this.onError('upload_failed', error, chunk);
            }
        }
    }
    
    /**
     * Get presigned URL from server
     */
    async getPresignedUrl(chunkNumber, testSessionId = null) {
        try {
            const response = await fetch('/api/presigned-url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    chunk_number: chunkNumber,
                    test_session_id: testSessionId
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to get presigned URL');
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('[VideoRecorder] Error getting presigned URL:', error);
            return null;
        }
    }
    
    /**
     * Upload chunk to S3 using presigned URL
     */
    async uploadToS3(blob, presignedData) {
        // Debug blob info
        console.log(`[VideoRecorder] Uploading blob - size: ${blob.size} bytes, type: ${blob.type}`);
        
        if (blob.size === 0) {
            console.error('[VideoRecorder] WARNING: Attempting to upload empty blob!');
        }
        
        const formData = new FormData();
        
        // Add all fields from presigned data
        Object.entries(presignedData.fields).forEach(([key, value]) => {
            formData.append(key, value);
        });
        
        // Add file
        formData.append('file', blob, 'chunk.webm');
        
        const response = await fetch(presignedData.upload_url, {
            method: 'POST',
            body: formData,
            headers: {
                'Origin': window.location.origin
            }
        });
        
        if (!response.ok) {
            const responseText = await response.text();
            throw new Error(`S3 upload failed: ${response.status} - ${responseText}`);
        }
        
        return true;
    }
    
    /**
     * Generate unique session ID
     */
    generateSessionId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2, 9);
        return `video_session_${timestamp}_${random}`;
    }
    
    /**
     * Start duration timer
     */
    startDurationTimer() {
        this.durationInterval = setInterval(() => {
            if (!this.recordingStartTime) return;
            
            const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            if (this.durationElement) {
                this.durationElement.textContent = 
                    `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }
    
    /**
     * Update status display
     */
    updateStatus(status, type = 'info') {
        if (this.statusElement) {
            this.statusElement.textContent = status;
            this.statusElement.className = `status-value ${type}`;
        }
        
        console.log(`[VideoRecorder] Status: ${status}`);
    }
    
    /**
     * Show error message
     */
    showError(message) {
        console.error(`[VideoRecorder] Error: ${message}`);
        
        // You can implement custom error display here
        // For now, just log to console
    }
    
    /**
     * Get current recording state
     */
    getState() {
        return {
            isRecording: this.isRecording,
            sessionId: this.sessionId,
            testSessionId: this.testSessionId,
            chunksRecorded: this.chunksRecorded,
            chunksUploaded: this.chunksUploaded,
            recordingStartTime: this.recordingStartTime
        };
    }
    
    /**
     * Clean up resources
     */
    cleanup() {
        if (this.isRecording) {
            this.stopRecording();
        }
        
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        if (this.durationInterval) {
            clearInterval(this.durationInterval);
            this.durationInterval = null;
        }
        
        console.log('[VideoRecorder] Cleanup complete');
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VideoRecorder;
}

// Make available globally
window.VideoRecorder = VideoRecorder;