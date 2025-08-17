#!/usr/bin/env python3
"""
Behavioral Signals API Monitor - Refactored to use unified client

Monitors API availability and automatically submits audio files when available.
This replaces the original monitor_api.py with a cleaner implementation.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import BehavioralSignalsClient, Monitor


# Configuration (should be moved to config file or environment variables)
API_KEY = "f38d44bfe4ae7c915e2be3ec32c2101f"
CLIENT_ID = "10000127"
VIDEO_FILE = "../../data/audios/video1_53yPfrqbpkE_5min.mp3"
CHECK_INTERVAL = 300  # 5 minutes
MAX_CHECKS = 12  # 1 hour total
PROCESS_ID_FILE = "../../data/last_process_id.txt"


def main():
    """Main monitoring function"""
    # Check for --once flag
    run_once = "--once" in sys.argv
    
    print("Behavioral Signals API Monitor")
    print("=" * 50)
    print(f"Will check API every {CHECK_INTERVAL} seconds ({CHECK_INTERVAL/60} minutes)")
    
    if not run_once:
        print(f"Maximum monitoring time: {MAX_CHECKS * CHECK_INTERVAL / 60} minutes")
    
    print(f"Video file: {os.path.basename(VIDEO_FILE)}")
    print("\nPress Ctrl+C to stop monitoring\n")
    
    # Initialize client
    client = BehavioralSignalsClient(
        api_key=API_KEY,
        client_id=CLIENT_ID
    )
    
    # Initialize monitor
    monitor = Monitor(
        client=client,
        check_interval=CHECK_INTERVAL,
        max_checks=1 if run_once else MAX_CHECKS
    )
    
    def on_check(check_count):
        """Callback for each check"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        max_str = f"/{MAX_CHECKS}" if not run_once else ""
        print(f"[{timestamp}] Check {check_count}{max_str}:")
        print("  Testing API status...", end="", flush=True)
        
        if not client.check_connectivity():
            print(" ✗")
            return
        print(" ✓")
        
        print("  Testing authentication...", end="", flush=True)
        if not client.test_authentication():
            print(" ✗")
            return
        print(" ✓")
        
        print("  Submitting video...", end="", flush=True)
    
    def on_success(result):
        """Callback for successful submission"""
        print(f" ✓ (Process ID: {result.process_id})")
        
        # Save process ID
        client.save_process_id(result.process_id, PROCESS_ID_FILE)
        print(f"\nProcess ID saved to: {PROCESS_ID_FILE}")
        print("You can check the processing status using this ID.")
        
        if run_once:
            print("\nSingle check complete. Exiting.")
        else:
            print("\nMonitoring complete! Video submitted successfully.")
    
    try:
        # Run monitoring
        if run_once:
            result = monitor.run_once(VIDEO_FILE, name='monitor-submission')
            if result.success:
                on_success(result)
            else:
                print(f" ✗ ({result.error})")
                sys.exit(1)
        else:
            monitor.run_indefinitely(
                VIDEO_FILE,
                name='monitor-submission',
                on_check=on_check,
                on_success=on_success
            )
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()