#!/usr/bin/env python3
"""
Camera Quality Test
Comprehensive camera capture quality assessment
"""

import cv2
import numpy as np
import time
import json
from datetime import datetime

class CameraQualityTester:
    """Test and analyze camera capture quality."""
    
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'camera_index': camera_index,
            'tests': {}
        }
    
    def test_resolution_support(self):
        """Test different resolution support."""
        print("\n📐 Testing Resolution Support...")
        
        resolutions = [
            (320, 240, "QVGA"),
            (640, 480, "VGA"),
            (1280, 720, "HD"),
            (1920, 1080, "Full HD"),
            (3840, 2160, "4K")
        ]
        
        cap = cv2.VideoCapture(self.camera_index)
        supported = []
        
        for width, height, name in resolutions:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width == width and actual_height == height:
                ret, frame = cap.read()
                if ret:
                    supported.append({
                        'resolution': f"{width}x{height}",
                        'name': name,
                        'supported': True
                    })
                    print(f"   ✅ {name} ({width}x{height})")
                else:
                    print(f"   ⚠️  {name} ({width}x{height}) - Set but no frames")
            else:
                print(f"   ❌ {name} ({width}x{height}) - Got {actual_width}x{actual_height}")
        
        cap.release()
        self.results['tests']['resolution_support'] = supported
        return supported
    
    def test_fps_consistency(self, duration=5):
        """Test FPS consistency over time."""
        print(f"\n⏱️  Testing FPS Consistency ({duration} seconds)...")
        
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        requested_fps = 30
        cap.set(cv2.CAP_PROP_FPS, requested_fps)
        actual_fps_setting = cap.get(cv2.CAP_PROP_FPS)
        
        frame_times = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            frame_start = time.time()
            ret, frame = cap.read()
            
            if ret:
                frame_time = time.time() - frame_start
                frame_times.append(frame_time)
        
        cap.release()
        
        if frame_times:
            avg_fps = 1 / np.mean(frame_times)
            std_fps = np.std([1/t for t in frame_times])
            min_fps = 1 / max(frame_times)
            max_fps = 1 / min(frame_times)
            
            print(f"   Requested FPS: {requested_fps}")
            print(f"   Camera reported FPS: {actual_fps_setting:.1f}")
            print(f"   Measured average FPS: {avg_fps:.1f}")
            print(f"   FPS std deviation: {std_fps:.2f}")
            print(f"   Min/Max FPS: {min_fps:.1f}/{max_fps:.1f}")
            
            consistency_score = 100 - (std_fps / avg_fps * 100) if avg_fps > 0 else 0
            print(f"   Consistency score: {consistency_score:.1f}%")
            
            self.results['tests']['fps_consistency'] = {
                'average_fps': round(avg_fps, 2),
                'std_deviation': round(std_fps, 2),
                'consistency_score': round(consistency_score, 2),
                'frame_count': len(frame_times)
            }
    
    def test_image_quality(self):
        """Test image quality metrics."""
        print("\n🖼️  Testing Image Quality...")
        
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        quality_metrics = []
        
        # Capture multiple frames
        for i in range(10):
            ret, frame = cap.read()
            
            if ret and frame is not None:
                # Convert to grayscale for some metrics
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Calculate metrics
                brightness = np.mean(frame)
                contrast = np.std(gray)
                
                # Sharpness using Laplacian variance
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                sharpness = laplacian.var()
                
                # Noise estimation
                noise = self.estimate_noise(gray)
                
                quality_metrics.append({
                    'brightness': brightness,
                    'contrast': contrast,
                    'sharpness': sharpness,
                    'noise': noise
                })
        
        cap.release()
        
        if quality_metrics:
            avg_metrics = {
                'brightness': round(np.mean([m['brightness'] for m in quality_metrics]), 2),
                'contrast': round(np.mean([m['contrast'] for m in quality_metrics]), 2),
                'sharpness': round(np.mean([m['sharpness'] for m in quality_metrics]), 2),
                'noise': round(np.mean([m['noise'] for m in quality_metrics]), 4)
            }
            
            print(f"   Average brightness: {avg_metrics['brightness']} (ideal: 100-150)")
            print(f"   Average contrast: {avg_metrics['contrast']} (ideal: 40-80)")
            print(f"   Average sharpness: {avg_metrics['sharpness']} (higher is better)")
            print(f"   Estimated noise: {avg_metrics['noise']} (lower is better)")
            
            # Quality assessment
            quality_score = 0
            
            # Brightness score (0-25 points)
            if 80 <= avg_metrics['brightness'] <= 170:
                quality_score += 25
            elif 50 <= avg_metrics['brightness'] <= 200:
                quality_score += 15
            else:
                quality_score += 5
            
            # Contrast score (0-25 points)
            if 30 <= avg_metrics['contrast'] <= 100:
                quality_score += 25
            elif 20 <= avg_metrics['contrast'] <= 120:
                quality_score += 15
            else:
                quality_score += 5
            
            # Sharpness score (0-25 points)
            if avg_metrics['sharpness'] > 1000:
                quality_score += 25
            elif avg_metrics['sharpness'] > 500:
                quality_score += 15
            else:
                quality_score += 5
            
            # Noise score (0-25 points)
            if avg_metrics['noise'] < 0.01:
                quality_score += 25
            elif avg_metrics['noise'] < 0.05:
                quality_score += 15
            else:
                quality_score += 5
            
            print(f"\n   Overall quality score: {quality_score}/100")
            
            avg_metrics['quality_score'] = quality_score
            self.results['tests']['image_quality'] = avg_metrics
    
    def estimate_noise(self, image):
        """Estimate image noise level."""
        # Use difference between image and its smoothed version
        blur = cv2.GaussianBlur(image, (5, 5), 0)
        diff = cv2.absdiff(image, blur)
        return np.std(diff) / 255.0
    
    def test_low_light_performance(self):
        """Test camera performance in current lighting."""
        print("\n💡 Testing Low Light Performance...")
        
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Try to adjust exposure for low light
        cap.set(cv2.CAP_PROP_EXPOSURE, -1)  # Auto exposure
        
        low_light_frames = []
        
        for i in range(10):
            ret, frame = cap.read()
            
            if ret:
                brightness = np.mean(frame)
                
                # Check if it's actually low light
                if brightness < 50:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # Calculate SNR (Signal-to-Noise Ratio)
                    signal = np.mean(gray)
                    noise = np.std(gray)
                    snr = signal / noise if noise > 0 else 0
                    
                    low_light_frames.append({
                        'brightness': brightness,
                        'snr': snr
                    })
        
        cap.release()
        
        if low_light_frames:
            avg_brightness = np.mean([f['brightness'] for f in low_light_frames])
            avg_snr = np.mean([f['snr'] for f in low_light_frames])
            
            print(f"   Low light detected!")
            print(f"   Average brightness: {avg_brightness:.1f}")
            print(f"   Average SNR: {avg_snr:.2f}")
            
            self.results['tests']['low_light_performance'] = {
                'detected': True,
                'avg_brightness': round(avg_brightness, 2),
                'avg_snr': round(avg_snr, 2)
            }
        else:
            print(f"   Normal lighting conditions")
            self.results['tests']['low_light_performance'] = {
                'detected': False
            }
    
    def test_autofocus_speed(self):
        """Test autofocus response (if available)."""
        print("\n🔍 Testing Autofocus...")
        
        cap = cv2.VideoCapture(self.camera_index)
        
        # Check if autofocus is available
        autofocus = cap.get(cv2.CAP_PROP_AUTOFOCUS)
        
        if autofocus != -1:
            print(f"   Autofocus available: {'Yes' if autofocus else 'No'}")
            
            # Test focus changes
            sharpness_values = []
            
            for i in range(20):
                ret, frame = cap.read()
                if ret:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                    sharpness = laplacian.var()
                    sharpness_values.append(sharpness)
                
                time.sleep(0.1)
            
            if sharpness_values:
                stability = 1 - (np.std(sharpness_values) / np.mean(sharpness_values))
                print(f"   Focus stability: {stability*100:.1f}%")
                
                self.results['tests']['autofocus'] = {
                    'available': bool(autofocus),
                    'stability': round(stability * 100, 2)
                }
        else:
            print(f"   Autofocus not available")
            self.results['tests']['autofocus'] = {'available': False}
        
        cap.release()
    
    def generate_report(self):
        """Generate comprehensive quality report."""
        print("\n" + "=" * 60)
        print("📊 CAMERA QUALITY REPORT")
        print("=" * 60)
        
        print(f"\nCamera Index: {self.camera_index}")
        print(f"Test Date: {self.results['timestamp']}")
        
        # Resolution support summary
        if 'resolution_support' in self.results['tests']:
            supported_res = self.results['tests']['resolution_support']
            print(f"\n✅ Supported Resolutions: {len(supported_res)}")
            for res in supported_res:
                print(f"   - {res['name']}")
        
        # Image quality summary
        if 'image_quality' in self.results['tests']:
            quality = self.results['tests']['image_quality']
            score = quality['quality_score']
            
            print(f"\n🖼️  Image Quality Score: {score}/100")
            
            if score >= 80:
                print("   Grade: EXCELLENT")
            elif score >= 60:
                print("   Grade: GOOD")
            elif score >= 40:
                print("   Grade: FAIR")
            else:
                print("   Grade: POOR")
        
        # FPS consistency
        if 'fps_consistency' in self.results['tests']:
            fps = self.results['tests']['fps_consistency']
            print(f"\n⏱️  FPS Consistency: {fps['consistency_score']}%")
        
        # Save detailed report
        report_file = f"camera_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        return self.results

def main():
    """Run comprehensive camera quality tests."""
    print("🎥 CAMERA QUALITY TEST SUITE")
    print("Comprehensive camera capture quality assessment")
    print("=" * 60)
    
    tester = CameraQualityTester(camera_index=0)
    
    # Run all tests
    tester.test_resolution_support()
    tester.test_fps_consistency()
    tester.test_image_quality()
    tester.test_low_light_performance()
    tester.test_autofocus_speed()
    
    # Generate report
    report = tester.generate_report()
    
    print("\n✨ Quality testing complete!")

if __name__ == "__main__":
    main()