"""Talk Time Analytics Service - tracks speaking time per participant."""

import os
import sys
# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from typing import Dict, Any, List
from datetime import datetime, timezone

from src.analytics.base_analytics_service import BaseAnalyticsService, run_service


class TalkTimeAnalyticsService(BaseAnalyticsService):
    """
    Analytics service that tracks talk time for each participant.
    
    Processes audio and transcript events to calculate:
    - Total talk time per participant
    - Participation percentage
    - Speaking equality metrics
    - Talk time distribution
    """
    
    def __init__(self, **kwargs):
        super().__init__(service_name="talk_time_analytics", **kwargs)
        
        # Track active speakers per session
        self.active_speakers: Dict[str, Dict[str, float]] = {}
        
    def get_event_types(self) -> List[str]:
        """Subscribe to audio and transcript events."""
        return ["audio", "transcript"]
    
    async def process_event(self, event: Dict[str, Any], event_type: str):
        """Process audio and transcript events."""
        if event_type == "audio":
            await self.process_audio_event(event)
        elif event_type == "transcript":
            await self.process_transcript_event(event)
            
    async def process_audio_event(self, event: Dict[str, Any]):
        """
        Process audio chunks to track speaking time.
        
        Audio events contain duration information that we can use
        to accurately track how long each participant speaks.
        """
        session_id = event["sessionId"]
        data = event["data"]
        participant_id = data.get("participantId")
        
        if not participant_id:
            self.logger.warning(f"Audio event without participant_id: {event['eventId']}")
            return
            
        # Duration in milliseconds from audio chunk
        duration_ms = data.get("duration", 0)
        duration_seconds = duration_ms / 1000.0
        
        # Increment talk time counter
        current_time = await self.increment_counter(
            "talk_time_seconds",
            session_id,
            participant_id,
            duration_seconds
        )
        
        # Track in memory for percentage calculation
        if session_id not in self.active_speakers:
            self.active_speakers[session_id] = {}
            
        if participant_id not in self.active_speakers[session_id]:
            self.active_speakers[session_id][participant_id] = 0
            
        self.active_speakers[session_id][participant_id] += duration_seconds
        
        # Publish individual metric
        await self.publish_metric(
            "talk_time_seconds",
            current_time,
            session_id,
            participant_id,
            tags={
                "user_name": data.get("userName", "Unknown"),
                "user_id": str(data.get("userId", "")),
            }
        )
        
        # Calculate and publish participation percentage
        await self.calculate_participation_percentage(session_id, participant_id)
        
        # Log for debugging
        self.logger.debug(
            f"Participant {participant_id} spoke for {duration_seconds:.2f}s "
            f"(total: {current_time}s)"
        )
        
    async def process_transcript_event(self, event: Dict[str, Any]):
        """
        Process transcript events for additional metrics.
        
        Transcripts give us text-based metrics like words spoken.
        """
        session_id = event["sessionId"]
        data = event["data"]
        participant_id = data.get("participantId")
        
        if not participant_id:
            return
            
        text = data.get("text", "")
        word_count = len(text.split())
        
        # Track words spoken
        total_words = await self.increment_counter(
            "words_spoken",
            session_id,
            participant_id,
            word_count
        )
        
        # Publish metric
        await self.publish_metric(
            "words_spoken",
            total_words,
            session_id,
            participant_id,
            tags={
                "user_name": data.get("userName", "Unknown"),
            }
        )
        
    async def calculate_participation_percentage(
        self,
        session_id: str,
        participant_id: str
    ):
        """Calculate and publish participation percentage."""
        if session_id not in self.active_speakers:
            return
            
        speakers = self.active_speakers[session_id]
        total_time = sum(speakers.values())
        
        if total_time == 0:
            return
            
        participant_time = speakers.get(participant_id, 0)
        percentage = (participant_time / total_time) * 100
        
        # Publish percentage metric
        await self.publish_metric(
            "participation_percentage",
            round(percentage, 2),
            session_id,
            participant_id,
            tags={
                "total_speakers": str(len(speakers)),
            }
        )
        
        # Calculate and publish equality metric (Gini coefficient)
        if len(speakers) >= 2:
            gini = self.calculate_gini_coefficient(list(speakers.values()))
            await self.publish_metric(
                "talk_time_equality",
                round(1 - gini, 3),  # Convert to equality (0=unequal, 1=equal)
                session_id,
                tags={
                    "participant_count": str(len(speakers)),
                }
            )
            
    def calculate_gini_coefficient(self, values: List[float]) -> float:
        """
        Calculate Gini coefficient for talk time distribution.
        
        0 = perfect equality (everyone talks the same amount)
        1 = perfect inequality (one person talks the entire time)
        """
        if not values or sum(values) == 0:
            return 0.0
            
        # Sort values
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Calculate Gini
        cumsum = 0
        for i, value in enumerate(sorted_values):
            cumsum += value * (n - i)
            
        total = sum(sorted_values)
        gini = (n + 1 - 2 * cumsum / total) / n
        
        return max(0, min(1, gini))  # Ensure between 0 and 1
    
    async def store_metric(self, metric: Dict[str, Any]):
        """Store metric in database."""
        # In production, this would insert into a time-series table
        # For now, just log it
        self.logger.info(f"Metric stored: {metric['metric']} = {metric['value']}")


if __name__ == "__main__":
    # Run the service with Heroku environment variables
    redis_url = os.environ.get('REDIS_URL')
    if redis_url and redis_url.startswith('redis://'):
        # Heroku Redis uses redis:// but redis-py 5.x requires rediss:// for TLS
        # Check if this is a Heroku Redis instance (they use TLS on port 6380)
        if ':6380' in redis_url or 'amazonaws.com' in redis_url:
            redis_url = redis_url.replace('redis://', 'rediss://', 1)
    
    run_service(
        TalkTimeAnalyticsService,
        redis_url=redis_url,
        log_level=os.environ.get('LOG_LEVEL', 'INFO')
    )