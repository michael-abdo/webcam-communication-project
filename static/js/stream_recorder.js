/**
 * Stream Recorder - Raw video/audio streaming to S3
 * Handles MediaRecorder, chunking, and S3 uploads
 */

// Global variables
let mediaStream = null;
let mediaRecorder = null;
let recordingStartTime = null;
let sessionId = null;
let participantId = null;
let chunkNumber = 0;
let chunksRecorded = 0;
let chunksUploaded = 0;
let uploadQueue = [];
let isRecording = false;
let durationInterval = null;
let lastChunkTimestamp = null;

let facilitatorIdInput = null;
let deviceKindInput = null;
let consentCheckbox = null;
let isCameraReady = false;

// Configuration
const CHUNK_DURATION_MS = 5000; // 5 seconds
const MIME_TYPE = 'video/webm;codecs=vp8,opus';

// Initialize on page load
window.addEventListener('DOMContentLoaded', async () => {
    facilitatorIdInput = document.getElementById('facilitatorIdInput');
    deviceKindInput = document.getElementById('deviceKindInput');
    consentCheckbox = document.getElementById('consentCheckbox');

    if (deviceKindInput && !deviceKindInput.value) {
        deviceKindInput.value = (navigator.userAgent || 'unknown-device').toLowerCase();
    }

    [facilitatorIdInput, deviceKindInput].forEach((input) => {
        if (input) {
            input.addEventListener('input', updateCaptureEligibility);
        }
    });

    if (consentCheckbox) {
        consentCheckbox.addEventListener('change', updateCaptureEligibility);
    }

    await initializeCamera();
    updateCaptureEligibility();
});

/**
 * Initialize camera and microphone access
 */
async function initializeCamera() {
    try {
        // Request camera and microphone permissions
        mediaStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });
        
        // Display video preview
        const videoElement = document.getElementById('videoPreview');
        videoElement.srcObject = mediaStream;
        
        isCameraReady = true;
        updateCaptureEligibility();

        updateStatus('Camera ready', 'info');
    } catch (error) {
        console.error('Error accessing camera:', error);
        showError('Failed to access camera/microphone. Please check permissions.');
        isCameraReady = false;
        updateCaptureEligibility();
    }
}

/**
 * Enable or disable recording controls based on readiness.
 */
function updateCaptureEligibility() {
    const recordBtn = document.getElementById('recordBtn');
    if (!recordBtn) return;

    const facilitatorReady = facilitatorIdInput && facilitatorIdInput.value.trim().length > 0;
    const consentGranted = consentCheckbox ? consentCheckbox.checked : false;
    const deviceReady = !!mediaStream && isCameraReady;

    recordBtn.disabled = !(facilitatorReady && consentGranted && deviceReady && !isRecording);
}

/**
 * Start recording
 */
async function startRecording() {
    if (!mediaStream) {
        showError('No media stream available');
        return;
    }
    if (!facilitatorIdInput || facilitatorIdInput.value.trim().length === 0) {
        showError('Facilitator ID is required before recording.');
        return;
    }
    if (!consentCheckbox || !consentCheckbox.checked) {
        showError('Facilitator consent must be confirmed before recording.');
        return;
    }
    
    try {
        // Reset state and register session
        sessionId = null;
        participantId = null;
        chunkNumber = 0;
        chunksRecorded = 0;
        chunksUploaded = 0;
        uploadQueue = [];
        document.getElementById('chunksRecorded').textContent = '0';
        document.getElementById('chunksUploaded').textContent = '0';
        document.getElementById('sessionId').textContent = '-';

        await ensureSessionRegistered();
        document.getElementById('sessionId').textContent = sessionId;
        
        // Check if MediaRecorder is supported
        if (!MediaRecorder.isTypeSupported(MIME_TYPE)) {
            showError('WebM recording not supported in this browser');
            return;
        }
        
        // Create MediaRecorder
        mediaRecorder = new MediaRecorder(mediaStream, {
            mimeType: MIME_TYPE,
            videoBitsPerSecond: 2500000 // 2.5 Mbps
        });
        
        // Handle data available event
        mediaRecorder.ondataavailable = handleDataAvailable;
        
        // Handle recording stop
        mediaRecorder.onstop = handleRecordingStop;
        
        // Handle errors
        mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event);
            showError('Recording error: ' + event.error);
        };
        
        // Start recording with chunking
        mediaRecorder.start();
        
        // Set up chunking timer
        setTimeout(requestChunk, CHUNK_DURATION_MS);
        
        // Update UI
        isRecording = true;
        recordingStartTime = Date.now();
        lastChunkTimestamp = recordingStartTime;
        updateCaptureEligibility();
        document.getElementById('stopBtn').disabled = false;
        document.getElementById('recordingStatus').textContent = 'Recording';
        document.getElementById('recordingStatus').classList.add('recording');
        document.getElementById('recordingStatus').classList.remove('stopped');
        
        // Start duration timer
        durationInterval = setInterval(updateDuration, 1000);
        
        updateStatus('Recording started', 'info');
        
    } catch (error) {
        console.error('Error starting recording:', error);
        showError('Failed to start recording: ' + error.message);
        isRecording = false;
        updateCaptureEligibility();
    }
}

