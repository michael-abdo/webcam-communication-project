#!/usr/bin/env python3
"""
Quick Test Script - Refactored to use unified client

Simple script to quickly test API connectivity and file submission.
This replaces the original quick_test.py with a cleaner implementation.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import BehavioralSignalsClient


# Configuration
API_KEY = "f38d44bfe4ae7c915e2be3ec32c2101f"
CLIENT_ID = "10000127"
VIDEO_FILE = "../../data/audios/video1_53yPfrqbpkE_5min.mp3"


def main():
    """Quick test of API functionality"""
    print("Behavioral Signals API - Quick Test")
    print("=" * 50)
    
    # Allow file path override from command line
    file_path = sys.argv[1] if len(sys.argv) > 1 else VIDEO_FILE
    print(f"Test file: {os.path.basename(file_path)}")
    print(f"Client ID: {CLIENT_ID}")
    print()
    
    # Initialize client with retry enabled
    client = BehavioralSignalsClient(
        api_key=API_KEY,
        client_id=CLIENT_ID,
        retry_attempts=3,
        retry_delay=5
    )
    
    # Test connectivity
    print("Testing API connectivity...", end="", flush=True)
    if not client.check_connectivity():
        print(" ✗")
        print("\nAPI is not reachable. Troubleshooting:")
        print("1. Check if API is online at https://platform.behavioralsignals.com")
        print("2. Verify your internet connection")
        print("3. Try again later")
        sys.exit(1)
    print(" ✓")
    
    # Test authentication
    print("Testing authentication...", end="", flush=True)
    if not client.test_authentication():
        print(" ✗")
        print("\nAuthentication failed. Check your API key and client ID.")
        sys.exit(1)
    print(" ✓")
    
    # Submit file
    print("\nSubmitting file for processing...")
    result = client.submit_file(file_path, name='quick-test')
    
    if result.success:
        print(f"\n✓ Success! Audio submitted for processing.")
        print(f"Process ID: {result.process_id}")
        print(f"Status: {result.status_msg}")
        
        # Optional: Monitor until complete
        if "--wait" in sys.argv:
            print("\nMonitoring processing status...")
            
            def callback(status, elapsed):
                print(f"\r[{int(elapsed)}s] Status: {status.status_msg}", 
                      end="", flush=True)
            
            final_status = client.monitor_until_complete(
                result.process_id,
                callback=callback
            )
            
            if final_status.status.name == 'COMPLETE':
                print("\n✓ Processing complete!")
            else:
                print(f"\n✗ Processing failed: {final_status.status_msg}")
    else:
        print(f"\n✗ Submission failed: {result.error}")
        
        if "Insufficient credits" in str(result.error):
            print("\nERROR: Account has insufficient credits for processing")
            print("Please add credits to your account at https://platform.behavioralsignals.com")
        
        print("\nTroubleshooting:")
        print("1. Check if API is online")
        print("2. Verify file exists and is accessible")
        print("3. Check file format (MP3 recommended)")
        print("4. Ensure you have sufficient API credits")


if __name__ == "__main__":
    main()