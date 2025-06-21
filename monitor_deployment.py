#!/usr/bin/env python3
"""
Deployment Monitoring Tool
Monitor your Railway/Render deployment health and performance
"""

import requests
import time
import json
from datetime import datetime
import statistics
import sys

class DeploymentMonitor:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.metrics = {
            'response_times': [],
            'success_count': 0,
            'failure_count': 0,
            'error_log': []
        }
    
    def check_health(self):
        """Check health endpoint"""
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response_time = (time.time() - start) * 1000  # ms
            
            if response.status_code == 200:
                self.metrics['response_times'].append(response_time)
                self.metrics['success_count'] += 1
                return True, response_time, response.json()
            else:
                self.metrics['failure_count'] += 1
                self.metrics['error_log'].append({
                    'time': datetime.now().isoformat(),
                    'error': f'Status {response.status_code}'
                })
                return False, response_time, None
                
        except Exception as e:
            self.metrics['failure_count'] += 1
            self.metrics['error_log'].append({
                'time': datetime.now().isoformat(),
                'error': str(e)
            })
            return False, 0, None
    
    def test_analysis_endpoint(self):
        """Test fatigue analysis endpoint"""
        test_cases = [
            {"perclos": 0.1, "confidence": 0.95},   # Alert
            {"perclos": 0.25, "confidence": 0.90},  # Moderate
            {"perclos": 0.45, "confidence": 0.85},  # High
            {"perclos": 0.65, "confidence": 0.80},  # Critical
        ]
        
        results = []
        for test_data in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/api/analyze",
                    json=test_data,
                    timeout=5
                )
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        'input': test_data,
                        'output': result,
                        'success': True
                    })
                else:
                    results.append({
                        'input': test_data,
                        'success': False,
                        'error': f'Status {response.status_code}'
                    })
            except Exception as e:
                results.append({
                    'input': test_data,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def continuous_monitor(self, duration_minutes=5, interval_seconds=30):
        """Monitor deployment continuously"""
        print(f"📊 MONITORING DEPLOYMENT: {self.base_url}")
        print(f"Duration: {duration_minutes} minutes")
        print(f"Check interval: {interval_seconds} seconds")
        print("=" * 60)
        print()
        
        end_time = time.time() + (duration_minutes * 60)
        check_count = 0
        
        while time.time() < end_time:
            check_count += 1
            print(f"\n🔍 Check #{check_count} at {datetime.now().strftime('%H:%M:%S')}")
            
            # Health check
            success, response_time, data = self.check_health()
            if success:
                print(f"✅ Health: OK ({response_time:.0f}ms)")
                if data:
                    print(f"   Status: {data.get('status', 'unknown')}")
            else:
                print(f"❌ Health: FAILED")
            
            # Calculate statistics
            if self.metrics['response_times']:
                avg_time = statistics.mean(self.metrics['response_times'])
                min_time = min(self.metrics['response_times'])
                max_time = max(self.metrics['response_times'])
                
                print(f"\n📈 Statistics:")
                print(f"   Success rate: {self.metrics['success_count']}/{check_count} ({self.metrics['success_count']/check_count*100:.1f}%)")
                print(f"   Avg response: {avg_time:.0f}ms")
                print(f"   Min/Max: {min_time:.0f}ms / {max_time:.0f}ms")
            
            if check_count % 5 == 0:  # Every 5 checks, test analysis
                print(f"\n🧪 Testing analysis endpoint...")
                results = self.test_analysis_endpoint()
                success_count = sum(1 for r in results if r['success'])
                print(f"   Analysis tests: {success_count}/{len(results)} passed")
            
            # Wait for next check
            if time.time() < end_time:
                time.sleep(interval_seconds)
        
        # Final report
        self.generate_report()
    
    def generate_report(self):
        """Generate monitoring report"""
        print("\n" + "=" * 60)
        print("📊 MONITORING REPORT")
        print("=" * 60)
        
        total_checks = self.metrics['success_count'] + self.metrics['failure_count']
        uptime_percent = (self.metrics['success_count'] / total_checks * 100) if total_checks > 0 else 0
        
        print(f"\n🎯 Uptime: {uptime_percent:.1f}%")
        print(f"✅ Successful checks: {self.metrics['success_count']}")
        print(f"❌ Failed checks: {self.metrics['failure_count']}")
        
        if self.metrics['response_times']:
            print(f"\n⚡ Performance:")
            print(f"   Average response: {statistics.mean(self.metrics['response_times']):.0f}ms")
            print(f"   Median response: {statistics.median(self.metrics['response_times']):.0f}ms")
            print(f"   95th percentile: {sorted(self.metrics['response_times'])[int(len(self.metrics['response_times'])*0.95)]:.0f}ms")
        
        if self.metrics['error_log']:
            print(f"\n⚠️  Recent errors:")
            for error in self.metrics['error_log'][-5:]:  # Last 5 errors
                print(f"   {error['time']}: {error['error']}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if uptime_percent < 99:
            print("   ⚠️  Uptime below 99% - check deployment logs")
        if self.metrics['response_times'] and statistics.mean(self.metrics['response_times']) > 500:
            print("   ⚠️  High response times - consider performance optimization")
        if uptime_percent == 100 and self.metrics['response_times'] and statistics.mean(self.metrics['response_times']) < 200:
            print("   ✅ Excellent performance and reliability!")
    
    def load_test(self, concurrent_requests=10):
        """Simple load test"""
        print(f"\n🔥 LOAD TEST: {concurrent_requests} concurrent requests")
        print("=" * 60)
        
        import concurrent.futures
        
        def make_request():
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}/health", timeout=10)
                return time.time() - start, response.status_code == 200
            except:
                return None, False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        successful = sum(1 for _, success in results if success)
        times = [t for t, _ in results if t is not None]
        
        print(f"\n📊 Load Test Results:")
        print(f"   Success rate: {successful}/{concurrent_requests} ({successful/concurrent_requests*100:.0f}%)")
        if times:
            print(f"   Avg response: {statistics.mean(times)*1000:.0f}ms")
            print(f"   Max response: {max(times)*1000:.0f}ms")

def main():
    """Main monitoring flow"""
    if len(sys.argv) < 2:
        print("Usage: python3 monitor_deployment.py <deployment-url> [duration-minutes]")
        print("Example: python3 monitor_deployment.py https://my-app.railway.app 10")
        sys.exit(1)
    
    deployment_url = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # Ensure HTTPS
    if not deployment_url.startswith(('http://', 'https://')):
        deployment_url = 'https://' + deployment_url
    
    monitor = DeploymentMonitor(deployment_url)
    
    # Quick health check
    print("🏥 Quick health check...")
    success, response_time, data = monitor.check_health()
    if success:
        print(f"✅ Deployment is healthy! Response time: {response_time:.0f}ms")
    else:
        print("❌ Deployment health check failed!")
        return
    
    # Run load test
    monitor.load_test()
    
    # Start continuous monitoring
    monitor.continuous_monitor(duration_minutes=duration)

if __name__ == "__main__":
    main()