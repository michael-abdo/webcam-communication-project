/**
 * Stream Recorder - Raw video/audio streaming to S3
 * Handles MediaRecorder, chunking, and S3 uploads
 */

// Global variables
let mediaStream = null;
let mediaRecorder = null;
let recordingStartTime = null;
let sessionId = null;
let chunkNumber = 0;
let chunksRecorded = 0;
let chunksUploaded = 0;
let uploadQueue = [];
let isRecording = false;
let durationInterval = null;

// Configuration
const CHUNK_DURATION_MS = 5000; // 5 seconds
const MIME_TYPE = 'video/webm;codecs=vp8,opus';

// Initialize on page load
window.addEventListener('DOMContentLoaded', async () => {
    await initializeCamera();
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
        
        // Enable record button
        document.getElementById('recordBtn').disabled = false;
        
        updateStatus('Camera ready', 'info');
    } catch (error) {
        console.error('Error accessing camera:', error);
        showError('Failed to access camera/microphone. Please check permissions.');
        document.getElementById('recordBtn').disabled = true;
    }
}

/**
 * Start recording
 */
async function startRecording() {
    if (!mediaStream) {
        showError('No media stream available');
        return;
    }
    
    try {
        // Generate new session ID
        sessionId = generateSessionId();
        document.getElementById('sessionId').textContent = sessionId;
        
        // Reset counters
        chunkNumber = 0;
        chunksRecorded = 0;
        chunksUploaded = 0;
        uploadQueue = [];
        
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
        document.getElementById('recordBtn').disabled = true;
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
        const chunk = {
            data: event.data,
            number: chunkNumber++,
            timestamp: Date.now()
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
        
        // Upload to S3
        await uploadToS3(chunk.data, presignedData);
        
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
 * Get presigned URL from server
 */
async function getPresignedUrl(chunkNumber) {
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
        
        // Update UI
        document.getElementById('recordBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        document.getElementById('recordingStatus').textContent = 'Stopped';
        document.getElementById('recordingStatus').classList.remove('recording');
        document.getElementById('recordingStatus').classList.add('stopped');
        
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
 * Generate unique session ID
 */
function generateSessionId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 9);
    return `session_${timestamp}_${random}`;
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