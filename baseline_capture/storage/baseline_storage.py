#!/usr/bin/env python3
"""
Baseline Storage Handler

Extends existing S3 infrastructure for baseline capture data storage.
Handles both baseline media files and extracted metrics according to SOP requirements.

Author: Baseline Capture System
Version: 1.0
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import sys
import logging

# Add streaming directory to path to import existing S3 handler
sys.path.append(os.path.join(os.path.dirname(__file__), '../../streaming'))
from s3_handler import get_s3_client, S3_BUCKET
from botocore.exceptions import ClientError


class BaselineStorage:
    """
    Handles storage for baseline capture data including:
    - S3 storage for baseline video/audio files
    - Local JSON storage for baseline metrics
    - Session correlation with assessment data
    """
    
    def __init__(self, base_results_path: str = None):
        """
        Initialize baseline storage handler.
        
        Args:
            base_results_path (str): Base directory for local results storage
        """
        # Use existing assessments results structure
        if base_results_path is None:
            self.base_results_path = os.path.join(
                os.path.dirname(__file__), 
                '../../assessments/results/baseline'
            )
        else:
            self.base_results_path = base_results_path
        
        # Ensure results directory exists
        os.makedirs(self.base_results_path, exist_ok=True)
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    def generate_baseline_upload_urls(self, session_id: str) -> Dict[str, Any]:
        """
        Generate presigned URLs for baseline capture uploads.
        
        Creates separate upload URLs for:
        - 10s neutral face baseline video
        - 15s speech calibration video
        
        Args:
            session_id (str): Unique session identifier
            
        Returns:
            Dict with presigned URLs for face and speech baseline uploads
        """
        try:
            s3_client = get_s3_client()
            
            # Create timestamp for organizing files
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # S3 key structure for baseline data
            base_key = f"baseline/{session_id}/{timestamp}"
            
            # Generate URLs for both baseline components
            face_baseline_key = f"{base_key}_face_neutral.webm"
            speech_baseline_key = f"{base_key}_speech_calibration.webm"
            
            # Face baseline upload URL (10 seconds max)
            face_upload_response = s3_client.generate_presigned_post(
                Bucket=S3_BUCKET,
                Key=face_baseline_key,
                ExpiresIn=600,  # 10 minutes to complete baseline
                Conditions=[
                    {'content-type': 'video/webm;codecs=vp8,opus'},
                    ['content-length-range', 0, 20 * 1024 * 1024]  # Max 20MB for 10s
                ]
            )
            face_upload_response['fields']['Content-Type'] = 'video/webm;codecs=vp8,opus'
            face_upload_response['key'] = face_baseline_key
            
            # Speech baseline upload URL (15 seconds max)
            speech_upload_response = s3_client.generate_presigned_post(
                Bucket=S3_BUCKET,
                Key=speech_baseline_key,
                ExpiresIn=600,  # 10 minutes to complete baseline
                Conditions=[
                    {'content-type': 'video/webm;codecs=vp8,opus'},
                    ['content-length-range', 0, 30 * 1024 * 1024]  # Max 30MB for 15s
                ]
            )
            speech_upload_response['fields']['Content-Type'] = 'video/webm;codecs=vp8,opus'
            speech_upload_response['key'] = speech_baseline_key
            
            return {
                'session_id': session_id,
                'timestamp': timestamp,
                'face_baseline': {
                    'upload_url': face_upload_response['url'],
                    'fields': face_upload_response['fields'],
                    's3_key': face_baseline_key,
                    'expected_duration': 10,
                    'content_type': 'face_neutral'
                },
                'speech_baseline': {
                    'upload_url': speech_upload_response['url'],
                    'fields': speech_upload_response['fields'],
                    's3_key': speech_baseline_key,
                    'expected_duration': 15,
                    'content_type': 'speech_calibration'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating baseline upload URLs: {e}")
            return {'error': str(e)}
    
    def store_baseline_metrics(self, session_id: str, baseline_data: Dict[str, Any]) -> bool:
        """
        Store baseline metrics and quality validation results locally.
        
        Args:
            session_id (str): Session identifier
            baseline_data (Dict): Processed baseline metrics
            
        Returns:
            bool: True if storage successful
        """
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{session_id}_{timestamp}_baseline_metrics.json"
            file_path = os.path.join(self.base_results_path, filename)
            
            # Add storage metadata
            storage_data = {
                'session_id': session_id,
                'stored_at': datetime.now().isoformat(),
                'storage_version': '1.0',
                'baseline_data': baseline_data
            }
            
            # Write to JSON file
            with open(file_path, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            
            self.logger.info(f"Baseline metrics stored: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing baseline metrics: {e}")
            return False
    
    def load_baseline_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load baseline metrics for a session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Dict with baseline data or None if not found
        """
        try:
            # Find the most recent baseline file for this session
            baseline_files = []
            for filename in os.listdir(self.base_results_path):
                if filename.startswith(session_id) and filename.endswith('_baseline_metrics.json'):
                    file_path = os.path.join(self.base_results_path, filename)
                    baseline_files.append(file_path)
            
            if not baseline_files:
                return None
            
            # Load the most recent file (they include timestamps)
            most_recent_file = sorted(baseline_files)[-1]
            
            with open(most_recent_file, 'r') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading baseline metrics: {e}")
            return None
    
    def get_baseline_download_urls(self, session_id: str, timestamp: str = None) -> Dict[str, Any]:
        """
        Generate download URLs for baseline media files.
        
        Args:
            session_id (str): Session identifier
            timestamp (str): Specific timestamp (optional)
            
        Returns:
            Dict with download URLs for baseline files
        """
        try:
            s3_client = get_s3_client()
            
            # If no timestamp provided, find the most recent baseline for this session
            if not timestamp:
                timestamp = self._find_latest_baseline_timestamp(session_id)
                if not timestamp:
                    return {'error': 'No baseline found for session'}
            
            # Construct S3 keys
            base_key = f"baseline/{session_id}/{timestamp}"
            face_key = f"{base_key}_face_neutral.webm"
            speech_key = f"{base_key}_speech_calibration.webm"
            
            # Generate download URLs
            # Generate presigned URLs for download
            s3_client = get_s3_client()
            face_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': face_key},
                ExpiresIn=3600  # 1 hour
            )
            speech_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': speech_key},
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                'session_id': session_id,
                'timestamp': timestamp,
                'face_baseline_url': face_url,
                'speech_baseline_url': speech_url,
                'expiration_seconds': 3600
            }
            
        except Exception as e:
            self.logger.error(f"Error generating baseline download URLs: {e}")
            return {'error': str(e)}
    
    def delete_baseline_data(self, session_id: str, delete_raw_media: bool = True, delete_metrics: bool = False) -> Dict[str, Any]:
        """
        Delete baseline data according to privacy requirements.
        
        SOP specifies:
        - Immediate deletion of raw media available
        - 24-hour window to delete derived features
        
        Args:
            session_id (str): Session identifier
            delete_raw_media (bool): Delete S3 video files
            delete_metrics (bool): Delete local metrics
            
        Returns:
            Dict with deletion results
        """
        try:
            results = {
                'session_id': session_id,
                'deleted_raw_media': False,
                'deleted_metrics': False,
                'errors': []
            }
            
            if delete_raw_media:
                # Delete S3 baseline files
                try:
                    s3_client = get_s3_client()
                    
                    # Find all baseline files for this session
                    response = s3_client.list_objects_v2(
                        Bucket=S3_BUCKET,
                        Prefix=f"baseline/{session_id}/"
                    )
                    
                    if 'Contents' in response:
                        # Delete all found objects
                        objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                        
                        s3_client.delete_objects(
                            Bucket=S3_BUCKET,
                            Delete={'Objects': objects_to_delete}
                        )
                        
                        results['deleted_raw_media'] = True
                        results['deleted_files'] = len(objects_to_delete)
                        
                except Exception as e:
                    results['errors'].append(f"S3 deletion error: {e}")
            
            if delete_metrics:
                # Delete local baseline metrics
                try:
                    for filename in os.listdir(self.base_results_path):
                        if filename.startswith(session_id) and filename.endswith('_baseline_metrics.json'):
                            file_path = os.path.join(self.base_results_path, filename)
                            os.remove(file_path)
                    
                    results['deleted_metrics'] = True
                    
                except Exception as e:
                    results['errors'].append(f"Local metrics deletion error: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error deleting baseline data: {e}")
            return {'error': str(e)}
    
    def list_user_baselines(self, user_id: str = None) -> List[Dict[str, Any]]:
        """
        List available baselines for a user or all baselines.
        
        Args:
            user_id (str): Optional user identifier filter
            
        Returns:
            List of baseline information dictionaries
        """
        try:
            baselines = []
            
            # Scan local baseline metrics files
            for filename in os.listdir(self.base_results_path):
                if filename.endswith('_baseline_metrics.json'):
                    file_path = os.path.join(self.base_results_path, filename)
                    
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Extract session info
                        session_id = data.get('session_id', 'unknown')
                        stored_at = data.get('stored_at', 'unknown')
                        
                        # Basic filtering by user if provided
                        if user_id and user_id not in session_id:
                            continue
                        
                        baseline_info = {
                            'session_id': session_id,
                            'stored_at': stored_at,
                            'file_path': file_path,
                            'has_face_data': 'face_validation' in data.get('baseline_data', {}),
                            'has_audio_data': 'audio_validation' in data.get('baseline_data', {}),
                        }
                        
                        baselines.append(baseline_info)
                        
                    except Exception as e:
                        self.logger.warning(f"Error reading baseline file {filename}: {e}")
            
            # Sort by storage date (most recent first)
            baselines.sort(key=lambda x: x['stored_at'], reverse=True)
            
            return baselines
            
        except Exception as e:
            self.logger.error(f"Error listing baselines: {e}")
            return []
    
    def _find_latest_baseline_timestamp(self, session_id: str) -> Optional[str]:
        """
        Find the latest baseline timestamp for a session by querying S3.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            str: Latest timestamp or None if not found
        """
        try:
            s3_client = get_s3_client()
            
            response = s3_client.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=f"baseline/{session_id}/",
                MaxKeys=100
            )
            
            if 'Contents' not in response:
                return None
            
            # Extract timestamps from object keys
            timestamps = []
            for obj in response['Contents']:
                key = obj['Key']
                # Extract timestamp from key like: baseline/session_id/20241108_143055_face_neutral.webm
                parts = key.split('/')
                if len(parts) >= 3:
                    filename = parts[2]  # e.g., "20241108_143055_face_neutral.webm"
                    timestamp_part = filename.split('_')[:2]  # ["20241108", "143055"]
                    if len(timestamp_part) == 2:
                        timestamp = f"{timestamp_part[0]}_{timestamp_part[1]}"
                        timestamps.append(timestamp)
            
            # Return the most recent timestamp
            return sorted(timestamps)[-1] if timestamps else None
            
        except Exception as e:
            self.logger.error(f"Error finding latest baseline timestamp: {e}")
            return None