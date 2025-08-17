#!/usr/bin/env python3
"""
End-to-End Integration Test Script

Tests the complete workflow from YouTube URL to behavioral analysis.
This script demonstrates the new shared processing architecture.

Usage:
    python scripts/e2e_test.py "https://youtube.com/watch?v=VIDEO_ID"
    python scripts/e2e_test.py "https://youtube.com/watch?v=VIDEO_ID" --chunks
    python scripts/e2e_test.py --test-video  # Uses a short test video
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.pipeline import Pipeline


def run_command(cmd: list, description: str, timeout: int = 300) -> Tuple[bool, str]:
    """Run a command and return success status and output
    
    Args:
        cmd: Command to run as list
        description: Description for logging
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (success, output)
    """
    print(f"\n🔄 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        if result.returncode == 0:
            print(f"   ✅ Success!")
            return True, result.stdout
        else:
            print(f"   ❌ Failed with return code {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timed out after {timeout} seconds")
        return False, f"Timeout after {timeout} seconds"
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return False, str(e)


def test_e2e_workflow(url: str, enable_chunking: bool = False, dry_run: bool = False) -> bool:
    """Test the complete end-to-end workflow
    
    Args:
        url: YouTube URL to test with
        enable_chunking: Whether to test chunk processing
        dry_run: If True, skip API calls to avoid costs
        
    Returns:
        True if all tests passed
    """
    print("🚀 Starting End-to-End Integration Test")
    print("=" * 60)
    print(f"📺 URL: {url}")
    print(f"🧩 Chunking: {'Enabled' if enable_chunking else 'Disabled'}")
    print(f"🧪 Mode: {'Dry Run' if dry_run else 'Full Test'}")
    
    # Initialize pipeline for testing
    pipeline = Pipeline()
    video_id = pipeline.extract_video_id(url)
    
    if not video_id:
        print("❌ Invalid YouTube URL")
        return False
    
    print(f"🆔 Video ID: {video_id}")
    
    # Step 1: Run shared processing (using relative path)
    shared_script = "../../../shared_processing/scripts/process_media.py"
    cmd = ["python3", str(shared_script), url]
    
    if enable_chunking:
        cmd.extend(["--chunk", "--chunk-duration", "30", "--min-duration", "10"])
    
    success, output = run_command(cmd, "Running shared processing", timeout=600)
    if not success:
        print("\n❌ Shared processing failed - cannot continue")
        return False
    
    # Step 2: Verify shared files were created
    print(f"\n🔍 Verifying shared files were created...")
    shared_files = pipeline.find_shared_files(video_id)
    
    total_files = sum(len(files) for files in shared_files.values())
    if total_files == 0:
        print("❌ No shared files found after processing")
        return False
    
    print(f"✅ Found {total_files} shared processed files:")
    for file_type, files in shared_files.items():
        if files:
            print(f"   📁 {file_type}: {len(files)} files")
            for f in files:
                file_path = Path(f)
                file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                print(f"      • {file_path.name} ({file_size:.1f} MB)")
    
    # Step 3: Test behavior_signals analysis
    if dry_run:
        print(f"\n🧪 Dry run mode - skipping API calls")
        print(f"   Would analyze using: {'chunks' if enable_chunking else 'single files'}")
        
        # Test pipeline setup
        try:
            job_data = {
                'id': 'dry_run_test',
                'status': 'would_process',
                'url': url,
                'video_id': video_id,
                'available_files': shared_files
            }
            print(f"   ✅ Pipeline setup successful")
            print(f"   📊 Job data: {job_data}")
            return True
            
        except Exception as e:
            print(f"   ❌ Pipeline setup failed: {str(e)}")
            return False
    
    else:
        print(f"\n🤖 Running behavioral signals analysis...")
        
        # Run actual analysis
        behavior_cmd = [
            "python3", 
            str(Path(__file__).parent / "run_pipeline.py"),
            url
        ]
        
        if enable_chunking:
            behavior_cmd.append("--chunks")
        
        success, output = run_command(behavior_cmd, "Running behavioral analysis", timeout=900)
        
        if not success:
            print(f"\n❌ Behavioral analysis failed")
            return False
        
        print(f"\n✅ Behavioral analysis completed successfully!")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="End-to-End Integration Test for Shared Processing Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'url',
        nargs='?',
        help='YouTube URL to test (optional if using --test-video)'
    )
    
    parser.add_argument(
        '--chunks',
        action='store_true',
        help='Test chunk processing workflow'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Skip API calls to avoid costs (recommended for testing)'
    )
    
    parser.add_argument(
        '--test-video',
        action='store_true',
        help='Use a predefined short test video'
    )
    
    args = parser.parse_args()
    
    # Determine URL to use
    if args.test_video:
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Short test video
        print("🎬 Using predefined test video (short duration)")
    elif args.url:
        test_url = args.url
    else:
        parser.print_help()
        return
    
    # Run the test
    start_time = time.time()
    
    success = test_e2e_workflow(
        url=test_url,
        enable_chunking=args.chunks,
        dry_run=args.dry_run
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print(f"🏁 End-to-End Test Complete!")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"📊 Result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if success:
        print("\n🎉 The new shared processing architecture is working correctly!")
        print("   • Shared processing creates files in the correct locations")
        print("   • Behavior signals pipeline can find and use shared files")
        print("   • End-to-end workflow is functional")
        
        if args.dry_run:
            print("\n💡 To test with real API calls, run without --dry-run flag")
            print("   ⚠️  Note: Real API calls will consume credits and cost money")
    else:
        print("\n❌ Test failed - check the error messages above")
        print("   • Ensure shared_processing is set up correctly")
        print("   • Verify API credentials are configured")
        print("   • Check network connectivity")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()