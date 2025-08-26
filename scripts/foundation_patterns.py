#!/usr/bin/env python3
"""
Foundation-First Design Patterns

Examples of how to enforce that higher-level functions 
require lower-level validations to pass first.
"""

import functools
import time
from typing import Dict, List, Callable, Any
from enum import Enum

# Pattern 1: Decorator Pattern (Recommended)
# ==========================================

class LayerStatus(Enum):
    """Status of each architectural layer."""
    UNTESTED = "untested"
    PASSED = "passed"
    FAILED = "failed"

class SystemLayers:
    """Tracks validation status of each layer."""
    def __init__(self):
        self.layers = {
            'foundation': LayerStatus.UNTESTED,
            'health': LayerStatus.UNTESTED,
            'streaming': LayerStatus.UNTESTED,
            'analysis': LayerStatus.UNTESTED
        }
        self.validation_results = {}
    
    def validate_layer(self, layer: str, passed: bool, details: dict = None):
        """Record validation result for a layer."""
        self.layers[layer] = LayerStatus.PASSED if passed else LayerStatus.FAILED
        self.validation_results[layer] = {
            'passed': passed,
            'timestamp': time.time(),
            'details': details or {}
        }
    
    def is_layer_valid(self, layer: str) -> bool:
        """Check if a layer has passed validation."""
        return self.layers.get(layer) == LayerStatus.PASSED

# Global system state
system = SystemLayers()

