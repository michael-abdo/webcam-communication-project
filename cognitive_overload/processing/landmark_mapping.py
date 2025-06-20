#!/usr/bin/env python3
"""
MediaPipe Face Mesh Landmark Mapping for Cognitive Overload Detection

This module provides comprehensive mapping of MediaPipe Face Mesh landmarks 
to specific facial features relevant for cognitive overload detection.

Based on MediaPipe Face Mesh canonical landmark numbering (468 points + iris).
"""

from typing import List, Dict, Tuple, Any
import numpy as np
import math

class CognitiveLandmarkMapper:
    """
    Maps MediaPipe Face Mesh landmarks to cognitive overload indicators.
    """
    
    def __init__(self):
        """Initialize landmark mappings for cognitive overload detection."""
        
        # MediaPipe Face Mesh landmark indices for key facial features
        # Based on canonical face model with 468 landmarks
        
        # EYEBROW LANDMARKS (for brow furrow detection)
        self.left_eyebrow_landmarks = [46, 53, 52, 51, 48]  # Left eyebrow contour
        self.right_eyebrow_landmarks = [276, 283, 282, 295, 285]  # Right eyebrow contour
        self.eyebrow_center_landmarks = [9, 10, 151]  # Center forehead points
        
        # EYE LANDMARKS (for eye strain detection)
        self.left_eye_landmarks = {
            'upper_lid': [159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7],
            'lower_lid': [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
            'inner_corner': [33],
            'outer_corner': [133],
            'center': [168]  # Approximate eye center
        }
        
        self.right_eye_landmarks = {
            'upper_lid': [386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249],
            'lower_lid': [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466],
            'inner_corner': [263],
            'outer_corner': [362],
            'center': [473]  # Approximate eye center
        }
        
        # IRIS LANDMARKS (for pupil/iris tracking - requires refine_landmarks=True)
        self.left_iris_landmarks = [468, 469, 470, 471, 472]  # Left iris (5 points)
        self.right_iris_landmarks = [473, 474, 475, 476, 477]  # Right iris (5 points)
        
        # MOUTH LANDMARKS (for mouth tension detection)
        self.mouth_landmarks = {
            'outer_lip': [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318],
            'upper_lip': [61, 84, 17, 314, 405, 320, 307, 375, 291, 303, 267, 269, 270, 267, 271, 272],
            'lower_lip': [146, 91, 181, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318],
            'corners': [61, 291],  # Left and right mouth corners
            'center_top': [13],
            'center_bottom': [14]
        }
        
        # NOSE LANDMARKS (for reference points)
        self.nose_landmarks = {
            'tip': [1],
            'bridge': [9, 10, 151],
            'nostrils': [438, 439, 218, 219]
        }
        
        # FACE CONTOUR (for overall face tracking)
        self.face_contour_landmarks = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
        
        # COGNITIVE OVERLOAD FEATURE GROUPS
        self.cognitive_features = {
            'brow_furrow': {
                'landmarks': self.left_eyebrow_landmarks + self.right_eyebrow_landmarks + self.eyebrow_center_landmarks,
                'description': 'Eyebrow landmarks for detecting forehead tension and brow furrowing'
            },
            'eye_strain': {
                'landmarks': (self.left_eye_landmarks['upper_lid'] + self.left_eye_landmarks['lower_lid'] + 
                             self.right_eye_landmarks['upper_lid'] + self.right_eye_landmarks['lower_lid']),
                'description': 'Eye landmarks for detecting eye strain, squinting, and eyelid tension'
            },
            'mouth_tension': {
                'landmarks': self.mouth_landmarks['outer_lip'] + self.mouth_landmarks['corners'],
                'description': 'Mouth landmarks for detecting lip compression and jaw tension'
            },
            'overall_stress': {
                'landmarks': self.face_contour_landmarks,
                'description': 'Face contour for overall facial tension and micro-expression changes'
            }
        }
    
    def get_landmark_group(self, group_name: str) -> List[int]:
        """
        Get landmark indices for a specific facial feature group.
        
        Args:
            group_name (str): Name of the landmark group
            
        Returns:
            List[int]: List of landmark indices
        """
        group_mapping = {
            'left_eyebrow': self.left_eyebrow_landmarks,
            'right_eyebrow': self.right_eyebrow_landmarks,
            'left_eye_upper': self.left_eye_landmarks['upper_lid'],
            'left_eye_lower': self.left_eye_landmarks['lower_lid'],
            'right_eye_upper': self.right_eye_landmarks['upper_lid'],
            'right_eye_lower': self.right_eye_landmarks['lower_lid'],
            'left_iris': self.left_iris_landmarks,
            'right_iris': self.right_iris_landmarks,
            'mouth_outer': self.mouth_landmarks['outer_lip'],
            'mouth_corners': self.mouth_landmarks['corners'],
            'nose': self.nose_landmarks['tip'] + self.nose_landmarks['bridge'],
            'face_contour': self.face_contour_landmarks
        }
        
        return group_mapping.get(group_name, [])
    
    def calculate_eyebrow_distance(self, landmarks: List[Dict]) -> float:
        """
        Calculate distance between eyebrows (brow furrow indicator).
        
        Args:
            landmarks (List[Dict]): List of all facial landmarks
            
        Returns:
            float: Distance between eyebrow centers (lower = more furrowed)
        """
        if len(landmarks) < max(self.left_eyebrow_landmarks + self.right_eyebrow_landmarks):
            return 0.0
        
        # Get center points of each eyebrow
        left_brow_points = [landmarks[i] for i in self.left_eyebrow_landmarks if i < len(landmarks)]
        right_brow_points = [landmarks[i] for i in self.right_eyebrow_landmarks if i < len(landmarks)]
        
        if not left_brow_points or not right_brow_points:
            return 0.0
        
        # Calculate average position of each eyebrow
        left_center_x = sum(p['x'] for p in left_brow_points) / len(left_brow_points)
        left_center_y = sum(p['y'] for p in left_brow_points) / len(left_brow_points)
        
        right_center_x = sum(p['x'] for p in right_brow_points) / len(right_brow_points)
        right_center_y = sum(p['y'] for p in right_brow_points) / len(right_brow_points)
        
        # Calculate distance
        distance = math.sqrt((right_center_x - left_center_x)**2 + (right_center_y - left_center_y)**2)
        return distance
    
    def calculate_eye_openness(self, landmarks: List[Dict], eye_side: str = 'left') -> float:
        """
        Calculate eye openness ratio (eye strain indicator).
        
        Args:
            landmarks (List[Dict]): List of all facial landmarks
            eye_side (str): 'left' or 'right' eye
            
        Returns:
            float: Eye openness ratio (lower = more closed/strained)
        """
        eye_landmarks = self.left_eye_landmarks if eye_side == 'left' else self.right_eye_landmarks
        
        if len(landmarks) < max(eye_landmarks['upper_lid'] + eye_landmarks['lower_lid']):
            return 0.0
        
        # Get upper and lower eyelid points
        upper_points = [landmarks[i] for i in eye_landmarks['upper_lid'] if i < len(landmarks)]
        lower_points = [landmarks[i] for i in eye_landmarks['lower_lid'] if i < len(landmarks)]
        
        if not upper_points or not lower_points:
            return 0.0
        
        # Calculate vertical eye opening (average distance between upper and lower lids)
        vertical_distances = []
        min_length = min(len(upper_points), len(lower_points))
        
        for i in range(min_length):
            upper_y = upper_points[i]['y']
            lower_y = lower_points[i]['y']
            vertical_distances.append(abs(upper_y - lower_y))
        
        if not vertical_distances:
            return 0.0
        
        avg_vertical_distance = sum(vertical_distances) / len(vertical_distances)
        
        # Calculate horizontal eye width for normalization
        inner_corner = landmarks[eye_landmarks['inner_corner'][0]]
        outer_corner = landmarks[eye_landmarks['outer_corner'][0]]
        horizontal_distance = abs(outer_corner['x'] - inner_corner['x'])
        
        if horizontal_distance == 0:
            return 0.0
        
        # Return normalized eye openness ratio
        openness_ratio = avg_vertical_distance / horizontal_distance
        return openness_ratio
    
    def calculate_mouth_compression(self, landmarks: List[Dict]) -> float:
        """
        Calculate mouth compression ratio (tension indicator).
        
        Args:
            landmarks (List[Dict]): List of all facial landmarks
            
        Returns:
            float: Mouth compression ratio (lower = more compressed)
        """
        mouth_corners = self.mouth_landmarks['corners']
        
        if len(landmarks) < max(mouth_corners):
            return 0.0
        
        # Get mouth corner positions
        left_corner = landmarks[mouth_corners[0]]
        right_corner = landmarks[mouth_corners[1]]
        
        # Calculate mouth width
        mouth_width = abs(right_corner['x'] - left_corner['x'])
        
        # Get upper and lower lip center points
        if (len(landmarks) > max(self.mouth_landmarks['center_top']) and 
            len(landmarks) > max(self.mouth_landmarks['center_bottom'])):
            
            upper_lip = landmarks[self.mouth_landmarks['center_top'][0]]
            lower_lip = landmarks[self.mouth_landmarks['center_bottom'][0]]
            mouth_height = abs(upper_lip['y'] - lower_lip['y'])
            
            if mouth_width == 0:
                return 0.0
            
            # Return width-to-height ratio (lower = more compressed)
            compression_ratio = mouth_height / mouth_width
            return compression_ratio
        
        return 0.0
    
    def validate_landmark_indices(self, total_landmarks: int) -> Dict[str, bool]:
        """
        Validate that all mapped landmark indices are within bounds.
        
        Args:
            total_landmarks (int): Total number of landmarks available
            
        Returns:
            Dict[str, bool]: Validation results for each feature group
        """
        validation_results = {}
        
        for feature_name, feature_data in self.cognitive_features.items():
            landmark_indices = feature_data['landmarks']
            max_index = max(landmark_indices) if landmark_indices else 0
            validation_results[feature_name] = max_index < total_landmarks
        
        return validation_results
    
    def get_cognitive_metrics(self, landmarks: List[Dict]) -> Dict[str, float]:
        """
        Calculate all cognitive overload metrics from landmarks.
        
        Args:
            landmarks (List[Dict]): List of all facial landmarks
            
        Returns:
            Dict[str, float]: Dictionary of cognitive overload metrics
        """
        metrics = {}
        
        try:
            # Brow furrow detection
            metrics['brow_furrow_distance'] = self.calculate_eyebrow_distance(landmarks)
            
            # Eye strain detection
            metrics['left_eye_openness'] = self.calculate_eye_openness(landmarks, 'left')
            metrics['right_eye_openness'] = self.calculate_eye_openness(landmarks, 'right')
            metrics['avg_eye_openness'] = (metrics['left_eye_openness'] + metrics['right_eye_openness']) / 2
            
            # Mouth tension detection
            metrics['mouth_compression'] = self.calculate_mouth_compression(landmarks)
            
            # Overall cognitive stress indicator (combination of metrics)
            stress_indicators = [
                1.0 - (metrics['brow_furrow_distance'] / 100.0),  # Normalized brow tension
                1.0 - metrics['avg_eye_openness'],                # Eye strain
                1.0 - metrics['mouth_compression']                # Mouth tension
            ]
            
            metrics['cognitive_stress_score'] = sum(stress_indicators) / len(stress_indicators)
            
        except Exception as e:
            print(f"Error calculating cognitive metrics: {e}")
            # Return default values on error
            metrics = {
                'brow_furrow_distance': 0.0,
                'left_eye_openness': 0.0,
                'right_eye_openness': 0.0,
                'avg_eye_openness': 0.0,
                'mouth_compression': 0.0,
                'cognitive_stress_score': 0.0
            }
        
        return metrics

def main():
    """
    Demonstrate landmark mapping functionality.
    """
    mapper = CognitiveLandmarkMapper()
    
    print("=== MEDIAPIPE FACE MESH LANDMARK MAPPING ===")
    print(f"Total cognitive feature groups: {len(mapper.cognitive_features)}")
    
    for feature_name, feature_data in mapper.cognitive_features.items():
        print(f"\n{feature_name.upper()}:")
        print(f"  Landmarks: {feature_data['landmarks']}")
        print(f"  Count: {len(feature_data['landmarks'])}")
        print(f"  Description: {feature_data['description']}")
    
    print("\n=== VALIDATION FOR 468 LANDMARKS ===")
    validation = mapper.validate_landmark_indices(468)
    for feature, is_valid in validation.items():
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{feature}: {status}")
    
    print("\n=== AVAILABLE LANDMARK GROUPS ===")
    groups = ['left_eyebrow', 'right_eyebrow', 'left_eye_upper', 'right_eye_upper', 
              'mouth_outer', 'nose', 'face_contour']
    for group in groups:
        landmarks = mapper.get_landmark_group(group)
        print(f"{group}: {len(landmarks)} landmarks")

if __name__ == "__main__":
    main()