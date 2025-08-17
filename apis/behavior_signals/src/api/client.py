#!/usr/bin/env python3
"""
Unified Behavioral Signals API Client

This module consolidates all API functionality from monitor_api.py,
monitor_and_notify.py, and quick_test.py into a single reusable client.
"""

import requests
import time
import os
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ProcessStatus(Enum):
    """Process status codes from API"""
    PENDING = 0
    PROCESSING = 1
    COMPLETE = 2
    ERROR_GENERAL = -1
    ERROR_PROCESSING = -2
    ERROR_SYSTEM = -3


@dataclass
class ProcessResult:
    """Result from submitting a file for processing"""
    success: bool
    process_id: Optional[str] = None
    status_msg: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class StatusResult:
    """Result from checking process status"""
    status: Optional[ProcessStatus] = None
    status_msg: Optional[str] = None
    error: Optional[str] = None


class BehavioralSignalsClient:
    """
    Unified client for Behavioral Signals API
    
    Consolidates functionality from monitor_api.py, monitor_and_notify.py,
    and quick_test.py into a single reusable client.
    """
    
    def __init__(
        self,
        api_key: str,
        client_id: str,
        base_url: str = "https://api.behavioralsignals.com",
        request_timeout: int = 30,
        upload_timeout: int = 120,
        retry_attempts: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize the API client
        
        Args:
            api_key: API authentication key
            client_id: Client ID for API access
            base_url: Base URL for API endpoints
            request_timeout: Timeout for regular requests (seconds)
            upload_timeout: Timeout for file uploads (seconds)
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retries (seconds)
        """
        self.api_key = api_key
        self.client_id = client_id
        self.base_url = base_url
        self.request_timeout = request_timeout
        self.upload_timeout = upload_timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Common headers
        self.auth_headers = {
            "X-Auth-Token": self.api_key,
            "accept": "application/json"
        }
    
    def check_connectivity(self) -> bool:
        """
        Test if API is reachable
        
        Returns:
            bool: True if API is reachable, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/status",
                timeout=self.request_timeout
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def test_authentication(self) -> bool:
        """
        Test if authentication works
        
        Returns:
            bool: True if authentication succeeds, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/v5/clients/{self.client_id}",
                headers=self.auth_headers,
                timeout=self.request_timeout
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def submit_file(
        self,
        file_path: str,
        name: Optional[str] = None,
        embeddings: bool = True,
        retry: bool = True
    ) -> ProcessResult:
        """
        Submit an audio/video file for processing
        
        Args:
            file_path: Path to the file to submit
            name: Optional name for the process
            embeddings: Whether to generate embeddings
            retry: Whether to retry on failure
            
        Returns:
            ProcessResult: Result of the submission
        """
        if not os.path.exists(file_path):
            return ProcessResult(
                success=False,
                error=f"File not found: {file_path}"
            )
        
        url = f"{self.base_url}/v5/clients/{self.client_id}/processes/audio"
        
        # Determine content type based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        content_type = 'audio/mp3' if ext == '.mp3' else 'video/mp4'
        
        # Use filename as default name if not provided
        if name is None:
            name = os.path.basename(file_path)
        
        max_attempts = self.retry_attempts if retry else 1
        
        for attempt in range(max_attempts):
            try:
                with open(file_path, 'rb') as f:
                    files = {
                        'file': (os.path.basename(file_path), f, content_type)
                    }
                    data = {
                        'name': name,
                        'embeddings': str(embeddings).lower()
                    }
                    
                    response = requests.post(
                        url,
                        headers={"X-Auth-Token": self.api_key},
                        files=files,
                        data=data,
                        timeout=self.upload_timeout
                    )
                
                if response.status_code == 200:
                    result_data = response.json()
                    return ProcessResult(
                        success=True,
                        process_id=result_data.get('pid'),
                        status_msg=result_data.get('statusmsg'),
                        raw_response=result_data
                    )
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    if attempt < max_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return ProcessResult(
                        success=False,
                        error=error_msg
                    )
                    
            except requests.exceptions.Timeout:
                error_msg = f"Timeout on attempt {attempt + 1}"
                if attempt < max_attempts - 1:
                    time.sleep(self.retry_delay)
                    continue
                return ProcessResult(success=False, error=error_msg)
                
            except requests.exceptions.ConnectionError:
                error_msg = f"Connection error on attempt {attempt + 1}"
                if attempt < max_attempts - 1:
                    time.sleep(self.retry_delay)
                    continue
                return ProcessResult(success=False, error=error_msg)
                
            except Exception as e:
                return ProcessResult(
                    success=False,
                    error=f"Unexpected error: {str(e)}"
                )
        
        return ProcessResult(
            success=False,
            error="All retry attempts failed"
        )
    
    def get_process_status(self, process_id: str) -> StatusResult:
        """
        Check the status of a processing job
        
        Args:
            process_id: The process ID to check
            
        Returns:
            StatusResult: Current status of the process
        """
        try:
            url = f"{self.base_url}/v5/clients/{self.client_id}/processes/{process_id}"
            response = requests.get(
                url,
                headers=self.auth_headers,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                status_code = result.get('status')
                
                # Convert to enum
                status = None
                if status_code == 0:
                    status = ProcessStatus.PENDING
                elif status_code == 1:
                    status = ProcessStatus.PROCESSING
                elif status_code == 2:
                    status = ProcessStatus.COMPLETE
                elif status_code in [-1, -2, -3]:
                    status = ProcessStatus.ERROR_GENERAL
                
                return StatusResult(
                    status=status,
                    status_msg=result.get('statusmsg')
                )
            else:
                return StatusResult(
                    error=f"Failed to get status: HTTP {response.status_code}"
                )
                
        except Exception as e:
            return StatusResult(error=str(e))
    
    def get_results(self, process_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Retrieve results for a completed process
        
        Args:
            process_id: The process ID to get results for
            
        Returns:
            Tuple of (success, results_dict or None)
        """
        try:
            url = f"{self.base_url}/v5/clients/{self.client_id}/processes/{process_id}/results"
            response = requests.get(
                url,
                headers=self.auth_headers,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, None
                
        except Exception:
            return False, None
    
    def monitor_until_complete(
        self,
        process_id: str,
        check_interval: int = 5,
        max_wait: int = 600,
        callback=None
    ) -> StatusResult:
        """
        Monitor a process until it completes or fails
        
        Args:
            process_id: The process ID to monitor
            check_interval: Seconds between status checks
            max_wait: Maximum seconds to wait
            callback: Optional callback function called with status updates
            
        Returns:
            StatusResult: Final status of the process
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                return StatusResult(
                    error=f"Timeout: Process did not complete within {max_wait} seconds"
                )
            
            status_result = self.get_process_status(process_id)
            
            if callback:
                callback(status_result, elapsed)
            
            if status_result.error:
                return status_result
            
            if status_result.status == ProcessStatus.COMPLETE:
                return status_result
            
            if status_result.status in [ProcessStatus.ERROR_GENERAL,
                                       ProcessStatus.ERROR_PROCESSING,
                                       ProcessStatus.ERROR_SYSTEM]:
                return status_result
            
            time.sleep(check_interval)
    
    @staticmethod
    def save_process_id(process_id: str, file_path: str = "process_id.txt"):
        """
        Save process ID to a file for later reference
        
        Args:
            process_id: The process ID to save
            file_path: Path to save the ID to
        """
        with open(file_path, 'w') as f:
            f.write(f"{process_id}\n")


class Monitor:
    """
    Monitoring wrapper around the client for automated checking
    """
    
    def __init__(
        self,
        client: BehavioralSignalsClient,
        check_interval: int = 300,
        max_checks: Optional[int] = None
    ):
        """
        Initialize the monitor
        
        Args:
            client: BehavioralSignalsClient instance
            check_interval: Seconds between checks
            max_checks: Maximum number of checks (None for infinite)
        """
        self.client = client
        self.check_interval = check_interval
        self.max_checks = max_checks
    
    def run_once(self, file_path: str, **kwargs) -> ProcessResult:
        """
        Run a single check and submission if API is available
        
        Args:
            file_path: Path to file to submit
            **kwargs: Additional arguments for submit_file
            
        Returns:
            ProcessResult: Result of the submission
        """
        # Test connectivity
        if not self.client.check_connectivity():
            return ProcessResult(
                success=False,
                error="API is not reachable"
            )
        
        # Test authentication
        if not self.client.test_authentication():
            return ProcessResult(
                success=False,
                error="Authentication failed"
            )
        
        # Submit file
        return self.client.submit_file(file_path, **kwargs)
    
    def run_indefinitely(
        self,
        file_path: str,
        on_success=None,
        on_check=None,
        **kwargs
    ):
        """
        Run monitoring loop indefinitely or until max_checks
        
        Args:
            file_path: Path to file to submit
            on_success: Callback when submission succeeds
            on_check: Callback for each check attempt
            **kwargs: Additional arguments for submit_file
        """
        check_count = 0
        
        while True:
            check_count += 1
            
            if self.max_checks and check_count > self.max_checks:
                print(f"Reached maximum checks ({self.max_checks})")
                break
            
            if on_check:
                on_check(check_count)
            
            result = self.run_once(file_path, **kwargs)
            
            if result.success:
                if on_success:
                    on_success(result)
                break
            
            time.sleep(self.check_interval)