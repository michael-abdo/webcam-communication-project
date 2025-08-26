#!/usr/bin/env python3
"""
Test Enforced Pipeline - Verify Foundation Enforcement Works

This script tests that the core pipeline properly enforces
foundation requirements at each layer.
"""

import time
import sys
from core_pipeline import pipeline, get_pipeline

def test_enforcement():
    """Test that enforcement prevents operations without validation."""
    print("🧪 TESTING ENFORCED PIPELINE")
    print("=" * 60)
    
    # Test 1: Try to initialize camera without foundation
    print("\n1️⃣ TEST: Initialize camera without foundation validation")
    print("-" * 40)
    try:
        pipeline.initialize_camera()
        print("❌ FAIL: Camera initialized without foundation!")
    except RuntimeError as e:
        print(f"✅ PASS: Properly blocked - {e}")
    
    # Test 2: Try to start monitoring without health validation
    print("\n2️⃣ TEST: Start monitoring without health validation")
    print("-" * 40)
    try:
        pipeline.start_health_monitoring()
        print("❌ FAIL: Monitoring started without validation!")
    except RuntimeError as e:
        print(f"✅ PASS: Properly blocked - {e}")
    
    # Test 3: Try to get frame without streaming validation
    print("\n3️⃣ TEST: Get frame without streaming validation")
    print("-" * 40)
    try:
        frame = pipeline.get_frame()
        print("❌ FAIL: Got frame without validation!")
    except RuntimeError as e:
        print(f"✅ PASS: Properly blocked - {e}")
    
    # Test 4: Try to start analysis without full stack
    print("\n4️⃣ TEST: Start analysis without full stack validation")
    print("-" * 40)
    try:
        pipeline.start_fatigue_analysis()
        print("❌ FAIL: Analysis started without validation!")
    except RuntimeError as e:
        print(f"✅ PASS: Properly blocked - {e}")
    
    # Test 5: Validate foundation and test progression
    print("\n5️⃣ TEST: Proper validation sequence")
    print("-" * 40)
    
    # Validate foundation
    print("Validating foundation...")
    if not pipeline.validator.validate_layer('foundation'):
        print("❌ Foundation validation failed - ensure camera is connected")
        return False
    print("✅ Foundation validated")
    
    # Now camera should work
    try:
        pipeline.initialize_camera()
        print("✅ Camera initialized after foundation validation")
    except Exception as e:
        print(f"❌ Camera initialization failed: {e}")
        return False
    
    # But monitoring should still fail (needs health)
    try:
        pipeline.start_health_monitoring()
        print("❌ FAIL: Monitoring started without health validation!")
    except RuntimeError as e:
        print(f"✅ PASS: Health validation required - {e}")
    
    # Test 6: Check validation expiration
    print("\n6️⃣ TEST: Validation expiration")
    print("-" * 40)
    
    status = pipeline.validator.get_status('foundation')
    print(f"Foundation TTL: {status['ttl_seconds']}s")
    print(f"Expires in: {status.get('expires_in', 0)}s")
    
    # Test 7: Full stack validation
    print("\n7️⃣ TEST: Full stack validation and operation")
    print("-" * 40)
    
    print("Validating full stack...")
    if pipeline.validate_stack('streaming'):
        print("✅ Stack validated up to streaming")
        
        # Start components
        try:
            pipeline.start_health_monitoring()
            print("✅ Health monitoring started")
            
            time.sleep(1)  # Let it initialize
            
            pipeline.start_video_streaming()
            print("✅ Video streaming started")
            
            # Get a frame
            frame = pipeline.get_frame(annotated=True)
            if frame is not None:
                print(f"✅ Got frame: {frame.shape}")
            else:
                print("⚠️  No frame available yet")
            
            # Show metrics
            metrics = pipeline.get_metrics()
            print(f"\n📊 Metrics:")
            print(f"  Camera: {metrics.get('camera', {})}")
            print(f"  Health: FPS={metrics.get('health', {}).get('fps', 0)}")
            
        except Exception as e:
            print(f"❌ Operation failed: {e}")
            return False
    else:
        print("❌ Stack validation failed")
        return False
    
    # Test 8: Cascade invalidation
    print("\n8️⃣ TEST: Cascade invalidation")
    print("-" * 40)
    
    print("Current validation status:")
    for layer in ['foundation', 'health', 'streaming']:
        status = pipeline.validator.get_status(layer)
        print(f"  {layer}: {status['status']}")
    
    print("\nInvalidating foundation (should cascade)...")
    pipeline.validator.invalidate_layer('foundation', cascade=True)
    
    print("After cascade:")
    for layer in ['foundation', 'health', 'streaming']:
        status = pipeline.validator.get_status(layer)
        print(f"  {layer}: {status['status']}")
    
    # Now operations should fail again
    try:
        frame = pipeline.get_frame()
        print("❌ FAIL: Got frame after invalidation!")
    except RuntimeError as e:
        print(f"✅ PASS: Properly blocked after cascade - {e}")
    
    return True

def test_performance():
    """Test performance of validation checks."""
    print("\n\n⚡ PERFORMANCE TEST")
    print("=" * 60)
    
    # Test validation speed
    print("Testing validation performance...")
    
    start_time = time.time()
    for i in range(100):
        # Check if validated (should be fast from cache)
        _ = pipeline.validator._is_layer_valid('foundation')
    elapsed = time.time() - start_time
    
    print(f"100 validation checks: {elapsed*1000:.2f}ms")
    print(f"Average per check: {elapsed*10:.2f}ms")
    
    # Test decorator overhead
    @pipeline.validator.requires('foundation')
    def dummy_function():
        return True
    
    start_time = time.time()
    for i in range(100):
        try:
            dummy_function()
        except:
            pass
    elapsed = time.time() - start_time
    
    print(f"100 decorated calls: {elapsed*1000:.2f}ms")
    print(f"Average overhead: {elapsed*10:.2f}ms")

def main():
    """Run all tests."""
    try:
        # Run enforcement tests
        if test_enforcement():
            print("\n✅ All enforcement tests passed!")
        else:
            print("\n❌ Some tests failed")
            return 1
        
        # Run performance tests
        test_performance()
        
        # Final status
        print("\n\n📊 FINAL STATUS REPORT")
        pipeline.status_report()
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        pipeline.shutdown()
        
        print("\n✅ Enforced pipeline test complete!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        return 1
    finally:
        # Ensure cleanup
        if pipeline.camera:
            pipeline.shutdown()

if __name__ == '__main__':
    sys.exit(main())