"""Test loader utility for loading and validating test definitions."""

import json
import os
from pathlib import Path


class TestLoader:
    """Loads and manages test definitions from JSON files."""
    
    def __init__(self, definitions_path='tests/definitions'):
        self.definitions_path = Path(definitions_path)
        self._tests_cache = {}
        
    def get_available_tests(self):
        """Get list of all available tests."""
        tests = []
        
        # Scan all category directories
        for category_dir in self.definitions_path.iterdir():
            if category_dir.is_dir() and category_dir.name != '__pycache__':
                # Scan JSON files in each category
                for test_file in category_dir.glob('*.json'):
                    if test_file.name != 'test_schema.json':
                        try:
                            # Load basic test info
                            with open(test_file, 'r') as f:
                                test_data = json.load(f)
                                tests.append({
                                    'test_id': test_data.get('test_id'),
                                    'title': test_data.get('title'),
                                    'description': test_data.get('description'),
                                    'category': test_data.get('category'),
                                    'duration_minutes': test_data.get('duration_minutes', 0),
                                    'question_count': len(test_data.get('questions', [])),
                                    'file_path': str(test_file)
                                })
                        except Exception as e:
                            print(f"Error loading test {test_file}: {e}")
                            
        return sorted(tests, key=lambda x: x.get('category', ''))
    
    def load_test(self, test_id):
        """Load a specific test by ID."""
        # Check cache first
        if test_id in self._tests_cache:
            return self._tests_cache[test_id]
            
        # Search for test file
        for category_dir in self.definitions_path.iterdir():
            if category_dir.is_dir():
                for test_file in category_dir.glob('*.json'):
                    if test_file.name != 'test_schema.json':
                        try:
                            with open(test_file, 'r') as f:
                                test_data = json.load(f)
                                if test_data.get('test_id') == test_id:
                                    # Cache and return
                                    self._tests_cache[test_id] = test_data
                                    return test_data
                        except Exception as e:
                            print(f"Error loading test {test_file}: {e}")
                            
        return None
    
    def validate_test(self, test_data):
        """Basic validation of test structure."""
        required_fields = ['test_id', 'title', 'description', 'questions']
        
        for field in required_fields:
            if field not in test_data:
                return False, f"Missing required field: {field}"
                
        if not test_data.get('questions'):
            return False, "Test must have at least one question"
            
        # Validate each question
        for i, question in enumerate(test_data['questions']):
            if 'id' not in question:
                return False, f"Question {i} missing 'id' field"
            if 'type' not in question:
                return False, f"Question {i} missing 'type' field"
            if 'question' not in question:
                return False, f"Question {i} missing 'question' field"
                
        return True, "Valid"