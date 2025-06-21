#!/usr/bin/env python3
"""
Foundation Enforcer for Camera System

Practical implementation of foundation-first validation
that ensures higher functions require lower validations.
"""

import functools
import time
import json
import os
from typing import Dict, Optional, Callable, Any
from datetime import datetime
from enum import Enum

# Import camera test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.quick_camera_test import test_camera


class ValidationStatus(Enum):
    """Status of validation layers."""
    NOT_VALIDATED = "not_validated"
    VALIDATING = "validating"
    PASSED = "passed"
    FAILED = "failed"
    EXPIRED = "expired"


class FoundationValidator:
    """
    Singleton validator that tracks all layer validations
    and enforces dependencies.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.validations = {
            'foundation': {
                'status': ValidationStatus.NOT_VALIDATED,
                'timestamp': None,
                'details': {},
                'dependencies': [],
                'ttl_seconds': 300  # 5 minute validity
            },
            'health': {
                'status': ValidationStatus.NOT_VALIDATED,
                'timestamp': None,
                'details': {},
                'dependencies': ['foundation'],
                'ttl_seconds': 60  # 1 minute validity
            },
            'streaming': {
                'status': ValidationStatus.NOT_VALIDATED,
                'timestamp': None,
                'details': {},
                'dependencies': ['foundation', 'health'],
                'ttl_seconds': 30  # 30 second validity
            },
            'analysis': {
                'status': ValidationStatus.NOT_VALIDATED,
                'timestamp': None,
                'details': {},
                'dependencies': ['foundation', 'health', 'streaming'],
                'ttl_seconds': 30  # 30 second validity
            }
        }
        
        self._validation_callbacks = {}
        self._cache_file = '.foundation_cache.json'
        self._load_cache()
        self._initialized = True
    
    def _load_cache(self):
        """Load validation cache from disk."""
        # Disable cache loading for now to ensure fresh validations
        return
        
        if os.path.exists(self._cache_file):
            try:
                with open(self._cache_file, 'r') as f:
                    cache = json.load(f)
                    # Only load non-expired validations
                    for layer, data in cache.items():
                        if layer in self.validations and data.get('timestamp'):
                            age = time.time() - data['timestamp']
                            ttl = self.validations[layer]['ttl_seconds']
                            if age < ttl:
                                self.validations[layer].update({
                                    'status': ValidationStatus(data['status']),
                                    'timestamp': data['timestamp'],
                                    'details': data.get('details', {})
                                })
            except:
                pass  # Ignore cache errors
    
    def _save_cache(self):
        """Save validation cache to disk."""
        cache = {}
        for layer, data in self.validations.items():
            if data['status'] == ValidationStatus.PASSED:
                cache[layer] = {
                    'status': data['status'].value,
                    'timestamp': data['timestamp'],
                    'details': data['details']
                }
        
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(cache, f)
        except:
            pass  # Ignore cache errors
    
    def register_validator(self, layer: str, validator: Callable[[], Dict[str, Any]]):
        """Register a validation function for a layer."""
        self._validation_callbacks[layer] = validator
    
    def validate_layer(self, layer: str, force: bool = False) -> bool:
        """
        Validate a specific layer, checking dependencies first.
        Returns True if validation passes.
        """
        if layer not in self.validations:
            raise ValueError(f"Unknown layer: {layer}")
        
        # Check if already valid and not expired
        if not force and self._is_layer_valid(layer):
            return True
        
        # Check dependencies first
        layer_config = self.validations[layer]
        for dep in layer_config['dependencies']:
            if not self.validate_layer(dep, force=False):
                print(f"❌ Cannot validate {layer}: dependency {dep} failed")
                return False
        
        # Mark as validating
        layer_config['status'] = ValidationStatus.VALIDATING
        
        # Run validation
        print(f"🔍 Validating {layer}...")
        
        try:
            if layer in self._validation_callbacks:
                result = self._validation_callbacks[layer]()
            else:
                # Default validators
                if layer == 'foundation':
                    result = self._validate_foundation()
                else:
                    result = {'success': True, 'details': {}}
            
            if result['success']:
                layer_config['status'] = ValidationStatus.PASSED
                layer_config['timestamp'] = time.time()
                layer_config['details'] = result.get('details', {})
                self._save_cache()
                print(f"✅ {layer} validation PASSED")
                return True
            else:
                layer_config['status'] = ValidationStatus.FAILED
                layer_config['details'] = result.get('details', {})
                print(f"❌ {layer} validation FAILED")
                return False
                
        except Exception as e:
            layer_config['status'] = ValidationStatus.FAILED
            layer_config['details'] = {'error': str(e)}
            print(f"❌ {layer} validation ERROR: {e}")
            return False
    
    def _validate_foundation(self) -> Dict[str, Any]:
        """Built-in foundation validator."""
        try:
            # Run actual camera test
            camera_healthy = test_camera(0)
            
            return {
                'success': camera_healthy,
                'details': {
                    'camera_index': 0,
                    'test_time': datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {
                'success': False,
                'details': {'error': str(e)}
            }
    
    def _is_layer_valid(self, layer: str) -> bool:
        """Check if layer is valid and not expired."""
        config = self.validations[layer]
        
        if config['status'] != ValidationStatus.PASSED:
            return False
        
        if config['timestamp'] is None:
            return False
        
        # Check TTL
        age = time.time() - config['timestamp']
        if age > config['ttl_seconds']:
            config['status'] = ValidationStatus.EXPIRED
            return False
        
        return True
    
    def get_status(self, layer: str) -> Dict[str, Any]:
        """Get detailed status of a layer."""
        if layer not in self.validations:
            return {'error': 'Unknown layer'}
        
        config = self.validations[layer]
        
        status = {
            'layer': layer,
            'status': config['status'].value,
            'valid': self._is_layer_valid(layer),
            'dependencies': config['dependencies'],
            'details': config['details']
        }
        
        if config['timestamp']:
            age = time.time() - config['timestamp']
            status['age_seconds'] = round(age, 1)
            status['ttl_seconds'] = config['ttl_seconds']
            status['expires_in'] = max(0, round(config['ttl_seconds'] - age, 1))
        
        return status
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all layers."""
        return {
            layer: self.get_status(layer)
            for layer in self.validations
        }
    
    def invalidate_layer(self, layer: str, cascade: bool = True):
        """Invalidate a layer and optionally its dependents."""
        if layer not in self.validations:
            return
        
        self.validations[layer]['status'] = ValidationStatus.NOT_VALIDATED
        self.validations[layer]['timestamp'] = None
        
        if cascade:
            # Invalidate all layers that depend on this one
            for other_layer, config in self.validations.items():
                if layer in config['dependencies']:
                    self.invalidate_layer(other_layer, cascade=True)


