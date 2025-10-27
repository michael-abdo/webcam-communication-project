#!/usr/bin/env python3
"""
Deployment Validation Script
Tests deployment endpoints for ChatGPT agent compatibility
"""

import requests
import json
import sys
from urllib.parse import urljoin

def validate_deployment(base_url):
    """Validate deployment endpoints."""
    print(f"🔍 Validating deployment at: {base_url}")
    print("=" * 60)
    
    tests = [
        ("Health Check", "GET", "/health", None),
        ("System Info", "GET", "/api/info", None),
        ("System Metrics", "GET", "/api/metrics", None),
        ("Fatigue Analysis", "POST", "/api/analyze", {"perclos": 0.25, "confidence": 0.95}),
    ]
    
    results = []
    
    for test_name, method, endpoint, data in tests:
        print(f"\n🧪 Testing: {test_name}")
        print(f"   {method} {endpoint}")
        
        try:
            url = urljoin(base_url, endpoint)
            
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            
            # Check response
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    print(f"   ✅ SUCCESS: {response.status_code}")
                    print(f"   📊 Response size: {len(str(json_data))} characters")
                    
                    # Check CORS headers
                    cors_headers = response.headers.get('Access-Control-Allow-Origin', 'Not set')
                    print(f"   🌐 CORS: {cors_headers}")
                    
                    results.append({
                        'test': test_name,
                        'status': 'PASS',
                        'response_code': response.status_code,
                        'cors': cors_headers
                    })
                    
                except json.JSONDecodeError:
                    print(f"   ❌ FAIL: Invalid JSON response")
                    results.append({'test': test_name, 'status': 'FAIL', 'error': 'Invalid JSON'})
            else:
                print(f"   ❌ FAIL: HTTP {response.status_code}")
                print(f"   📝 Response: {response.text[:200]}")
                results.append({'test': test_name, 'status': 'FAIL', 'error': f'HTTP {response.status_code}'})
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ FAIL: Connection error - {e}")
            results.append({'test': test_name, 'status': 'FAIL', 'error': str(e)})
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    
    for result in results:
        status_icon = "✅" if result['status'] == 'PASS' else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
        
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 DEPLOYMENT VALIDATED - Ready for ChatGPT agent access!")
        return True
    else:
        print("⚠️  DEPLOYMENT ISSUES - Please fix failed tests")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 validate_deployment.py <base_url>")
        print("Example: python3 validate_deployment.py https://your-app.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    success = validate_deployment(base_url)
    sys.exit(0 if success else 1)