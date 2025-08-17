#!/usr/bin/env python3
"""
Behavioral Signals Analysis Pipeline - Uses shared processed media files

This script analyzes YouTube videos that have been processed by the shared processing system.

New Workflow:
  1. First, run shared processing to create audio files:
     python ../../../shared_processing/scripts/process_media.py "YOUTUBE_URL"
  
  2. Then run this script to analyze the processed files:
     python scripts/run_pipeline.py "YOUTUBE_URL"

Usage:
    # Analyze video using shared processed files
    python scripts/run_pipeline.py "https://youtube.com/watch?v=VIDEO_ID"
    
    # Prefer chunk files for analysis
    python scripts/run_pipeline.py "https://youtube.com/watch?v=VIDEO_ID" --chunks
    
    # Check what files are available for a video
    python scripts/run_pipeline.py "https://youtube.com/watch?v=VIDEO_ID" --check-files
    
    # Check job status
    python scripts/run_pipeline.py --status job_12345
    
    # Process batch of URLs (must have shared processing done first)
    python scripts/run_pipeline.py --batch urls.txt
    
    # Generate report from existing results
    python scripts/run_pipeline.py --report process_12345_results.json
    
    # Auto-process: Run shared processing first, then analysis
    python scripts/run_pipeline.py "https://youtube.com/watch?v=VIDEO_ID" --auto-process
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.pipeline import Pipeline
from src.analysis.create_report import create_behavior_report


def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def run_shared_processing(url: str, enable_chunking: bool = False) -> bool:
    """Run shared processing for a YouTube URL
    
    Args:
        url: YouTube URL to process
        enable_chunking: Whether to create chunks
        
    Returns:
        True if successful
    """
    print(f"\n🔄 Running shared processing for: {url}")
    print("-" * 50)
    
    # Build command
    shared_script = Path(__file__).parent.parent.parent.parent / "shared_processing" / "scripts" / "process_media.py"
    cmd = ["python3", str(shared_script), url]
    
    if enable_chunking:
        cmd.append("--chunk")
    
    try:
        # Run shared processing
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ Shared processing completed successfully")
            return True
        else:
            print(f"❌ Shared processing failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Shared processing timed out")
        return False
    except Exception as e:
        print(f"❌ Error running shared processing: {str(e)}")
        return False


def check_available_files(pipeline: Pipeline, url: str):
    """Check what processed files are available for a URL
    
    Args:
        pipeline: Pipeline instance
        url: YouTube URL to check
    """
    video_id = pipeline.extract_video_id(url)
    if not video_id:
        print(f"❌ Invalid YouTube URL: {url}")
        return
    
    print(f"\n📁 Available files for video: {video_id}")
    print("-" * 50)
    
    shared_files = pipeline.find_shared_files(video_id)
    
    total_files = sum(len(files) for files in shared_files.values())
    
    if total_files == 0:
        print("❌ No processed files found")
        print(f"💡 Run shared processing first:")
        print(f"   python ../../../shared_processing/scripts/process_media.py \"{url}\"")
        return
    
    if shared_files['converted']:
        print(f"🎵 Converted Audio Files ({len(shared_files['converted'])} files):")
        for f in shared_files['converted']:
            print(f"   • {Path(f).name}")
    
    if shared_files['samples']:
        print(f"📏 Sample Files ({len(shared_files['samples'])} files):")
        for f in shared_files['samples']:
            print(f"   • {Path(f).name}")
    
    if shared_files['chunks']:
        print(f"🧩 Chunk Files ({len(shared_files['chunks'])} files):")
        for f in shared_files['chunks']:
            print(f"   • {Path(f).name}")
    
    print(f"\n✅ Total: {total_files} processed files available")


def process_single_url(
    pipeline: Pipeline, 
    url: str, 
    prefer_chunks: bool = False,
    auto_process: bool = False,
    enable_chunking: bool = False
) -> bool:
    """Process a single YouTube URL"""
    print(f"\n🔄 Processing URL: {url}")
    print("-" * 50)
    
    # If auto-process is enabled, run shared processing first
    if auto_process:
        if not run_shared_processing(url, enable_chunking):
            return False
        print()  # Add spacing
    
    # Check if files are available
    video_id = pipeline.extract_video_id(url)
    if not video_id:
        print(f"❌ Invalid YouTube URL: {url}")
        return False
    
    shared_files = pipeline.find_shared_files(video_id)
    total_files = sum(len(files) for files in shared_files.values())
    
    if total_files == 0:
        print(f"❌ No processed files found for video ID: {video_id}")
        print(f"💡 Run shared processing first:")
        print(f"   python ../../../shared_processing/scripts/process_media.py \"{url}\"")
        print(f"   Or use --auto-process flag to run it automatically")
        return False
    
    # Process through behavioral signals API
    job = pipeline.process_url(url, prefer_chunks=prefer_chunks)
    
    if job['status'] == 'completed':
        print(f"\n✅ Success! Job ID: {job['id']}")
        
        if job.get('audio_paths'):  # Chunked processing
            print(f"📊 Processed {len(job['audio_paths'])} chunks")
            print(f"📄 Results: {len(job.get('result_paths', []))} result files")
        else:  # Single file processing
            print(f"🎵 Audio: {Path(job['audio_path']).name}")
            print(f"📄 Results: {job['result_path']}")
        
        if job.get('report_path'):
            print(f"📋 Report: {job['report_path']}")
        
        return True
    else:
        print(f"\n❌ Failed! Job ID: {job['id']}")
        print(f"📊 Status: {job['status']}")
        print(f"❌ Error: {job.get('error', 'Unknown error')}")
        return False


def process_batch(pipeline: Pipeline, batch_file: str, prefer_chunks: bool = False, auto_process: bool = False) -> None:
    """Process a batch of URLs from a file"""
    batch_path = Path(batch_file)
    
    if not batch_path.exists():
        print(f"❌ Batch file not found: {batch_file}")
        return
    
    with open(batch_path, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"\n📊 Processing {len(urls)} URLs from {batch_file}")
    print("=" * 50)
    
    success_count = 0
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing...")
        if process_single_url(pipeline, url, prefer_chunks, auto_process):
            success_count += 1
    
    print(f"\n\n📊 Batch Summary: {success_count}/{len(urls)} successful")


def check_job_status(pipeline: Pipeline, job_id: str):
    """Check the status of a job"""
    job = pipeline.get_job_status(job_id)
    
    if not job:
        print(f"❌ Job not found: {job_id}")
        return
    
    print(f"\n📊 Job Status: {job_id}")
    print("-" * 50)
    print(f"Status: {job['status']}")
    print(f"URL: {job['url']}")
    print(f"Created: {job['created_at']}")
    
    if job.get('updated_at'):
        print(f"Updated: {job['updated_at']}")
    
    if job.get('audio_path'):
        print(f"Audio: {job['audio_path']}")
    
    if job.get('audio_paths'):
        print(f"Chunks: {len(job['audio_paths'])} files")
    
    if job.get('process_id'):
        print(f"Process ID: {job['process_id']}")
    
    if job.get('result_path'):
        print(f"Results: {job['result_path']}")
    
    if job.get('result_paths'):
        print(f"Results: {len(job['result_paths'])} files")
    
    if job.get('report_path'):
        print(f"Report: {job['report_path']}")
    
    if job.get('error'):
        print(f"Error: {job['error']}")


def generate_report_from_results(results_file: str):
    """Generate a report from existing results JSON"""
    results_path = Path(results_file)
    
    if not results_path.exists():
        print(f"❌ Results file not found: {results_file}")
        return
    
    # Generate report filename
    report_name = results_path.stem.replace('_results', '')
    report_path = results_path.parent.parent / 'reports' / f"{report_name}_report.txt"
    
    print(f"\n📋 Generating report from: {results_file}")
    
    try:
        create_behavior_report(str(results_path), str(report_path))
        print(f"✅ Report generated: {report_path}")
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="Behavioral Signals Analysis - Process shared processed media files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'urls',
        nargs='*',
        help='YouTube URLs to analyze (must have shared processing done first)'
    )
    
    parser.add_argument(
        '--chunks',
        action='store_true',
        help='Prefer chunk files for analysis'
    )
    
    parser.add_argument(
        '--check-files',
        action='store_true',
        help='Check what processed files are available for the URL'
    )
    
    parser.add_argument(
        '--auto-process',
        action='store_true',
        help='Automatically run shared processing first if needed'
    )
    
    parser.add_argument(
        '--enable-chunking',
        action='store_true',
        help='Enable chunking when auto-processing (used with --auto-process)'
    )
    
    parser.add_argument(
        '--status',
        help='Check status of a job by ID'
    )
    
    parser.add_argument(
        '--batch',
        help='Process batch of URLs from file'
    )
    
    parser.add_argument(
        '--report',
        help='Generate report from existing results JSON'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Initialize pipeline
    pipeline = Pipeline()
    
    # Check dependencies
    if not pipeline.check_dependencies():
        print("\n❌ Pipeline dependencies check failed!")
        print("Please ensure shared processing directories are accessible.")
        sys.exit(1)
    
    # Handle different modes
    if args.status:
        check_job_status(pipeline, args.status)
    elif args.batch:
        process_batch(pipeline, args.batch, args.chunks, args.auto_process)
    elif args.report:
        generate_report_from_results(args.report)
    elif args.check_files and args.urls:
        for url in args.urls:
            check_available_files(pipeline, url)
    elif args.urls:
        success_count = 0
        for url in args.urls:
            if process_single_url(pipeline, url, args.chunks, args.auto_process, args.enable_chunking):
                success_count += 1
        
        if len(args.urls) > 1:
            print(f"\n📊 Summary: {success_count}/{len(args.urls)} successful")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()