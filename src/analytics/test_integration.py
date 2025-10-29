#!/usr/bin/env python3
"""
Integration test for the analytics event flow.

This test verifies the complete flow from event publishing to analytics processing:
1. Publishes test events to Redis
2. Verifies analytics services receive and process events
3. Checks that metrics are calculated correctly
4. Validates database storage (if configured)
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import uuid
import redis.asyncio as redis
from dataclasses import dataclass, field
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics_services.base_analytics_service import BaseAnalyticsService


# Test configuration
TEST_SESSION_ID = f"test-integration-{int(time.time())}"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
TEST_DURATION_SECONDS = 10


@dataclass
class TestMetric:
    """Represents a collected test metric."""
    service: str
    metric: str
    value: float
    session_id: str
    participant_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, Any] = field(default_factory=dict)


class TestAnalyticsService(BaseAnalyticsService):
    """
    Test analytics service that collects all events and metrics for validation.
    """
    
    def __init__(self, **kwargs):
        super().__init__(service_name="test_integration", **kwargs)
        self.received_events: List[Dict[str, Any]] = []
        self.published_metrics: List[TestMetric] = []
        self.event_counts = {"audio": 0, "transcript": 0, "video": 0, "session": 0}
    
    def get_event_types(self) -> List[str]:
        """Subscribe to all event types."""
        return ["audio", "transcript", "video", "session", "participant"]
    
    async def process_event(self, event: Dict[str, Any], event_type: str):
        """Store all received events."""
        self.received_events.append(event)
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
        
        # Process specific event types
        if event_type == "audio":
            duration = event["data"].get("duration", 0) / 1000  # Convert to seconds
            await self.publish_metric(
                "test_audio_duration",
                duration,
                event["sessionId"],
                event["data"].get("participantId")
            )
        elif event_type == "transcript":
            word_count = len(event["data"].get("text", "").split())
            await self.publish_metric(
                "test_word_count",
                word_count,
                event["sessionId"],
                event["data"].get("participantId")
            )
    
    async def store_metric(self, metric: Dict[str, Any]):
        """Override to collect metrics instead of storing."""
        self.published_metrics.append(
            TestMetric(
                service=self.service_name,
                metric=metric["metric"],
                value=metric["value"],
                session_id=metric["session_id"],
                participant_id=metric.get("participant_id"),
                tags=metric.get("tags", {})
            )
        )


class EventFlowIntegrationTest:
    """
    Integration test runner for the analytics event flow.
    """
    
    def __init__(self):
        self.redis_client = None
        self.test_service = None
        self.logger = self._setup_logging()
        self.test_events_published = 0
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Set up test logging."""
        logger = logging.getLogger("integration_test")
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    async def setup(self):
        """Set up test environment."""
        self.logger.info("Setting up integration test...")
        
        # Connect to Redis
        self.redis_client = await redis.from_url(REDIS_URL)
        
        # Verify Redis connection
        try:
            await self.redis_client.ping()
            self.logger.info("✓ Connected to Redis")
            self._record_pass("Redis connection")
        except Exception as e:
            self._record_fail("Redis connection", str(e))
            raise
        
        # Create and start test analytics service
        self.test_service = TestAnalyticsService(redis_url=REDIS_URL)
        
        # Start service in background
        self.service_task = asyncio.create_task(self.test_service.run())
        await asyncio.sleep(1)  # Give service time to subscribe
        
        self.logger.info("✓ Test analytics service started")
        self._record_pass("Service startup")
    
    async def publish_test_event(self, event_type: str, data: Dict[str, Any]):
        """Publish a test event to Redis."""
        event = {
            "eventId": str(uuid.uuid4()),
            "eventType": event_type,
            "sessionId": TEST_SESSION_ID,
            "timestamp": int(time.time() * 1000),
            "data": data,
            "metadata": {
                "rtmsStreamId": f"test-stream-{TEST_SESSION_ID}",
                "processingTime": datetime.now(timezone.utc).isoformat(),
                "version": "1.0",
            },
        }
        
        channel = f"analytics:{event_type}"
        await self.redis_client.publish(channel, json.dumps(event))
        self.test_events_published += 1
        
        self.logger.debug(f"Published {event_type} event to {channel}")
    
    async def test_basic_event_flow(self):
        """Test basic event publishing and reception."""
        self.logger.info("\nTesting basic event flow...")
        
        # Publish test events
        test_participant_id = str(uuid.uuid4())
        
        # Session start
        await self.publish_test_event("session", {
            "action": "start",
            "participantCount": 1,
        })
        
        # Audio event
        await self.publish_test_event("audio", {
            "participantId": test_participant_id,
            "userName": "Test User",
            "duration": 160,  # milliseconds
            "sequenceNo": 1,
        })
        
        # Transcript event
        await self.publish_test_event("transcript", {
            "participantId": test_participant_id,
            "userName": "Test User",
            "text": "This is a test transcript",
            "confidence": 0.95,
        })
        
        # Video event
        await self.publish_test_event("video", {
            "participantId": test_participant_id,
            "frameNumber": 1,
            "width": 1280,
            "height": 720,
        })
        
        # Session end
        await self.publish_test_event("session", {
            "action": "end",
            "duration": 5,
        })
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Verify events received
        if len(self.test_service.received_events) == self.test_events_published:
            self._record_pass(
                f"Event reception ({len(self.test_service.received_events)} events)"
            )
        else:
            self._record_fail(
                "Event reception",
                f"Expected {self.test_events_published} events, "
                f"received {len(self.test_service.received_events)}"
            )
        
        # Verify event types
        for event_type, count in self.test_service.event_counts.items():
            if count > 0:
                self.logger.info(f"  ✓ Received {count} {event_type} events")
    
    async def test_metric_calculation(self):
        """Test that metrics are calculated correctly."""
        self.logger.info("\nTesting metric calculation...")
        
        # Clear previous metrics
        self.test_service.published_metrics.clear()
        
        # Publish events with known values
        participant_id = str(uuid.uuid4())
        
        # Multiple audio events
        for i in range(5):
            await self.publish_test_event("audio", {
                "participantId": participant_id,
                "userName": "Metric Test User",
                "duration": 1000,  # 1 second
                "sequenceNo": i + 1,
            })
        
        # Multiple transcripts
        test_phrases = [
            "One two three",  # 3 words
            "Four five six seven",  # 4 words
            "Eight nine ten",  # 3 words
        ]
        
        for phrase in test_phrases:
            await self.publish_test_event("transcript", {
                "participantId": participant_id,
                "userName": "Metric Test User",
                "text": phrase,
            })
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Verify audio duration metrics
        audio_metrics = [
            m for m in self.test_service.published_metrics
            if m.metric == "test_audio_duration"
        ]
        
        if len(audio_metrics) == 5:
            self._record_pass(f"Audio metric count ({len(audio_metrics)})")
            total_duration = sum(m.value for m in audio_metrics)
            if abs(total_duration - 5.0) < 0.01:  # 5 seconds total
                self._record_pass(f"Audio duration calculation ({total_duration}s)")
            else:
                self._record_fail(
                    "Audio duration calculation",
                    f"Expected 5.0s, got {total_duration}s"
                )
        else:
            self._record_fail(
                "Audio metric count",
                f"Expected 5 metrics, got {len(audio_metrics)}"
            )
        
        # Verify word count metrics
        word_metrics = [
            m for m in self.test_service.published_metrics
            if m.metric == "test_word_count"
        ]
        
        if len(word_metrics) == 3:
            self._record_pass(f"Word count metric count ({len(word_metrics)})")
            total_words = sum(m.value for m in word_metrics)
            if total_words == 10:  # 3 + 4 + 3 words
                self._record_pass(f"Word count calculation ({total_words} words)")
            else:
                self._record_fail(
                    "Word count calculation",
                    f"Expected 10 words, got {total_words}"
                )
        else:
            self._record_fail(
                "Word count metric count",
                f"Expected 3 metrics, got {len(word_metrics)}"
            )
    
    async def test_concurrent_events(self):
        """Test handling of concurrent events from multiple participants."""
        self.logger.info("\nTesting concurrent event handling...")
        
        # Create multiple participants
        participants = [
            {"id": str(uuid.uuid4()), "name": f"User {i+1}"}
            for i in range(3)
        ]
        
        # Publish events concurrently
        tasks = []
        for _ in range(10):  # 10 rounds
            for participant in participants:
                tasks.append(
                    self.publish_test_event("audio", {
                        "participantId": participant["id"],
                        "userName": participant["name"],
                        "duration": 100,
                    })
                )
        
        # Execute all tasks concurrently
        start_time = time.time()
        await asyncio.gather(*tasks)
        publish_time = time.time() - start_time
        
        # Wait for processing
        await asyncio.sleep(2)
        
        self.logger.info(f"  Published {len(tasks)} events in {publish_time:.2f}s")
        
        # Verify all events were processed
        audio_count = self.test_service.event_counts.get("audio", 0)
        initial_count = 6  # From previous tests
        expected_new = len(tasks)
        
        if audio_count >= initial_count + expected_new:
            self._record_pass(
                f"Concurrent event processing ({expected_new} events)"
            )
            self.logger.info(f"  ✓ All concurrent events processed successfully")
        else:
            self._record_fail(
                "Concurrent event processing",
                f"Expected at least {initial_count + expected_new} events, "
                f"got {audio_count}"
            )
    
    async def test_error_handling(self):
        """Test error handling with malformed events."""
        self.logger.info("\nTesting error handling...")
        
        # Publish malformed event (missing required fields)
        malformed_event = {
            "eventId": str(uuid.uuid4()),
            "eventType": "audio",
            # Missing sessionId and other required fields
            "data": {},
        }
        
        try:
            await self.redis_client.publish(
                "analytics:audio",
                json.dumps(malformed_event)
            )
            await asyncio.sleep(1)
            
            # Service should continue running despite error
            if self.service_task.done():
                self._record_fail(
                    "Error resilience",
                    "Service crashed on malformed event"
                )
            else:
                self._record_pass("Error resilience (service still running)")
        except Exception as e:
            self._record_fail("Error handling test", str(e))
    
    def _record_pass(self, test_name: str):
        """Record a passed test."""
        self.test_results["passed"] += 1
        self.logger.info(f"  ✓ {test_name}")
    
    def _record_fail(self, test_name: str, error: str):
        """Record a failed test."""
        self.test_results["failed"] += 1
        self.test_results["errors"].append(f"{test_name}: {error}")
        self.logger.error(f"  ✗ {test_name}: {error}")
    
    async def teardown(self):
        """Clean up test environment."""
        self.logger.info("\nCleaning up...")
        
        if self.test_service:
            self.test_service.shutdown_event.set()
            await asyncio.sleep(0.5)
            
            if self.service_task and not self.service_task.done():
                self.service_task.cancel()
                try:
                    await self.service_task
                except asyncio.CancelledError:
                    pass
        
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info("✓ Cleanup complete")
    
    def print_summary(self):
        """Print test summary."""
        total = self.test_results["passed"] + self.test_results["failed"]
        
        self.logger.info("\n" + "=" * 50)
        self.logger.info("INTEGRATION TEST SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total tests: {total}")
        self.logger.info(f"Passed: {self.test_results['passed']} ✓")
        self.logger.info(f"Failed: {self.test_results['failed']} ✗")
        
        if self.test_results["errors"]:
            self.logger.info("\nErrors:")
            for error in self.test_results["errors"]:
                self.logger.error(f"  - {error}")
        
        self.logger.info("\nMetrics Summary:")
        self.logger.info(f"  Events published: {self.test_events_published}")
        self.logger.info(f"  Events received: {len(self.test_service.received_events)}")
        self.logger.info(f"  Metrics generated: {len(self.test_service.published_metrics)}")
        
        success_rate = (
            self.test_results["passed"] / total * 100 if total > 0 else 0
        )
        
        if success_rate == 100:
            self.logger.info(f"\n🎉 ALL TESTS PASSED! ({success_rate:.0f}%)")
        elif success_rate >= 80:
            self.logger.info(f"\n✅ Tests mostly passed ({success_rate:.0f}%)")
        else:
            self.logger.error(f"\n❌ Tests failed ({success_rate:.0f}% passed)")
        
        return self.test_results["failed"] == 0


async def main():
    """Run the integration test suite."""
    test = EventFlowIntegrationTest()
    
    try:
        # Setup
        await test.setup()
        
        # Run tests
        await test.test_basic_event_flow()
        await test.test_metric_calculation()
        await test.test_concurrent_events()
        await test.test_error_handling()
        
    except Exception as e:
        test.logger.error(f"\nTest suite failed: {e}")
        test._record_fail("Test suite execution", str(e))
    
    finally:
        # Teardown
        await test.teardown()
        
        # Print summary
        success = test.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Check Redis availability
    import subprocess
    
    try:
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode != 0 or "PONG" not in result.stdout:
            print("❌ Redis is not running!")
            print("Start Redis with: docker-compose up -d redis")
            sys.exit(1)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Could not verify Redis status")
        print("Make sure Redis is running on localhost:6379")
    
    # Run tests
    print("\n🚀 Starting Analytics Integration Test\n")
    asyncio.run(main())
