#!/usr/bin/env python3
"""
Baseline Capture REST API

Provides FastAPI endpoints for baseline capture workflow:
- Session management and initialization  
- Face and speech baseline upload handling
- Real-time quality feedback and validation
- Baseline completion and results retrieval

Author: Baseline Capture System
Version: 1.0
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import json
import tempfile
import os
import uuid
from datetime import datetime

# Import our baseline capture modules
from baseline_capture.core import BaselineCapture
from baseline_capture.analysis import BaselineAnalyzer
from baseline_capture.storage import BaselineStorage


# Pydantic models for request/response validation
class BaselineStartRequest(BaseModel):
    """Request to start baseline capture session"""
    user_id: Optional[str] = Field(default=None, description="Optional user identifier")
    session_id: Optional[str] = Field(default=None, description="Optional existing session ID")


class BaselineStartResponse(BaseModel):
    """Response for baseline session start"""
    success: bool
    session_id: str
    user_id: str
    state: str
    upload_urls: Dict[str, Any]
    instructions: Dict[str, List[str]]
    error: Optional[str] = None


class BaselineStatusResponse(BaseModel):
    """Response for baseline session status"""
    success: bool
    session_id: str
    state: str
    progress: Dict[str, bool]
    quality_feedback: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaselineCompleteRequest(BaseModel):
    """Request to complete baseline capture"""
    session_id: str
    face_video_path: Optional[str] = None
    speech_audio_path: Optional[str] = None


class BaselineCompleteResponse(BaseModel):
    """Response for baseline completion"""
    success: bool
    session_id: str
    baseline_metrics: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None
    error: Optional[str] = None


# Global session storage (in production, use Redis or database)
active_sessions: Dict[str, BaselineCapture] = {}

# Create FastAPI router
baseline_router = APIRouter(prefix="/api/baseline", tags=["baseline"])

# Logger
logger = logging.getLogger(__name__)


@baseline_router.post("/start", response_model=BaselineStartResponse)
async def start_baseline_session(request: BaselineStartRequest) -> BaselineStartResponse:
    """
    Initialize a new baseline capture session.
    
    Creates a new baseline capture session with S3 upload URLs
    and provides instructions for face and speech capture.
    """
    try:
        logger.info(f"Starting baseline session for user: {request.user_id}")
        
        # Create baseline capture session
        baseline_session = BaselineCapture(
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Start the session
        result = baseline_session.start_session()
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Store session for later use
        session_id = result['session_id']
        active_sessions[session_id] = baseline_session
        
        # Return successful response
        return BaselineStartResponse(
            success=True,
            session_id=session_id,
            user_id=result['user_id'],
            state=result['state'],
            upload_urls=result['upload_urls'],
            instructions=result['instructions']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting baseline session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@baseline_router.post("/face")
async def upload_face_baseline(
    session_id: str = Form(...),
    duration: Optional[float] = Form(10.0),
    face_video: UploadFile = File(...)
) -> JSONResponse:
    """
    Handle face baseline video upload and processing.
    
    Receives face baseline video, validates quality, and processes
    for baseline metric extraction.
    """
    try:
        logger.info(f"Processing face baseline upload for session: {session_id}")
        
        # Get active session
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        baseline_session = active_sessions[session_id]
        
        # Validate file type
        if not face_video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="Invalid file type. Expected video file.")
        
        # Save uploaded video to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await face_video.read()
            temp_file.write(content)
            temp_video_path = temp_file.name
        
        try:
            # Process face baseline
            result = baseline_session.capture_face_baseline(
                video_path=temp_video_path,
                duration=duration
            )
            
            response_data = {
                'success': result.success,
                'session_id': result.session_id,
                'capture_type': result.capture_type,
                'duration_seconds': result.duration_seconds,
                'quality_score': result.quality_score,
                'retry_needed': result.retry_needed
            }
            
            if result.error_message:
                response_data['error'] = result.error_message
            
            if result.capture_data:
                response_data['capture_data'] = result.capture_data
            
            logger.info(f"Face baseline processed: {result.quality_score:.2f} quality")
            return JSONResponse(content=response_data)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_video_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing face baseline: {e}")
        raise HTTPException(status_code=500, detail=f"Face processing failed: {str(e)}")


@baseline_router.post("/speech")
async def upload_speech_baseline(
    session_id: str = Form(...),
    duration: Optional[float] = Form(15.0),
    speech_audio: UploadFile = File(...)
) -> JSONResponse:
    """
    Handle speech baseline audio upload and processing.
    
    Receives speech baseline audio, validates quality, and processes
    for baseline metric extraction.
    """
    try:
        logger.info(f"Processing speech baseline upload for session: {session_id}")
        
        # Get active session
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        baseline_session = active_sessions[session_id]
        
        # Validate file type
        if not (speech_audio.content_type.startswith('audio/') or 
                speech_audio.content_type.startswith('video/')):
            raise HTTPException(status_code=400, detail="Invalid file type. Expected audio or video file.")
        
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await speech_audio.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        try:
            # Process speech baseline
            result = baseline_session.capture_speech_baseline(
                audio_path=temp_audio_path,
                duration=duration
            )
            
            response_data = {
                'success': result.success,
                'session_id': result.session_id,
                'capture_type': result.capture_type,
                'duration_seconds': result.duration_seconds,
                'quality_score': result.quality_score,
                'retry_needed': result.retry_needed
            }
            
            if result.error_message:
                response_data['error'] = result.error_message
            
            if result.capture_data:
                response_data['capture_data'] = result.capture_data
            
            logger.info(f"Speech baseline processed: {result.quality_score:.1f} quality")
            return JSONResponse(content=response_data)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_audio_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing speech baseline: {e}")
        raise HTTPException(status_code=500, detail=f"Speech processing failed: {str(e)}")


@baseline_router.get("/status/{session_id}", response_model=BaselineStatusResponse)
async def get_baseline_status(session_id: str) -> BaselineStatusResponse:
    """
    Get real-time status and quality feedback for baseline capture session.
    
    Returns current session state, progress, and quality metrics
    for real-time UI feedback.
    """
    try:
        # Get active session
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        baseline_session = active_sessions[session_id]
        
        # Get session status
        status = baseline_session.get_session_status()
        
        # Generate quality feedback if available
        quality_feedback = None
        if hasattr(baseline_session, 'quality_validator'):
            # Get latest quality validation results
            quality_feedback = {
                'face_quality_checks': len(baseline_session.quality_validator.face_quality_history),
                'audio_quality_checks': len(baseline_session.quality_validator.audio_quality_history),
                'recommendations': baseline_session.quality_validator._generate_recommendations(
                    status['progress']['face_complete'],
                    status['progress']['speech_complete']
                )
            }
        
        return BaselineStatusResponse(
            success=True,
            session_id=session_id,
            state=status['state'],
            progress=status['progress'],
            quality_feedback=quality_feedback
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting baseline status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@baseline_router.post("/complete", response_model=BaselineCompleteResponse)
async def complete_baseline_capture(request: BaselineCompleteRequest) -> BaselineCompleteResponse:
    """
    Complete baseline capture and generate final baseline metrics.
    
    Analyzes captured face and speech data to create personalized
    baseline metrics for assessment use.
    """
    try:
        logger.info(f"Completing baseline capture for session: {request.session_id}")
        
        # Get active session
        if request.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        baseline_session = active_sessions[request.session_id]
        
        # Check session is ready for completion
        status = baseline_session.get_session_status()
        if not status['progress']['ready_for_processing']:
            raise HTTPException(
                status_code=400, 
                detail=f"Session not ready for completion. Current state: {status['state']}"
            )
        
        # Initialize analyzer for final processing
        analyzer = BaselineAnalyzer(session_id=request.session_id)
        
        # Analyze face baseline if available
        face_data = {}
        if request.face_video_path and os.path.exists(request.face_video_path):
            face_data = analyzer.analyze_face_baseline(request.face_video_path)
        elif baseline_session.face_capture_attempts:
            # Use data from successful face capture attempt
            successful_attempt = next(
                (attempt for attempt in baseline_session.face_capture_attempts 
                 if attempt.get('quality_passed', False)), 
                None
            )
            if successful_attempt and successful_attempt.get('video_path'):
                face_data = analyzer.analyze_face_baseline(successful_attempt['video_path'])
        
        # Analyze speech baseline if available
        speech_data = {}
        if request.speech_audio_path and os.path.exists(request.speech_audio_path):
            speech_data = analyzer.analyze_speech_baseline(request.speech_audio_path)
        elif baseline_session.speech_capture_attempts:
            # Use data from successful speech capture attempt
            successful_attempt = next(
                (attempt for attempt in baseline_session.speech_capture_attempts 
                 if attempt.get('quality_passed', False)), 
                None
            )
            if successful_attempt and successful_attempt.get('audio_path'):
                speech_data = analyzer.analyze_speech_baseline(successful_attempt['audio_path'])
        
        # Compile final baseline metrics
        if face_data or speech_data:
            baseline_metrics = analyzer.compile_baseline_metrics(
                face_data or {'analysis_method': 'unavailable'},
                speech_data or {'analysis_method': 'unavailable'}
            )
            
            # Store baseline metrics
            storage_result = baseline_session.baseline_storage.store_baseline_metrics(
                request.session_id,
                baseline_metrics.__dict__
            )
            
            if not storage_result:
                logger.warning(f"Failed to store baseline metrics for session: {request.session_id}")
            
            # Update session state
            baseline_session.state = baseline_session.BaselineSessionState.COMPLETED
            
            response = BaselineCompleteResponse(
                success=True,
                session_id=request.session_id,
                baseline_metrics=baseline_metrics.__dict__,
                quality_score=baseline_metrics.overall_quality['overall_quality']
            )
            
            logger.info(f"Baseline capture completed successfully: {baseline_metrics.overall_quality['overall_quality']:.2f} quality")
            return response
            
        else:
            raise HTTPException(status_code=400, detail="No baseline data available for analysis")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing baseline capture: {e}")
        raise HTTPException(status_code=500, detail=f"Baseline completion failed: {str(e)}")


@baseline_router.get("/results/{session_id}")
async def get_baseline_results(session_id: str) -> JSONResponse:
    """
    Retrieve stored baseline metrics for a session.
    
    Returns previously computed baseline metrics for use in assessments.
    """
    try:
        logger.info(f"Retrieving baseline results for session: {session_id}")
        
        # Initialize storage handler
        storage = BaselineStorage()
        
        # Load baseline metrics
        baseline_data = storage.load_baseline_metrics(session_id)
        
        if not baseline_data:
            raise HTTPException(status_code=404, detail="No baseline results found for session")
        
        return JSONResponse(content={
            'success': True,
            'session_id': session_id,
            'baseline_data': baseline_data,
            'retrieved_at': datetime.now().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving baseline results: {e}")
        raise HTTPException(status_code=500, detail=f"Results retrieval failed: {str(e)}")


@baseline_router.delete("/session/{session_id}")
async def cleanup_baseline_session(session_id: str) -> JSONResponse:
    """
    Clean up baseline capture session and free resources.
    
    Removes session from active sessions and cleans up temporary files.
    """
    try:
        logger.info(f"Cleaning up baseline session: {session_id}")
        
        # Remove from active sessions
        if session_id in active_sessions:
            baseline_session = active_sessions[session_id]
            baseline_session.cleanup_session()
            del active_sessions[session_id]
        
        return JSONResponse(content={
            'success': True,
            'session_id': session_id,
            'message': 'Session cleaned up successfully'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up session: {e}")
        raise HTTPException(status_code=500, detail=f"Session cleanup failed: {str(e)}")


# Add CORS middleware support for baseline endpoints
def add_baseline_cors(app):
    """
    Add CORS configuration for baseline capture endpoints.
    
    Allows frontend to communicate with baseline API endpoints.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )


# Health check endpoint
@baseline_router.get("/health")
async def baseline_health_check() -> JSONResponse:
    """Health check endpoint for baseline capture API."""
    return JSONResponse(content={
        'status': 'healthy',
        'service': 'baseline_capture',
        'active_sessions': len(active_sessions),
        'timestamp': datetime.now().isoformat()
    })


# Error handlers
@baseline_router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content={'success': False, 'error': f'Validation error: {str(exc)}'}
    )


@baseline_router.exception_handler(FileNotFoundError)  
async def file_not_found_handler(request, exc):
    """Handle file not found errors."""
    return JSONResponse(
        status_code=404,
        content={'success': False, 'error': f'File not found: {str(exc)}'}
    )