"""
Template for creating new analytics services.

To create a new service:
1. Copy this file and rename it (e.g., interruption_analytics.py)
2. Update the class name and service_name
3. Implement the get_event_types() method
4. Implement the process_event() method
5. Add any service-specific methods
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

from base_analytics_service import BaseAnalyticsService, run_service


class TemplateAnalyticsService(BaseAnalyticsService):
    """
    [SERVICE DESCRIPTION HERE]
    
    This service processes [EVENT TYPES] to calculate:
    - [METRIC 1]
    - [METRIC 2]
    - [METRIC 3]
    """
    
    def __init__(self, **kwargs):
        # TODO: Change service_name to match your service
        super().__init__(service_name="template_analytics", **kwargs)
        
        # TODO: Initialize any service-specific state
        # Example: self.state_tracking = {}
        
    def get_event_types(self) -> List[str]:
        """
        Specify which event types this service processes.
        
        Available event types:
        - "audio": Audio chunk events with duration and speaker info
        - "video": Video frame events  
        - "transcript": Transcript segments with text and speaker
        - "session": Session lifecycle events (start/stop)
        - "participant": Participant events (join/leave/mute)
        
        Returns:
            List of event types to subscribe to
        """
        # TODO: Return the event types your service needs
        return ["audio", "transcript"]  # Example
    
    async def process_event(self, event: Dict[str, Any], event_type: str):
        """
        Process incoming events.
        
        Args:
            event: The event data with structure:
                {
                    "eventId": "uuid",
                    "eventType": "audio|video|transcript|session|participant",
                    "sessionId": "session_id", 
                    "timestamp": 1234567890,
                    "data": {
                        # Event-specific data
                    },
                    "metadata": {
                        "rtmsStreamId": "stream_id",
                        "processingTime": "2024-01-01T00:00:00Z",
                        "version": "1.0"
                    }
                }
            event_type: The type of event (matches eventType field)
        """
        # TODO: Implement event processing logic
        
        # Example: Route to specific handlers
        if event_type == "audio":
            await self.process_audio_event(event)
        elif event_type == "transcript":
            await self.process_transcript_event(event)
            
    async def process_audio_event(self, event: Dict[str, Any]):
        """
        Process audio events.
        
        Audio event data structure:
        {
            "participantId": "participant_uuid",
            "userId": "zoom_user_id",
            "userName": "John Doe",
            "duration": 20,  # milliseconds
            "s3Key": "audio/session_id/chunk.pcm16",
            "size": 640,
            "sampleRate": 16000,
            "channels": 1,
            "sequenceNo": 123
        }
        """
        session_id = event["sessionId"]
        data = event["data"]
        participant_id = data.get("participantId")
        
        # TODO: Implement your audio processing logic
        
        # Example: Track something
        value = data.get("duration", 0) / 1000  # Convert to seconds
        
        # Example: Publish a metric
        await self.publish_metric(
            "example_metric",  # Metric name
            value,             # Metric value
            session_id,        # Session ID (required)
            participant_id,    # Participant ID (optional)
            tags={             # Additional tags (optional)
                "user_name": data.get("userName", "Unknown"),
            }
        )
        
    async def process_transcript_event(self, event: Dict[str, Any]):
        """
        Process transcript events.
        
        Transcript event data structure:
        {
            "participantId": "participant_uuid",
            "userId": "zoom_user_id", 
            "userName": "John Doe",
            "text": "Hello everyone",
            "startTime": 10.5,  # seconds
            "endTime": 12.3,    # seconds
            "confidence": 0.95,
            "language": "en"
        }
        """
        session_id = event["sessionId"]
        data = event["data"]
        
        # TODO: Implement your transcript processing logic
        
        # Example: Count words
        text = data.get("text", "")
        word_count = len(text.split())
        
        # Example: Use increment_counter for cumulative metrics
        total_words = await self.increment_counter(
            "words_count",
            session_id,
            data.get("participantId"),
            word_count
        )
        
    # TODO: Add any service-specific helper methods
    
    async def calculate_custom_metric(self, session_id: str):
        """Example of a custom calculation method."""
        # Get cached values
        cached = await self.get_cached_metric("example_metric", session_id)
        
        # Perform calculations
        # ...
        
        # Publish results
        await self.publish_metric(
            "calculated_metric",
            calculated_value,
            session_id
        )
        
    async def store_metric(self, metric: Dict[str, Any]):
        """
        Override to customize metric storage.
        
        Default implementation logs metrics.
        In production, insert into time-series database.
        """
        # TODO: Implement database storage if needed
        self.logger.info(f"Metric: {metric['metric']} = {metric['value']}")


# Service-specific configuration
SERVICE_CONFIG = {
    # Add any service-specific configuration here
    "threshold": 0.5,
    "window_size": 60,  # seconds
}


if __name__ == "__main__":
    # Run the service
    # TODO: Update with your service class name
    run_service(
        TemplateAnalyticsService,
        # Override default configuration
        redis_url="redis://localhost:6379",
        log_level="INFO",
        **SERVICE_CONFIG
    )