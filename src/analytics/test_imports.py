#!/usr/bin/env python3
"""Test script to verify imports work correctly for Heroku deployment."""

import os
import sys

print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Test redis asyncio import
try:
    import redis.asyncio as redis
    print("✓ redis.asyncio import successful")
except ImportError as e:
    print(f"✗ redis.asyncio import failed: {e}")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test config import
try:
    from config import get_database_url
    print("✓ config.get_database_url import successful")
    print(f"  Database URL: {get_database_url()[:50]}...")
except ImportError as e:
    print(f"✗ config import failed: {e}")

# Test environment variables
print("\nEnvironment variables:")
print(f"DATABASE_URL: {'set' if os.environ.get('DATABASE_URL') else 'not set'}")
print(f"REDIS_URL: {'set' if os.environ.get('REDIS_URL') else 'not set'}")

# Test analytics service import
try:
    from analytics_services.base_analytics_service import BaseAnalyticsService
    print("\n✓ BaseAnalyticsService import successful")
except ImportError as e:
    print(f"\n✗ BaseAnalyticsService import failed: {e}")

try:
    from analytics_services.talk_time_analytics import TalkTimeAnalyticsService
    print("✓ TalkTimeAnalyticsService import successful")
except ImportError as e:
    print(f"✗ TalkTimeAnalyticsService import failed: {e}")

print("\nAll imports successful! The worker should run correctly on Heroku.")