/**
 * Create a capture session and register participant metadata.
 */
async function ensureSessionRegistered() {
    const facilitatorId = facilitatorIdInput.value.trim();
    const deviceKind = (deviceKindInput.value || navigator.userAgent || 'unknown-device').trim();
    const locale = navigator.language || 'en-US';
    const consentAt = new Date().toISOString();

    const sessionResponse = await fetch('/api/sessions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            facilitator_id: facilitatorId,
            consent_at: consentAt,
            device_kind: deviceKind,
            locale
        })
    });

    if (!sessionResponse.ok) {
        const errorBody = await sessionResponse.json().catch(() => ({}));
        throw new Error(errorBody.details || 'Unable to create capture session.');
    }

    const sessionData = await sessionResponse.json();
    sessionId = sessionData.id;

    const participantResponse = await fetch(`/api/sessions/${sessionId}/participants`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            device_id: deviceKind,
            status: 'ready',
            last_heartbeat_at: new Date().toISOString()
        })
    });

    if (participantResponse.ok) {
        const participantData = await participantResponse.json();
        participantId = participantData.id;
    } else {
        participantId = null;
        console.warn('Participant registration failed for session', sessionId);
    }
}

/**
 * Request data chunk from MediaRecorder
 */
function requestChunk() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.requestData();
        // Schedule next chunk
        setTimeout(requestChunk, CHUNK_DURATION_MS);
    }
}

/**
 * Handle data available from MediaRecorder
 */
function handleDataAvailable(event) {
    if (event.data && event.data.size > 0) {
        const now = Date.now();
        const durationMs = lastChunkTimestamp ? Math.max(1, now - lastChunkTimestamp) : CHUNK_DURATION_MS;
        lastChunkTimestamp = now;

        const chunk = {
            data: event.data,
            number: chunkNumber++,
            timestamp: now,
            durationMs
        };
        
        chunksRecorded++;
        document.getElementById('chunksRecorded').textContent = chunksRecorded;
        
        // Add to upload queue
        uploadQueue.push(chunk);
        processUploadQueue();
    }
}

/**
 * Process upload queue
 */
