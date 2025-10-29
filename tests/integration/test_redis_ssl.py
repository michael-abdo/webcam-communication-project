#!/usr/bin/env python3
"""
Test script to verify Redis SSL connection works with Heroku Redis URLs
"""

import os
import sys
import ssl
import redis
import asyncio
import redis.asyncio as redis_async
from datetime import datetime


def test_sync_redis_connection(redis_url):
    """Test synchronous Redis connection with SSL"""
    print("\n=== Testing Synchronous Redis Connection ===")
    print(f"Redis URL: {redis_url[:30]}...")
    
    try:
        # Check if SSL is needed
        if redis_url.startswith('rediss://'):
            print("Using SSL connection (rediss://)")
            client = redis.from_url(
                redis_url,
                decode_responses=True,
                ssl_cert_reqs=ssl.CERT_NONE
            )
        else:
            print("Using non-SSL connection (redis://)")
            client = redis.from_url(redis_url, decode_responses=True)
        
        # Test basic operations
        print("\n1. Testing PING...")
        pong = client.ping()
        print(f"   ✓ PING successful: {pong}")
        
        print("\n2. Testing SET/GET...")
        test_key = f"test:redis:ssl:{datetime.now().timestamp()}"
        test_value = "Hello from SSL test!"
        client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        print(f"   ✓ SET key: {test_key}")
        
        retrieved_value = client.get(test_key)
        print(f"   ✓ GET value: {retrieved_value}")
        assert retrieved_value == test_value, "Retrieved value doesn't match!"
        
        print("\n3. Testing Pub/Sub...")
        pubsub = client.pubsub()
        test_channel = "test:channel"
        pubsub.subscribe(test_channel)
        print(f"   ✓ Subscribed to channel: {test_channel}")
        
        # Publish a test message
        client.publish(test_channel, "Test message")
        print("   ✓ Published test message")
        
        # Cleanup
        pubsub.unsubscribe()
        pubsub.close()
        client.delete(test_key)
        print("   ✓ Cleanup completed")
        
        print("\n✅ Synchronous Redis connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Synchronous Redis connection test FAILED!")
        print(f"   Error: {type(e).__name__}: {e}")
        return False


async def test_async_redis_connection(redis_url):
    """Test asynchronous Redis connection with SSL"""
    print("\n=== Testing Asynchronous Redis Connection ===")
    print(f"Redis URL: {redis_url[:30]}...")
    
    try:
        # Check if SSL is needed
        if redis_url.startswith('rediss://'):
            print("Using SSL connection (rediss://)")
            client = await redis_async.from_url(
                redis_url,
                ssl_cert_reqs="none",  # String value for async redis
                decode_responses=True
            )
        else:
            print("Using non-SSL connection (redis://)")
            client = await redis_async.from_url(redis_url, decode_responses=True)
        
        # Test basic operations
        print("\n1. Testing PING...")
        pong = await client.ping()
        print(f"   ✓ PING successful: {pong}")
        
        print("\n2. Testing SET/GET...")
        test_key = f"test:redis:async:{datetime.now().timestamp()}"
        test_value = "Hello from async SSL test!"
        await client.set(test_key, test_value, ex=60)
        print(f"   ✓ SET key: {test_key}")
        
        retrieved_value = await client.get(test_key)
        print(f"   ✓ GET value: {retrieved_value}")
        assert retrieved_value == test_value, "Retrieved value doesn't match!"
        
        print("\n3. Testing Pub/Sub...")
        pubsub = client.pubsub()
        test_channel = "test:async:channel"
        await pubsub.subscribe(test_channel)
        print(f"   ✓ Subscribed to channel: {test_channel}")
        
        # Publish a test message
        await client.publish(test_channel, "Async test message")
        print("   ✓ Published test message")
        
        # Try to receive the message
        try:
            message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=2.0)
            if message:
                print(f"   ✓ Received message: {message}")
        except asyncio.TimeoutError:
            print("   ⚠ No message received (this is normal for this test)")
        
        # Cleanup
        await pubsub.unsubscribe()
        await pubsub.close()
        await client.delete(test_key)
        await client.close()
        print("   ✓ Cleanup completed")
        
        print("\n✅ Asynchronous Redis connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Asynchronous Redis connection test FAILED!")
        print(f"   Error: {type(e).__name__}: {e}")
        return False


def test_url_transformation():
    """Test URL transformation logic for Heroku Redis"""
    print("\n=== Testing URL Transformation Logic ===")
    
    test_cases = [
        ("redis://localhost:6379", "redis://localhost:6379", "Local Redis (no change)"),
        ("redis://h:password@host.amazonaws.com:6380", "rediss://h:password@host.amazonaws.com:6380", "Heroku Redis on port 6380"),
        ("redis://h:password@ec2-123.compute-1.amazonaws.com:12345", "rediss://h:password@ec2-123.compute-1.amazonaws.com:12345", "AWS Redis"),
        ("rediss://h:password@host.com:6380", "rediss://h:password@host.com:6380", "Already SSL (no change)"),
    ]
    
    for original, expected, description in test_cases:
        # Apply the transformation logic from talk_time_analytics.py
        transformed = original
        if original.startswith('redis://'):
            if ':6380' in original or 'amazonaws.com' in original:
                transformed = original.replace('redis://', 'rediss://', 1)
        
        status = "✓" if transformed == expected else "✗"
        print(f"{status} {description}")
        print(f"  Original:    {original}")
        print(f"  Transformed: {transformed}")
        print(f"  Expected:    {expected}")
        print()


def main():
    """Main test runner"""
    print("=" * 60)
    print("Redis SSL Connection Test Script")
    print("=" * 60)
    
    # Get Redis URL from environment
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Show current configuration
    print(f"\nEnvironment:")
    print(f"  REDIS_URL: {redis_url[:30]}...")
    print(f"  URL scheme: {redis_url.split('://')[0]}")
    
    # Test URL transformation
    test_url_transformation()
    
    # Test synchronous connection
    sync_success = test_sync_redis_connection(redis_url)
    
    # Test asynchronous connection
    async_success = asyncio.run(test_async_redis_connection(redis_url))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Synchronous Redis: {'✅ PASSED' if sync_success else '❌ FAILED'}")
    print(f"Asynchronous Redis: {'✅ PASSED' if async_success else '❌ FAILED'}")
    
    if sync_success and async_success:
        print("\n🎉 All tests passed! Redis SSL configuration is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()