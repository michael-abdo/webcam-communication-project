"""Base Analytics Service for processing RTMS events."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from config import DATABASE_URL
from models import SessionLocal
from models.entities import Base


class BaseAnalyticsService(ABC):
    """
    Base class for all analytics microservices.
    Handles Redis pub/sub, metric storage, and common functionality.
    """

    def __init__(
        self,
        service_name: str,
        redis_url: str = None,
        database_url: str = None,
        log_level: str = "INFO",
    ):
        self.service_name = service_name
        self.event_types: List[str] = []
        self.metrics_published = 0
        self.events_processed = 0
        
        # Setup logging
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, log_level))
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f'[%(asctime)s] [{service_name}] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Redis connection
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_client = None
        self.pubsub = None
        
        # Database connection for metrics
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(
            self.database_url,
            poolclass=NullPool,  # Disable connection pooling for async
            echo=False,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        
        # Processing state
        self.is_running = False
        self.processing_tasks = set()
        
    async def start(self):
        """Start the analytics service."""
        self.logger.info(f"Starting {self.service_name}")
        
        # Connect to Redis
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        
        # Subscribe to event channels
        channels = [f"rtms:events:{event_type}" for event_type in self.get_event_types()]
        if channels:
            await self.pubsub.subscribe(*channels)
            self.logger.info(f"Subscribed to channels: {channels}")
        
        # Start processing
        self.is_running = True
        await self.process_events()
        
    async def stop(self):
        """Gracefully stop the analytics service."""
        self.logger.info(f"Stopping {self.service_name}")
        self.is_running = False
        
        # Wait for ongoing tasks to complete
        if self.processing_tasks:
            self.logger.info(f"Waiting for {len(self.processing_tasks)} tasks to complete")
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        # Close connections
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
            
        self.logger.info(f"{self.service_name} stopped")
        
    async def process_events(self):
        """Main event processing loop."""
        try:
            async for message in self.pubsub.listen():
                if not self.is_running:
                    break
                    
                if message["type"] == "message":
                    # Process event in background task
                    task = asyncio.create_task(self._handle_message(message))
                    self.processing_tasks.add(task)
                    task.add_done_callback(self.processing_tasks.discard)
                    
        except Exception as e:
            self.logger.error(f"Event processing error: {e}", exc_info=True)
            
    async def _handle_message(self, message: Dict[str, Any]):
        """Handle a single Redis message."""
        try:
            # Parse event
            event = json.loads(message["data"])
            self.events_processed += 1
            
            # Extract event type from channel
            channel = message["channel"]
            event_type = channel.split(":")[-1]
            
            # Process event
            await self.process_event(event, event_type)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in message: {e}")
        except Exception as e:
            self.logger.error(f"Error processing event: {e}", exc_info=True)
            
    @abstractmethod
    async def process_event(self, event: Dict[str, Any], event_type: str):
        """
        Process a single event. Must be implemented by subclasses.
        
        Args:
            event: The parsed event data
            event_type: The type of event (audio, video, transcript, etc.)
        """
        pass
    
    @abstractmethod
    def get_event_types(self) -> List[str]:
        """
        Return list of event types this service processes.
        Must be implemented by subclasses.
        
        Returns:
            List of event types (e.g., ["audio", "transcript"])
        """
        pass
    
    async def publish_metric(
        self,
        metric_name: str,
        value: Any,
        session_id: str,
        participant_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Publish a computed metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            session_id: Session ID
            participant_id: Optional participant ID
            tags: Additional tags for the metric
            timestamp: Metric timestamp (defaults to now)
        """
        try:
            metric = {
                "service": self.service_name,
                "metric": metric_name,
                "value": value,
                "session_id": session_id,
                "participant_id": participant_id,
                "tags": tags or {},
                "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            }
            
            # Store in database
            await self.store_metric(metric)
            
            # Update cache for real-time access
            cache_key = f"metric:{metric_name}:{session_id}:{participant_id or 'all'}"
            cache_value = json.dumps(metric)
            
            # Set with 5 minute expiry
            await self.redis_client.setex(cache_key, 300, cache_value)
            
            # Publish to metric channel for real-time consumers
            metric_channel = f"metrics:{self.service_name}:{metric_name}"
            await self.redis_client.publish(metric_channel, cache_value)
            
            self.metrics_published += 1
            
        except Exception as e:
            self.logger.error(f"Failed to publish metric {metric_name}: {e}")
            
    async def store_metric(self, metric: Dict[str, Any]):
        """
        Store metric in database. Override for custom storage.
        
        Args:
            metric: Metric data to store
        """
        # Default implementation - can be overridden
        # This would typically insert into a time-series table
        self.logger.debug(f"Storing metric: {metric}")
        
    async def get_cached_metric(
        self,
        metric_name: str,
        session_id: str,
        participant_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached metric value.
        
        Args:
            metric_name: Name of the metric
            session_id: Session ID
            participant_id: Optional participant ID
            
        Returns:
            Cached metric data or None
        """
        cache_key = f"metric:{metric_name}:{session_id}:{participant_id or 'all'}"
        cached = await self.redis_client.get(cache_key)
        
        if cached:
            return json.loads(cached)
        return None
    
    async def increment_counter(
        self,
        counter_name: str,
        session_id: str,
        participant_id: Optional[str] = None,
        amount: int = 1,
    ) -> int:
        """
        Increment a counter metric.
        
        Args:
            counter_name: Name of the counter
            session_id: Session ID
            participant_id: Optional participant ID
            amount: Amount to increment by
            
        Returns:
            New counter value
        """
        key = f"counter:{counter_name}:{session_id}:{participant_id or 'all'}"
        new_value = await self.redis_client.incrby(key, amount)
        
        # Set expiry to 24 hours
        await self.redis_client.expire(key, 86400)
        
        return new_value
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get service metrics summary."""
        return {
            "service": self.service_name,
            "events_processed": self.events_processed,
            "metrics_published": self.metrics_published,
            "is_running": self.is_running,
            "active_tasks": len(self.processing_tasks),
        }


def run_service(service_class: type[BaseAnalyticsService], **kwargs):
    """
    Helper function to run an analytics service.
    
    Args:
        service_class: The service class to instantiate
        **kwargs: Arguments to pass to the service constructor
    """
    async def main():
        service = service_class(**kwargs)
        
        try:
            await service.start()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            await service.stop()
    
    asyncio.run(main())