def requires_foundation(*required_layers: str):
    """
    Decorator that enforces layer dependencies.
    Higher functions can only run if required lower layers have passed.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check all required layers
            failed_layers = []
            for layer in required_layers:
                if not system.is_layer_valid(layer):
                    failed_layers.append(layer)
            
            if failed_layers:
                raise RuntimeError(
                    f"Cannot execute {func.__name__}: "
                    f"Required layers not validated: {failed_layers}\n"
                    f"Please validate foundation layers first!"
                )
            
            # All requirements met, execute function
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Example usage of decorator pattern:

def validate_camera_foundation() -> bool:
    """Foundation layer - camera health check."""
    print("🎯 Validating camera foundation...")
    # Simulate camera test
    camera_healthy = True  # In reality, run actual camera test
    
    system.validate_layer('foundation', camera_healthy, {
        'camera_index': 0,
        'fps': 30,
        'resolution': '640x480'
    })
    
    if camera_healthy:
        print("✅ Foundation validated")
    else:
        print("❌ Foundation failed")
    
    return camera_healthy

@requires_foundation('foundation')
def start_health_monitoring():
    """Health monitoring - requires foundation."""
    print("📊 Starting health monitoring...")
    # Simulate health monitor setup
    system.validate_layer('health', True)
    print("✅ Health monitoring active")

@requires_foundation('foundation', 'health')
def start_video_streaming():
    """Video streaming - requires foundation AND health."""
    print("📹 Starting video streaming...")
    # Simulate streaming setup
    system.validate_layer('streaming', True)
    print("✅ Video streaming active")

@requires_foundation('foundation', 'health', 'streaming')
def start_fatigue_analysis():
    """Fatigue analysis - requires ALL lower layers."""
    print("🧠 Starting fatigue analysis...")
    system.validate_layer('analysis', True)
    print("✅ Fatigue analysis active")


# Pattern 2: Context Manager Pattern
# ==================================

class FoundationContext:
    """Context manager that ensures foundation is valid."""
    
    def __init__(self, required_layers: List[str]):
        self.required_layers = required_layers
        self.validated = False
    
    def __enter__(self):
        # Validate all required layers
        for layer in self.required_layers:
            if not system.is_layer_valid(layer):
                raise RuntimeError(
                    f"Foundation requirement not met: {layer} not validated"
                )
        self.validated = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass

# Example usage:
def advanced_processing():
    """Example using context manager pattern."""
    with FoundationContext(['foundation', 'health']):
        print("Performing advanced processing...")
        # This code only runs if foundation layers are valid


# Pattern 3: Chain of Responsibility Pattern
# ==========================================

class ValidationChain:
    """Chain of validators that must pass in sequence."""
    
    def __init__(self):
        self.validators = []
        self.results = {}
    
    def add_validator(self, name: str, validator: Callable[[], bool], 
                     error_msg: str = None):
        """Add a validator to the chain."""
        self.validators.append({
            'name': name,
            'validator': validator,
            'error_msg': error_msg or f"{name} validation failed"
        })
    
    def validate_all(self) -> bool:
        """Run all validators in sequence. Stop on first failure."""
        for val in self.validators:
            print(f"Validating {val['name']}...")
            
            try:
                result = val['validator']()
                self.results[val['name']] = result
                
                if not result:
                    print(f"❌ {val['error_msg']}")
                    return False
                    
            except Exception as e:
                print(f"❌ {val['name']} validation error: {e}")
                self.results[val['name']] = False
                return False
        
        print("✅ All validations passed!")
        return True

# Example usage:
def setup_system_with_chain():
    """Example of chain validation pattern."""
    chain = ValidationChain()
    
    # Add validators in order (foundation → advanced)
    chain.add_validator('camera', validate_camera_foundation, 
                       "Camera must be working")
    chain.add_validator('permissions', lambda: True,  # Mock validator
                       "Camera permissions required")
    chain.add_validator('resources', lambda: True,  # Mock validator
                       "Sufficient system resources required")
    
    if chain.validate_all():
        print("System ready for operation!")
    else:
        print("System setup failed - fix issues and retry")


# Pattern 4: State Machine Pattern
# ================================

class SystemStateMachine:
    """State machine that enforces progression through layers."""
    
    def __init__(self):
        self.current_state = 'uninitialized'
        self.valid_transitions = {
            'uninitialized': ['foundation_testing'],
            'foundation_testing': ['foundation_valid', 'failed'],
            'foundation_valid': ['health_testing'],
            'health_testing': ['health_valid', 'failed'],
            'health_valid': ['streaming_testing'],
            'streaming_testing': ['streaming_valid', 'failed'],
            'streaming_valid': ['analysis_testing'],
            'analysis_testing': ['fully_operational', 'failed'],
            'failed': ['uninitialized'],  # Can restart
            'fully_operational': []  # Terminal state
        }
    
    def can_transition_to(self, new_state: str) -> bool:
        """Check if transition to new state is allowed."""
        return new_state in self.valid_transitions.get(self.current_state, [])
    
    def transition_to(self, new_state: str):
        """Attempt to transition to new state."""
        if not self.can_transition_to(new_state):
            raise ValueError(
                f"Invalid transition: {self.current_state} → {new_state}\n"
                f"Must follow foundation-first progression!"
            )
        
        print(f"State transition: {self.current_state} → {new_state}")
        self.current_state = new_state
    
    def must_be_in_state(self, required_state: str):
        """Enforce that system is in required state."""
        if self.current_state != required_state:
            raise RuntimeError(
                f"Operation requires state '{required_state}' "
                f"but system is in '{self.current_state}'"
            )


# Pattern 5: Dependency Injection Pattern
# =======================================

class LayerDependencies:
    """Container for validated dependencies."""
    
    def __init__(self):
        self._dependencies = {}
    
    def register(self, name: str, dependency: Any):
        """Register a validated dependency."""
        self._dependencies[name] = dependency
    
    def get(self, name: str, required: bool = True) -> Any:
        """Get a dependency, optionally requiring it exists."""
        if required and name not in self._dependencies:
            raise RuntimeError(
                f"Required dependency '{name}' not available. "
                f"Ensure lower layers are validated first!"
            )
        return self._dependencies.get(name)
    
    def require_all(self, *names: str) -> List[Any]:
        """Get multiple required dependencies."""
        return [self.get(name, required=True) for name in names]

# Global dependencies
deps = LayerDependencies()

def initialize_with_dependencies():
    """Example of dependency injection pattern."""
    # Foundation layer provides camera
    camera = "MockCamera"  # In reality, validated camera object
    deps.register('camera', camera)
    
    # Health layer requires camera
    camera = deps.get('camera')  # Will fail if not registered
    health_monitor = f"HealthMonitor(camera={camera})"
    deps.register('health_monitor', health_monitor)
    
    # Streaming requires both
    camera, monitor = deps.require_all('camera', 'health_monitor')
    print(f"Streaming initialized with: {camera}, {monitor}")


# Pattern 6: Aspect-Oriented Programming (AOP) Pattern
# ====================================================

class FoundationAspect:
    """Aspect that intercepts calls and checks preconditions."""
    
    @staticmethod
    def before_call(func_name: str, required_layers: List[str]):
        """Check preconditions before function execution."""
        print(f"[AOP] Checking prerequisites for {func_name}")
        
        for layer in required_layers:
            if not system.is_layer_valid(layer):
                raise RuntimeError(
                    f"[AOP] Precondition failed: {layer} not validated"
                )
        
        print(f"[AOP] All prerequisites met for {func_name}")


# Example: Complete System with Foundation Enforcement
# ====================================================

class IntegratedCameraSystem:
    """Complete example showing foundation-first enforcement."""
    
    def __init__(self):
        self.layers = SystemLayers()
        self.state_machine = SystemStateMachine()
        self.dependencies = LayerDependencies()
    
    def startup(self):
        """System startup with enforced progression."""
        print("\n🚀 SYSTEM STARTUP - FOUNDATION FIRST")
        print("=" * 50)
        
        try:
            # Step 1: Foundation (REQUIRED)
            self.state_machine.transition_to('foundation_testing')
            if not self._validate_foundation():
                self.state_machine.transition_to('failed')
                raise RuntimeError("Foundation validation failed!")
            self.state_machine.transition_to('foundation_valid')
            
            # Step 2: Health Monitoring (depends on foundation)
            self.state_machine.transition_to('health_testing')
            self._start_health_monitoring()  # Will fail without foundation
            self.state_machine.transition_to('health_valid')
            
            # Step 3: Video Streaming (depends on health)
            self.state_machine.transition_to('streaming_testing')
            self._start_streaming()  # Will fail without health
            self.state_machine.transition_to('streaming_valid')
            
            # Step 4: Analysis (depends on all)
            self.state_machine.transition_to('analysis_testing')
            self._start_analysis()  # Will fail without streaming
            self.state_machine.transition_to('fully_operational')
            
            print("\n✅ SYSTEM FULLY OPERATIONAL")
            
        except Exception as e:
            print(f"\n❌ STARTUP FAILED: {e}")
            return False
        
        return True
    
    def _validate_foundation(self) -> bool:
        """Validate camera foundation."""
        print("\n1️⃣ Validating Foundation...")
        
        # Simulate camera validation
        camera_valid = True  # In reality, run actual test
        
        if camera_valid:
            self.layers.validate_layer('foundation', True)
            self.dependencies.register('camera', 'CameraObject')
            print("✅ Foundation validated")
            return True
        else:
            print("❌ Foundation validation failed")
            return False
    
    @requires_foundation('foundation')
    def _start_health_monitoring(self):
        """Start health monitoring (requires foundation)."""
        print("\n2️⃣ Starting Health Monitoring...")
        
        camera = self.dependencies.get('camera')
        self.layers.validate_layer('health', True)
        self.dependencies.register('monitor', f'HealthMonitor({camera})')
        print("✅ Health monitoring started")
    
    @requires_foundation('foundation', 'health')
    def _start_streaming(self):
        """Start video streaming (requires foundation + health)."""
        print("\n3️⃣ Starting Video Streaming...")
        
        camera, monitor = self.dependencies.require_all('camera', 'monitor')
        self.layers.validate_layer('streaming', True)
        self.dependencies.register('stream', 'VideoStream')
        print("✅ Video streaming started")
    
    @requires_foundation('foundation', 'health', 'streaming')
    def _start_analysis(self):
        """Start analysis (requires all lower layers)."""
        print("\n4️⃣ Starting Analysis Engine...")
        
        self.state_machine.must_be_in_state('streaming_valid')
        stream = self.dependencies.get('stream')
        self.layers.validate_layer('analysis', True)
        print("✅ Analysis engine started")


# Main execution examples
if __name__ == '__main__':
    print("🏗️ FOUNDATION-FIRST ENFORCEMENT PATTERNS")
    print("=" * 50)
    
    # Example 1: Decorator Pattern (RECOMMENDED)
    print("\n📌 PATTERN 1: Decorator Pattern")
    print("-" * 30)
    try:
        # This will fail - foundation not validated
        start_fatigue_analysis()
    except RuntimeError as e:
        print(f"Expected error: {e}")
    
    # Validate foundation first
    validate_camera_foundation()
    
    # Now we can proceed through layers
    start_health_monitoring()
    start_video_streaming() 
    start_fatigue_analysis()
    
    # Example 2: Complete integrated system
    print("\n\n📌 INTEGRATED SYSTEM EXAMPLE")
    print("-" * 30)
    integrated_system = IntegratedCameraSystem()
    integrated_system.startup()
    
    print("\n✅ All patterns demonstrated!")
    print("Choose the pattern that best fits your architecture.")