# Global validator instance
validator = FoundationValidator()


def requires(*layers: str, force: bool = False):
    """
    Decorator that enforces layer dependencies.
    
    Usage:
        @requires('foundation', 'health')
        def my_streaming_function():
            # This will only run if foundation and health are validated
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validate all required layers
            failed_layers = []
            
            for layer in layers:
                if not validator.validate_layer(layer, force=force):
                    failed_layers.append(layer)
            
            if failed_layers:
                error_msg = (
                    f"Cannot execute '{func.__name__}': "
                    f"Required validations failed: {failed_layers}\n"
                )
                
                # Add helpful status info
                for layer in failed_layers:
                    status = validator.get_status(layer)
                    error_msg += f"  - {layer}: {status['status']}\n"
                
                raise RuntimeError(error_msg)
            
            # All validations passed, execute function
            return func(*args, **kwargs)
        
        # Add validation info to function
        wrapper.required_layers = layers
        wrapper.validator = validator
        
        return wrapper
    return decorator


def with_foundation(layers: list, on_failure: Callable = None):
    """
    Context manager that ensures foundation layers are valid.
    
    Usage:
        with with_foundation(['foundation', 'health']):
            # Code here only runs if layers are valid
            perform_streaming()
    """
    class FoundationContext:
        def __enter__(self):
            for layer in layers:
                if not validator.validate_layer(layer):
                    if on_failure:
                        on_failure(layer)
                    raise RuntimeError(f"Foundation requirement failed: {layer}")
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    
    return FoundationContext()


# Example usage functions

@requires('foundation')
def initialize_camera():
    """Example: Initialize camera (requires foundation)."""
    print("📷 Initializing camera...")
    return "Camera initialized"


@requires('foundation', 'health')
def start_monitoring():
    """Example: Start monitoring (requires foundation + health)."""
    print("📊 Starting health monitoring...")
    return "Monitoring active"


@requires('foundation', 'health', 'streaming')
def analyze_video():
    """Example: Analyze video (requires all lower layers)."""
    print("🧠 Analyzing video stream...")
    return "Analysis running"


# Practical camera system implementation

class CameraSystem:
    """Example system using foundation enforcement."""
    
    def __init__(self):
        self.validator = validator
        self.components = {}
    
    @requires('foundation')
    def get_camera(self):
        """Get camera instance (requires foundation)."""
        if 'camera' not in self.components:
            print("Creating camera instance...")
            self.components['camera'] = "CameraObject"
        return self.components['camera']
    
    @requires('foundation', 'health')
    def get_monitor(self):
        """Get health monitor (requires foundation + health)."""
        if 'monitor' not in self.components:
            camera = self.get_camera()
            print(f"Creating monitor for {camera}...")
            self.components['monitor'] = f"Monitor({camera})"
        return self.components['monitor']
    
    @requires('foundation', 'health', 'streaming')
    def get_stream(self):
        """Get video stream (requires all prerequisites)."""
        if 'stream' not in self.components:
            monitor = self.get_monitor()
            print(f"Creating stream with {monitor}...")
            self.components['stream'] = "VideoStream"
        return self.components['stream']
    
    def status_report(self):
        """Show complete system status."""
        print("\n📊 SYSTEM STATUS REPORT")
        print("=" * 50)
        
        all_status = self.validator.get_all_status()
        
        for layer, status in all_status.items():
            icon = "✅" if status['valid'] else "❌"
            print(f"{icon} {layer.upper()}: {status['status']}")
            
            if status.get('expires_in'):
                print(f"   Expires in: {status['expires_in']}s")
            
            if status['dependencies']:
                print(f"   Dependencies: {', '.join(status['dependencies'])}")
            
            if status.get('details'):
                print(f"   Details: {status['details']}")
            
            print()


# Test script
if __name__ == '__main__':
    print("🏗️ FOUNDATION ENFORCEMENT DEMONSTRATION")
    print("=" * 50)
    
    system = CameraSystem()
    
    # Try to use high-level function without foundation
    print("\n1️⃣ Attempting to analyze without foundation...")
    try:
        analyze_video()
    except RuntimeError as e:
        print(f"Expected error:\n{e}")
    
    # Show system status
    system.status_report()
    
    # Now properly validate from foundation up
    print("\n2️⃣ Proper validation sequence...")
    
    # This will trigger foundation validation
    try:
        camera = system.get_camera()
        print(f"Got camera: {camera}")
    except RuntimeError as e:
        print(f"Camera initialization failed: {e}")
        print("Please ensure camera is connected and try again")
        exit(1)
    
    # Register additional validators
    validator.register_validator('health', 
        lambda: {'success': True, 'details': {'cpu': '15%', 'memory': '250MB'}}
    )
    validator.register_validator('streaming',
        lambda: {'success': True, 'details': {'fps': 30, 'resolution': '640x480'}}
    )
    
    # Now we can progress through layers
    monitor = system.get_monitor()
    stream = system.get_stream()
    
    # Finally we can analyze
    result = analyze_video()
    print(f"Result: {result}")
    
    # Show final status
    system.status_report()
    
    print("\n✅ Foundation enforcement working correctly!")