async function processUploadQueue() {
    if (uploadQueue.length === 0) return;
    
    const chunk = uploadQueue.shift();
    const uploadItem = addUploadItem(chunk.number);
    
    try {
        uploadItem.classList.add('upload-uploading');
        uploadItem.querySelector('.upload-status').textContent = 'Uploading...';
        
        // Get presigned URL
        const presignedData = await getPresignedUrl(chunk.number);
        
        if (!presignedData) {
            throw new Error('Failed to get presigned URL');
        }

        const checksum = await computeChunkChecksum(chunk.data);
        
        // Upload to S3
        await uploadToS3(chunk.data, presignedData);

        await recordChunkMetadata({
            sequenceNo: chunk.number,
            durationMs: chunk.durationMs || CHUNK_DURATION_MS,
            storageKey: presignedData.key,
            checksum
        });
        
        // Update success
        uploadItem.classList.remove('upload-uploading');
        uploadItem.classList.add('upload-success');
        uploadItem.querySelector('.upload-status').textContent = 'Uploaded';
        
        chunksUploaded++;
        document.getElementById('chunksUploaded').textContent = chunksUploaded;
        
        // Process next chunk if available
        if (uploadQueue.length > 0) {
            processUploadQueue();
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        uploadItem.classList.remove('upload-uploading');
        uploadItem.classList.add('upload-error');
        uploadItem.querySelector('.upload-status').textContent = 'Failed';
        
        // Retry after delay
        setTimeout(() => {
            uploadQueue.unshift(chunk);
            processUploadQueue();
        }, 5000);
    }
}

/**
 * Generate SHA-256 checksum for uploaded chunk.
 */
async function computeChunkChecksum(blob) {
    if (!window.crypto || !window.crypto.subtle) {
        return 'unavailable';
    }
    const buffer = await blob.arrayBuffer();
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Persist chunk metadata via capture API.
 */
async function recordChunkMetadata({ sequenceNo, durationMs, storageKey, checksum }) {
    if (!sessionId) {
        throw new Error('Session ID missing when recording chunk metadata.');
    }

    const response = await fetch(`/api/sessions/${sessionId}/chunks`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sequence_no: sequenceNo,
            duration_ms: durationMs,
            checksum: checksum || 'unavailable',
            storage_key: storageKey,
            participant_id: participantId || undefined,
            stored_at: new Date().toISOString()
        })
    });

    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.details || 'Failed to persist chunk metadata');
    }

    return response.json();
}

/**
 * Get presigned URL from server
 */
async function getPresignedUrl(chunkNumber) {
    if (!sessionId) {
        throw new Error('Session not initialized');
    }
    try {
        const response = await fetch('/api/presigned-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                chunk_number: chunkNumber
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get presigned URL');
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Error getting presigned URL:', error);
        return null;
    }
}

/**
 * Upload chunk to S3 using presigned URL
 */
async function uploadToS3(blob, presignedData) {
    const formData = new FormData();
    
    // Add all fields from presigned data
    Object.entries(presignedData.fields).forEach(([key, value]) => {
        formData.append(key, value);
    });
    
    // Add file last (important for S3)
    formData.append('file', blob, 'chunk.webm');
    
    const response = await fetch(presignedData.upload_url, {
        method: 'POST',
        body: formData,
        headers: {
            'Origin': window.location.origin
        }
    });
    
    if (!response.ok) {
        throw new Error(`S3 upload failed: ${response.status}`);
    }
    
    return true;
}

/**
 * Stop recording
 */
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        
        // Clear chunking timer
        isRecording = false;
        lastChunkTimestamp = null;
        
        // Update UI
        document.getElementById('stopBtn').disabled = true;
        document.getElementById('recordingStatus').textContent = 'Stopped';
        document.getElementById('recordingStatus').classList.remove('recording');
        document.getElementById('recordingStatus').classList.add('stopped');
        updateCaptureEligibility();
        
        // Stop duration timer
        if (durationInterval) {
            clearInterval(durationInterval);
            durationInterval = null;
        }
        
        updateStatus('Recording stopped. Finishing uploads...', 'info');
    }
}

/**
 * Handle recording stop event
 */
function handleRecordingStop() {
    // Final chunk will be handled by ondataavailable
    console.log('Recording stopped');
}

/**
 * Update recording duration display
 */
function updateDuration() {
    if (!recordingStartTime) return;
    
    const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    document.getElementById('duration').textContent = 
        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Add upload item to queue display
 */
function addUploadItem(chunkNumber) {
    const queueElement = document.getElementById('uploadQueue');
    
    // Clear initial message if present
    if (queueElement.querySelector('.info-message')) {
        queueElement.innerHTML = '';
    }
    
    const item = document.createElement('div');
    item.className = 'upload-item upload-pending';
    item.innerHTML = `
        <span>Chunk ${chunkNumber + 1}</span>
        <span class="upload-status">Pending</span>
    `;
    
    queueElement.appendChild(item);
    
    // Auto-scroll to bottom
    queueElement.scrollTop = queueElement.scrollHeight;
    
    return item;
}

/**
 * Update status message
 */
function updateStatus(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
}

/**
 * Show error message
 */
function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorContainer.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}
