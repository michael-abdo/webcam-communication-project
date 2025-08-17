"""Main pipeline orchestrator for Behavioral Signals processing"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys
import re

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.pipeline.config import Config
from src.api.client import BehavioralSignalsClient, Monitor
from src.analysis.create_report import create_behavior_report

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the complete processing pipeline using shared processed files"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize pipeline with configuration
        
        Args:
            config_path: Path to configuration file
        """
        self.config = Config(config_path)
        
        # Initialize API client
        api_config = self.config.api
        self.api_client = BehavioralSignalsClient(
            api_key=api_config['key'],
            client_id=api_config['client_id'],
            base_url=api_config['base_url']
        )
        
        self.jobs_dir = self.config.get_path('jobs')
        
        # Shared data directory paths
        self.shared_converted = self.config.get_path('shared_converted')
        self.shared_samples = self.config.get_path('shared_samples')
        self.shared_chunks = self.config.get_path('shared_chunks')
        
    def create_job(self, url: str) -> Dict[str, Any]:
        """Create a new job for tracking
        
        Args:
            url: YouTube URL to process
            
        Returns:
            Job dictionary
        """
        job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        job = {
            'id': job_id,
            'url': url,
            'status': 'created',
            'created_at': datetime.now().isoformat(),
            'video_path': None,
            'audio_path': None,
            'process_id': None,
            'result_path': None,
            'report_path': None,
            'error': None
        }
        
        # Save job file
        job_path = self.jobs_dir / f"job_{job_id}.json"
        with open(job_path, 'w') as f:
            json.dump(job, f, indent=2)
        
        return job
    
    def update_job(self, job: Dict[str, Any], **kwargs):
        """Update job status and save
        
        Args:
            job: Job dictionary
            **kwargs: Fields to update
        """
        job.update(kwargs)
        job['updated_at'] = datetime.now().isoformat()
        
        job_path = self.jobs_dir / f"job_{job['id']}.json"
        with open(job_path, 'w') as f:
            json.dump(job, f, indent=2)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID or None if not found
        """
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def find_shared_files(self, video_id: str) -> Dict[str, List[str]]:
        """Find processed files for a video ID in shared directories
        
        Args:
            video_id: YouTube video ID to search for
            
        Returns:
            Dictionary with found files by type
        """
        found_files = {
            'converted': [],
            'samples': [],
            'chunks': []
        }
        
        # Search in converted audio directory
        if self.shared_converted.exists():
            converted_files = list(self.shared_converted.glob(f"{video_id}*.mp3"))
            found_files['converted'] = [str(f) for f in sorted(converted_files)]
        
        # Search in samples directory
        if self.shared_samples.exists():
            sample_files = list(self.shared_samples.glob(f"{video_id}*.mp3"))
            found_files['samples'] = [str(f) for f in sorted(sample_files)]
        
        # Search in chunks directory
        if self.shared_chunks.exists():
            chunk_files = list(self.shared_chunks.glob(f"{video_id}*chunk*.mp3"))
            found_files['chunks'] = [str(f) for f in sorted(chunk_files)]
        
        return found_files
    
    def process_url(
        self,
        url: str,
        prefer_chunks: bool = False,
        report: bool = True
    ) -> Dict[str, Any]:
        """Process a YouTube URL by using shared processed files
        
        Args:
            url: YouTube URL to process
            prefer_chunks: Whether to prefer chunk files over single files
            report: Whether to generate a report
            
        Returns:
            Job dictionary with results
        """
        # Extract video ID
        video_id = self.extract_video_id(url)
        if not video_id:
            return {
                'id': 'error',
                'status': 'error',
                'error': 'Invalid YouTube URL - could not extract video ID',
                'url': url
            }
        
        # Create job for tracking
        job = self.create_job(url)
        logger.info(f"Created job {job['id']} for URL: {url} (video ID: {video_id})")
        
        try:
            # Step 1: Find shared processed files
            self.update_job(job, status='scanning_shared_files')
            shared_files = self.find_shared_files(video_id)
            
            # Determine which files to use
            audio_files = []
            enable_chunking = False
            
            if prefer_chunks and shared_files['chunks']:
                audio_files = shared_files['chunks']
                enable_chunking = True
                logger.info(f"Using {len(audio_files)} chunk files for processing")
            elif shared_files['converted']:
                audio_files = shared_files['converted']
                logger.info(f"Using {len(audio_files)} converted audio files for processing")
            elif shared_files['samples']:
                audio_files = shared_files['samples']
                logger.info(f"Using {len(audio_files)} sample files for processing")
            elif shared_files['chunks']:
                # Fall back to chunks if no other files found
                audio_files = shared_files['chunks']
                enable_chunking = True
                logger.info(f"Falling back to {len(audio_files)} chunk files for processing")
            else:
                self.update_job(job, status='error', error=f"No processed files found for video ID: {video_id}")
                logger.error(f"No processed files found for video ID: {video_id}. Please run shared processing first.")
                logger.error(f"  Run: python ../../../shared_processing/scripts/process_media.py \"{url}\"")
                return job
            
            # Update job with found files
            if enable_chunking:
                self.update_job(job, audio_paths=audio_files, chunk_count=len(audio_files))
            else:
                self.update_job(job, audio_path=audio_files[0] if audio_files else None)
            
            logger.info(f"Found shared processed files for video {video_id}")
            
            # Step 2: Process files through API (no audio processing needed - already done by shared processing)
            if enable_chunking:
                # Process multiple chunk files through the API
                process_ids = []
                result_paths = []
                
                for i, audio_path in enumerate(audio_files, 1):
                    logger.info(f"Processing chunk {i}/{len(audio_files)}: {Path(audio_path).name}")
                    
                    # Step 3a: Submit chunk to API
                    self.update_job(job, status=f'submitting_chunk_{i}_to_api')
                    result = self.api_client.submit_file(audio_path)
                    
                    if not result.success:
                        self.update_job(job, status='error', error=f"API submission failed for chunk {i}: {result.error}")
                        logger.error(f"API submission failed for chunk {i}: {result.error}")
                        return job
                    
                    process_id = result.process_id
                    process_ids.append(process_id)
                    logger.info(f"Submitted chunk {i} to API, process ID: {process_id}")
                    
                    # Step 4a: Monitor chunk processing
                    self.update_job(job, status=f'monitoring_chunk_{i}')
                    monitor = Monitor(
                        self.api_client,
                        check_interval=self.config.timeouts['api_check_interval']
                    )
                    
                    final_status = monitor.wait_for_completion(
                        process_id,
                        max_wait=self.config.timeouts['max_wait']
                    )
                    
                    if final_status != 2:  # Not complete
                        self.update_job(job, status='error', error=f"Processing failed for chunk {i} with status: {final_status}")
                        logger.error(f"Processing failed for chunk {i} with status: {final_status}")
                        return job
                    
                    # Step 5a: Get chunk results
                    success, results, error = self.api_client.get_results(process_id)
                    
                    if not success:
                        self.update_job(job, status='error', error=f"Failed to retrieve results for chunk {i}: {error}")
                        logger.error(f"Failed to retrieve results for chunk {i}: {error}")
                        return job
                    
                    # Save chunk results
                    result_path = self.config.get_path('results') / f"process_{process_id}_chunk_{i}_results.json"
                    with open(result_path, 'w') as f:
                        json.dump(results, f, indent=2)
                    
                    result_paths.append(str(result_path))
                    logger.info(f"Saved chunk {i} results: {result_path}")
                
                # Update job with all chunk data
                self.update_job(job, 
                              process_ids=process_ids, 
                              result_paths=result_paths,
                              status='retrieving_results')
                
                logger.info(f"Completed processing all {len(audio_files)} chunks")
                
            else:
                # Single file processing
                audio_path = audio_files[0]
                logger.info(f"Processing single audio file: {Path(audio_path).name}")
                
                # Step 3: Submit to API
                self.update_job(job, status='submitting_to_api')
                result = self.api_client.submit_file(audio_path)
                
                if not result.success:
                    self.update_job(job, status='error', error=f"API submission failed: {result.error}")
                    logger.error(f"API submission failed: {result.error}")
                    return job
                
                process_id = result.process_id
                self.update_job(job, process_id=process_id)
                logger.info(f"Submitted to API, process ID: {process_id}")
                
                # Step 4: Monitor processing
                self.update_job(job, status='monitoring_api')
                monitor = Monitor(
                    self.api_client,
                    check_interval=self.config.timeouts['api_check_interval']
                )
                
                final_status = monitor.wait_for_completion(
                    process_id,
                    max_wait=self.config.timeouts['max_wait']
                )
                
                if final_status != 2:  # Not complete
                    self.update_job(job, status='error', error=f"Processing failed with status: {final_status}")
                    logger.error(f"Processing failed with status: {final_status}")
                    return job
                
                # Step 5: Get results
                self.update_job(job, status='retrieving_results')
                success, results, error = self.api_client.get_results(process_id)
                
                if not success:
                    self.update_job(job, status='error', error=f"Failed to retrieve results: {error}")
                    logger.error(f"Failed to retrieve results: {error}")
                    return job
                
                # Save results
                result_path = self.config.get_path('results') / f"process_{process_id}_results.json"
                with open(result_path, 'w') as f:
                    json.dump(results, f, indent=2)
                
                self.update_job(job, result_path=str(result_path))
                logger.info(f"Saved results: {result_path}")
            
            # Step 6: Generate report (optional)
            if report:
                self.update_job(job, status='generating_report')
                
                if enable_chunking:
                    # For chunks, use the first result file for basic report
                    # TODO: Could implement aggregated reporting across chunks
                    report_path = self.config.get_path('reports') / f"report_chunks_{job['id']}.txt"
                    create_behavior_report(
                        result_paths[0],  # Use first chunk for now
                        str(report_path)
                    )
                else:
                    report_path = self.config.get_path('reports') / f"report_{process_id}.txt"
                    create_behavior_report(
                        str(result_path),
                        str(report_path)
                    )
                
                self.update_job(job, report_path=str(report_path))
                logger.info(f"Generated report: {report_path}")
            
            # Complete!
            self.update_job(job, status='completed')
            logger.info(f"Job {job['id']} completed successfully")
            
            return job
            
        except Exception as e:
            self.update_job(job, status='error', error=str(e))
            logger.error(f"Pipeline error: {str(e)}")
            return job
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed
        
        Returns:
            True if all dependencies are available
        """
        # Only need to check API client dependencies now
        # Media processing dependencies are handled by shared processing
        logger.info("Checking API client dependencies...")
        
        # Check if shared processing directories are accessible
        deps_ok = True
        
        try:
            # Try to access shared directories
            self.shared_converted.parent.mkdir(parents=True, exist_ok=True)
            self.shared_samples.parent.mkdir(parents=True, exist_ok=True) 
            self.shared_chunks.parent.mkdir(parents=True, exist_ok=True)
            logger.info("Shared processing directories are accessible")
        except Exception as e:
            logger.error(f"Cannot access shared processing directories: {str(e)}")
            deps_ok = False
        
        return deps_ok
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a job
        
        Args:
            job_id: Job ID to check
            
        Returns:
            Job dictionary or None if not found
        """
        job_path = self.jobs_dir / f"job_{job_id}.json"
        
        if not job_path.exists():
            return None
        
        with open(job_path, 'r') as f:
            return json.load(f)
    
    def list_available_files(self, video_id: str) -> Dict[str, List[str]]:
        """List all available processed files for a video ID
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with available files by type
        """
        return self.find_shared_files(video_id)