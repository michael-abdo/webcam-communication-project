#!/usr/bin/env python3
"""
Behavioral Signals API Monitor with Notifications - Refactored to use unified client

Monitors API, submits files, tracks processing status, and plays notification sounds.
This replaces the original monitor_and_notify.py with a cleaner implementation.
"""

import sys
import os
import subprocess
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import BehavioralSignalsClient, ProcessStatus


# Configuration
API_KEY = "f38d44bfe4ae7c915e2be3ec32c2101f"
CLIENT_ID = "10000127"
VIDEO_FILE = "../../data/audios/video1_53yPfrqbpkE_5min.mp3"
CHECK_INTERVAL = 300  # 5 minutes
PROCESS_ID_FILE = "../../data/completed_process_id.txt"


def play_bell_sound():
    """Play system bell sound using macOS commands"""
    try:
        # Method 1: Terminal bell
        print('\a')  # ASCII bell character
        
        # Method 2: macOS system sound
        subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], 
                      capture_output=True)
        
        # Method 3: macOS say command
        subprocess.run(['say', 'Processing complete!'], capture_output=True)
        
        return True
    except Exception as e:
        print(f"Could not play sound: {e}")
        return False


def monitor_with_notifications():
    """Main monitoring function with processing tracking and notifications"""
    print("Behavioral Signals API Monitor with Notification")
    print("=" * 50)
    print(f"Video file: {os.path.basename(VIDEO_FILE)}")
    print(f"Check interval: {CHECK_INTERVAL} seconds ({CHECK_INTERVAL/60} minutes)")
    print("\nMonitoring will run indefinitely. Press Ctrl+C to stop.\n")
    
    # Test notification sound
    print("Testing notification sound...")
    play_bell_sound()
    print("Sound test complete. Starting monitoring in 3 seconds...\n")
    import time
    time.sleep(3)
    
    # Initialize client
    client = BehavioralSignalsClient(
        api_key=API_KEY,
        client_id=CLIENT_ID
    )
    
    check_count = 0
    
    while True:
        check_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Check #{check_count}:")
        
        # Test API connectivity
        print("  Testing API connectivity...", end="", flush=True)
        if not client.check_connectivity():
            print(" ✗ (API unreachable)")
            print(f"  Waiting {CHECK_INTERVAL/60} minutes before next check...\n")
            time.sleep(CHECK_INTERVAL)
            continue
        print(" ✓")
        
        # Test authentication
        print("  Testing authentication...", end="", flush=True)
        if not client.test_authentication():
            print(" ✗ (Auth failed)")
            print(f"  Waiting {CHECK_INTERVAL/60} minutes before next check...\n")
            time.sleep(CHECK_INTERVAL)
            continue
        print(" ✓")
        
        # Submit file
        print("  Submitting MP3 file...", end="", flush=True)
        result = client.submit_file(VIDEO_FILE, name='auto-monitor-submission')
        
        if not result.success:
            print(f" ✗ ({result.error})")
            print(f"  Waiting {CHECK_INTERVAL/60} minutes before next check...\n")
            time.sleep(CHECK_INTERVAL)
            continue
        
        print(f" ✓ (Process ID: {result.process_id})")
        
        # Monitor processing status
        print("\n  Monitoring processing status...")
        
        def status_callback(status_result, elapsed):
            """Callback for status updates during monitoring"""
            print(f"\r  [{int(elapsed)}s] Status: {status_result.status_msg}", 
                  end="", flush=True)
        
        final_status = client.monitor_until_complete(
            result.process_id,
            callback=status_callback
        )
        
        if final_status.status == ProcessStatus.COMPLETE:
            print(f"\n✓ Processing complete!")
            print(f"  Status: {final_status.status_msg}")
            
            # Play notification sound
            print("\n🔔 Playing notification sound...")
            play_bell_sound()
            
            # Save process ID
            client.save_process_id(result.process_id, PROCESS_ID_FILE)
            print(f"✓ Process ID saved to: {PROCESS_ID_FILE}")
            
            # Try to get results
            success, results = client.get_results(result.process_id)
            if success and results:
                results_file = f"../../data/results/process_{result.process_id}_results.json"
                with open(results_file, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"✓ Results saved to: {results_file}")
            
            print("\n" + "=" * 50)
            print("Processing complete! You can retrieve results using the process ID.")
            print("=" * 50)
            
            # Exit after successful processing
            return True
            
        elif final_status.error:
            print(f"\n✗ Processing failed: {final_status.error}")
        else:
            print(f"\n✗ Processing failed: {final_status.status_msg}")
        
        # If we get here, processing failed
        print(f"\n  Waiting {CHECK_INTERVAL/60} minutes before next check...\n")
        time.sleep(CHECK_INTERVAL)


def main():
    """Main function with error handling"""
    try:
        monitor_with_notifications()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    main()