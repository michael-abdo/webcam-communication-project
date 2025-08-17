#!/usr/bin/env python3
"""
Real-time streaming processor for Behavioral Signals API

Simulates real-time streaming by processing audio in small chunks
and sending them to the API as they would arrive in a live stream.
"""

import sys
import time
import logging
import threading
import queue
from pathlib import Path
from typing import Dict, Any, List
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.config import Config
from src.api.client import BehavioralSignalsClient, Monitor, ProcessStatus
from src.pipeline.pipeline import Pipeline  # For accessing shared processing functionality

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamProcessor:
    """Real-time streaming processor for audio analysis"""
    
    def __init__(self):
        self.config = Config()
        self.pipeline = Pipeline()
        self.api_client = BehavioralSignalsClient(
            api_key=self.config.api['key'],
            client_id=self.config.api['client_id'],
            base_url=self.config.api['base_url']
        )
        self.results_queue = queue.Queue()
        self.processing_jobs = {}
        
        # Stream chunks directory
        self.stream_chunks_dir = Path("data/stream_chunks")
        self.stream_chunks_dir.mkdir(parents=True, exist_ok=True)
        
    def create_stream_chunks(self, video_id: str, chunk_duration: int = 10) -> List[str]:
        """
        Find or suggest creation of stream chunks from shared processing
        
        Args:
            video_id: YouTube video ID
            chunk_duration: Desired duration of each chunk in seconds
            
        Returns:
            List of chunk file paths
        """
        logger.info(f"Looking for stream chunks for video: {video_id}")
        
        # Check if shared chunks already exist
        shared_files = self.pipeline.find_shared_files(video_id)
        
        if shared_files['chunks']:
            logger.info(f"Using existing chunks: {len(shared_files['chunks'])} files")
            return shared_files['chunks']
        
        # No chunks found - suggest creating them via shared processing
        logger.warning(f"No chunks found for video {video_id}")
        logger.info(f"💡 Create chunks first using shared processing:")
        logger.info(f"   python ../../../shared_processing/scripts/process_media.py \"https://youtube.com/watch?v={video_id}\" --chunk --chunk-duration {chunk_duration}")
        return []
    
    def process_chunk_async(self, chunk_path: str, chunk_id: int):
        """
        Process a single chunk asynchronously
        
        Args:
            chunk_path: Path to audio chunk
            chunk_id: Unique identifier for this chunk
        """
        try:
            logger.info(f"🔄 Processing chunk {chunk_id}: {Path(chunk_path).name}")
            
            # Submit to API
            result = self.api_client.submit_file(chunk_path)
            if not result.success:
                logger.error(f"❌ Chunk {chunk_id} submission failed: {result.error}")
                return
            
            process_id = result.process_id
            logger.info(f"✅ Chunk {chunk_id} submitted, process ID: {process_id}")
            
            # Monitor processing using the client's method
            status_result = self.api_client.monitor_until_complete(
                process_id,
                check_interval=2,  # Check every 2 seconds
                max_wait=300  # 5 minutes max
            )
            
            if status_result.status == ProcessStatus.COMPLETE:  # Complete
                # Get results
                success, results = self.api_client.get_results(process_id)
                if success:
                    # Add to results queue with timing info
                    self.results_queue.put({
                        'chunk_id': chunk_id,
                        'process_id': process_id,
                        'results': results,
                        'chunk_file': Path(chunk_path).name,
                        'timestamp': time.time()
                    })
                    logger.info(f"🎯 Chunk {chunk_id} analysis complete!")
                else:
                    logger.error(f"❌ Failed to get results for chunk {chunk_id}")
            else:
                logger.error(f"❌ Chunk {chunk_id} processing failed with status: {status_result.status}")
                
        except Exception as e:
            logger.error(f"❌ Error processing chunk {chunk_id}: {str(e)}")
    
    def stream_process(self, video_id: str, chunk_duration: int = 10, stream_delay: float = 1.0):
        """
        Simulate real-time streaming by processing chunks with delays
        
        Args:
            video_id: YouTube video ID to stream
            chunk_duration: Duration of each chunk in seconds
            stream_delay: Delay between chunk submissions (simulates real-time)
        """
        logger.info(f"🚀 Starting real-time stream processing")
        logger.info(f"📁 Video ID: {video_id}")
        logger.info(f"⏱️  Chunk duration: {chunk_duration}s")
        logger.info(f"🕒 Stream delay: {stream_delay}s")
        
        # Find chunks
        chunks = self.create_stream_chunks(video_id, chunk_duration)
        if not chunks:
            logger.error("❌ No chunks created, aborting")
            return
        
        # Start results monitor thread
        monitor_thread = threading.Thread(target=self.monitor_results, daemon=True)
        monitor_thread.start()
        
        # Process chunks with timing simulation
        threads = []
        start_time = time.time()
        
        for i, chunk_path in enumerate(chunks, 1):
            # Calculate when this chunk would arrive in real streaming
            expected_time = start_time + (i - 1) * stream_delay
            current_time = time.time()
            
            # Wait if we're ahead of the streaming schedule
            if current_time < expected_time:
                sleep_time = expected_time - current_time
                logger.info(f"⏳ Waiting {sleep_time:.1f}s for next chunk...")
                time.sleep(sleep_time)
            
            # Start processing this chunk in a separate thread
            thread = threading.Thread(
                target=self.process_chunk_async,
                args=(chunk_path, i)
            )
            thread.start()
            threads.append(thread)
            
            logger.info(f"📡 Chunk {i}/{len(chunks)} sent to processing pipeline")
        
        # Wait for all processing to complete
        logger.info("⏳ Waiting for all chunks to complete processing...")
        for thread in threads:
            thread.join()
        
        # Give monitor thread time to process final results
        time.sleep(5)
        
        logger.info("🎉 Stream processing complete!")
        self.show_summary()
    
    def monitor_results(self):
        """Monitor and display results as they come in"""
        processed_chunks = set()
        
        while True:
            try:
                # Wait for results (with timeout to allow thread to exit)
                result = self.results_queue.get(timeout=1)
                
                chunk_id = result['chunk_id']
                if chunk_id in processed_chunks:
                    continue
                
                processed_chunks.add(chunk_id)
                
                logger.info(f"📊 RESULTS for Chunk {chunk_id} ({result['chunk_file']}):")
                
                # Process and display key results
                results = result['results'].get('results', [])
                
                # Group by task
                by_task = {}
                for r in results:
                    task = r.get('task', 'unknown')
                    if task not in by_task:
                        by_task[task] = []
                    by_task[task].append(r)
                
                # Display key insights
                if 'asr' in by_task:
                    transcripts = []
                    for segment in by_task['asr']:
                        text = segment.get('finalLabel', '').strip()
                        if text:
                            transcripts.append(text)
                    if transcripts:
                        logger.info(f"  🗣️  Speech: {' '.join(transcripts)}")
                
                if 'emotion' in by_task:
                    emotions = [seg.get('finalLabel', '') for seg in by_task['emotion']]
                    if emotions:
                        logger.info(f"  😊 Emotions: {', '.join(set(emotions))}")
                
                if 'gender' in by_task and by_task['gender']:
                    gender = by_task['gender'][0].get('finalLabel', 'Unknown')
                    logger.info(f"  👤 Gender: {gender}")
                
                logger.info(f"  💾 Full results saved for process {result['process_id']}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in results monitor: {str(e)}")
                break
    
    def show_summary(self):
        """Show processing summary"""
        logger.info("\n" + "="*60)
        logger.info("📈 STREAM PROCESSING SUMMARY")
        logger.info("="*60)
        logger.info(f"Total chunks processed: {len(self.processing_jobs)}")
        logger.info("Real-time behavioral analysis simulation complete!")
        logger.info("="*60)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Real-time streaming processor for Behavioral Signals API"
    )
    parser.add_argument(
        'audio_file',
        help='Path to audio file to stream process'
    )
    parser.add_argument(
        '--chunk-duration',
        type=int,
        default=10,
        help='Duration of each chunk in seconds (default: 10)'
    )
    parser.add_argument(
        '--stream-delay',
        type=float,
        default=2.0,
        help='Delay between chunks to simulate real-time (default: 2.0s)'
    )
    
    args = parser.parse_args()
    
    # Validate file exists
    if not Path(args.audio_file).exists():
        logger.error(f"Audio file not found: {args.audio_file}")
        sys.exit(1)
    
    # Create and run stream processor
    processor = StreamProcessor()
    
    logger.info("🎬 Starting Behavioral Signals Real-time Stream Processor")
    logger.info(f"⚠️  This will use API credits for each chunk!")
    
    processor.stream_process(
        args.audio_file,
        chunk_duration=args.chunk_duration,
        stream_delay=args.stream_delay
    )


if __name__ == "__main__":
    main()