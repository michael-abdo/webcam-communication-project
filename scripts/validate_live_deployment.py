#!/usr/bin/env python3
"""
Live Deployment Validation Script
Test your Railway/Render deployment
"""

import requests
import json
import sys
import time
from datetime import datetime

def test_endpoint(url, method='GET', data=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        
        # Check status code
        if response.status_code != expected_status:
            return False, f"Status {response.status_code} (expected {expected_status})"
        
        # Check JSON response
        try:
            json_data = response.json()
        except:
            return False, "Invalid JSON response"
        
        # Check CORS headers
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        if not cors_header:
            return False, "Missing CORS headers"
        
        return True, json_data
        
    except requests.exceptions.Timeout:
        return False, "Request timeout (>10s)"
    except requests.exceptions.ConnectionError:
        return False, "Connection failed"
    except Exception as e:
        return False, f"Error: {str(e)}"

def validate_deployment(base_url):
    """Validate all deployment endpoints"""
    print(f"🔍 VALIDATING DEPLOYMENT: {base_url}")
    print("=" * 60)
    print()
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    # Test results
    results = []
    all_passed = True
    
    # Test 1: Health Check
    print("1️⃣ Testing Health Endpoint...")
    success, result = test_endpoint(f"{base_url}/health")
    if success:
        print(f"   ✅ PASSED - Status: {result.get('status', 'unknown')}")
        print(f"   Fatigue System: {'Available' if result.get('fatigue_system_available') else 'Not Available'}")
    else:
        print(f"   ❌ FAILED - {result}")
        all_passed = False
    results.append(('Health Check', success))
    print()
    
    # Test 2: System Info
    print("2️⃣ Testing Info Endpoint...")
    success, result = test_endpoint(f"{base_url}/api/info")
    if success:
        print(f"   ✅ PASSED - System: {result.get('name', 'unknown')}")
        print(f"   Version: {result.get('version', 'unknown')}")
    else:
        print(f"   ❌ FAILED - {result}")
        all_passed = False
    results.append(('System Info', success))
    print()
    
    # Test 3: Metrics
    print("3️⃣ Testing Metrics Endpoint...")
    success, result = test_endpoint(f"{base_url}/api/metrics")
    if success:
        print(f"   ✅ PASSED - Metrics available")
        print(f"   Active sessions: {result.get('active_sessions', 0)}")
    else:
        print(f"   ❌ FAILED - {result}")
        all_passed = False
    results.append(('Metrics', success))
    print()
    
    # Test 4: Fatigue Analysis
    print("4️⃣ Testing Fatigue Analysis...")
    test_data = {"perclos": 0.25, "confidence": 0.95}
    success, result = test_endpoint(f"{base_url}/api/analyze", method='POST', data=test_data)
    if success:
        print(f"   ✅ PASSED - Analysis successful")
        print(f"   Fatigue Level: {result.get('fatigue_level', 'unknown')}")
        print(f"   Risk Score: {result.get('risk_score', 0)}")
    else:
        print(f"   ❌ FAILED - {result}")
        all_passed = False
    results.append(('Fatigue Analysis', success))
    print()
    
    # Test 5: HTTPS Verification
    print("5️⃣ Testing HTTPS...")
    if base_url.startswith('https://'):
        print("   ✅ PASSED - HTTPS enabled")
        results.append(('HTTPS', True))
    else:
        print("   ❌ FAILED - Not using HTTPS")
        results.append(('HTTPS', False))
        all_passed = False
    print()
    
    # Test 6: Response Time
    print("6️⃣ Testing Response Time...")
    start_time = time.time()
    success, _ = test_endpoint(f"{base_url}/health")
    response_time = (time.time() - start_time) * 1000  # ms
    
    if success and response_time < 1000:
        print(f"   ✅ PASSED - Response time: {response_time:.0f}ms")
        results.append(('Response Time', True))
    else:
        print(f"   ❌ FAILED - Response time: {response_time:.0f}ms (>1000ms)")
        results.append(('Response Time', False))
        all_passed = False
    print()
    
    # Summary
    print("=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if all_passed:
        print()
        print("🎉 DEPLOYMENT VALIDATION SUCCESSFUL!")
        print()
        print("✅ Your deployment is ready for ChatGPT integration")
        print(f"✅ Share this URL with ChatGPT: {base_url}")
        print("✅ All endpoints are responding correctly")
        print("✅ CORS is enabled for cross-origin access")
        print("✅ HTTPS is active for secure communication")
    else:
        print()
        print("⚠️  DEPLOYMENT VALIDATION FAILED")
        print("Please check the failed tests above")
    
    return all_passed

def main():
    """Main validation flow"""
    if len(sys.argv) < 2:
        print("Usage: python3 validate_live_deployment.py <deployment-url>")
        print("Example: python3 validate_live_deployment.py https://my-app.railway.app")
        sys.exit(1)
    
    deployment_url = sys.argv[1]
    
    # Ensure URL has protocol
    if not deployment_url.startswith(('http://', 'https://')):
        deployment_url = 'https://' + deployment_url
    
    # Run validation
    success = validate_deployment(deployment_url)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()