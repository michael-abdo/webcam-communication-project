"""
Assessment Scoring Module

Calculates scores for various assessment types based on test definitions
and user responses.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def load_test_definition(test_id: str) -> Optional[Dict[str, Any]]:
    """
    Load test definition from JSON file.
    
    Args:
        test_id: The test identifier
        
    Returns:
        Test definition dict or None if not found
    """
    # Common test definition paths relative to project root
    test_paths = [
        project_root / f"tests/definitions/bias-resilient/{test_id}.json",
        project_root / f"tests/definitions/cognitive/{test_id}.json",
        project_root / f"tests/definitions/fatigue/{test_id}.json",
        project_root / f"tests/definitions/custom/{test_id}.json",
    ]
    
    for path in test_paths:
        if path.exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading test definition from {path}: {e}")
                
    return None


def get_correct_answer(question: Dict[str, Any]) -> Optional[Union[str, int, float]]:
    """
    Extract the correct answer from a question definition.
    
    Args:
        question: Question dict from test definition
        
    Returns:
        Correct answer value or None if not found
    """
    # For questions with explicit correct answer
    if 'scoring' in question and 'correct_answer' in question['scoring']:
        return question['scoring']['correct_answer']
    
    # For multiple choice questions
    if question.get('type') == 'multiple_choice' and 'options' in question:
        for option in question['options']:
            if option.get('is_correct', False):
                return option.get('value')
    
    # For true/false questions
    if question.get('type') == 'true_false' and 'correct_answer' in question:
        return question['correct_answer']
    
    return None


def calculate_text_score(user_answer: str, correct_answer: str, 
                        points: int = 1) -> int:
    """
    Calculate score for text input questions.
    
    Args:
        user_answer: User's answer
        correct_answer: Expected correct answer
        points: Points awarded for correct answer
        
    Returns:
        Score (0 or points value)
    """
    # Clean and normalize answers for comparison
    user_clean = str(user_answer).strip().lower()
    correct_clean = str(correct_answer).strip().lower()
    
    # Handle numeric answers
    try:
        # Try to convert to numbers for numeric comparison
        user_num = float(user_clean)
        correct_num = float(correct_clean)
        
        # Allow for small floating point differences
        if abs(user_num - correct_num) < 0.001:
            return points
    except ValueError:
        # Not numeric, do string comparison
        pass
    
    # Exact match comparison
    if user_clean == correct_clean:
        return points
        
    return 0


def calculate_multiple_choice_score(user_answer: Any, question: Dict[str, Any],
                                  points: int = 1) -> int:
    """
    Calculate score for multiple choice questions.
    
    Args:
        user_answer: User's selected value
        question: Question definition with options
        points: Points awarded for correct answer
        
    Returns:
        Score (0 or points value)
    """
    if 'options' not in question:
        return 0
        
    # Find the correct option
    for option in question['options']:
        if option.get('is_correct', False):
            correct_value = option.get('value')
            # Compare values (handle type conversion)
            if str(user_answer) == str(correct_value):
                return points
                
    return 0


def calculate_likert_score(user_answer: Any, question: Dict[str, Any]) -> float:
    """
    Calculate score for likert scale questions.
    
    Args:
        user_answer: User's selected value (typically 1-5 or 1-7)
        question: Question definition
        
    Returns:
        Raw score value (not normalized)
    """
    try:
        value = float(user_answer)
    except (ValueError, TypeError):
        return 0
    
    # Check if this is a reverse-scored question
    if 'reverse-scored' in question.get('tags', []):
        # Assume 5-point scale by default, adjust if needed
        max_scale = question.get('validation', {}).get('max_value', 5)
        min_scale = question.get('validation', {}).get('min_value', 1)
        # Reverse the score
        value = (max_scale + min_scale) - value
    
    return value


def calculate_section_scores(test_def: Dict[str, Any], answers: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate scores grouped by section/category tags.
    
    Args:
        test_def: Test definition with questions
        answers: User answers keyed by question ID
        
    Returns:
        Dict of section scores with structure:
        {
            'section_name': {
                'score': achieved_score,
                'max_score': maximum_possible_score,
                'percentage': score_percentage,
                'questions': [list of question IDs in section]
            }
        }
    """
    section_scores = {}
    questions = test_def.get('questions', [])
    
    # Define section mappings based on tags
    section_mappings = {
        'cognitive-reflection': 'crt',
        'numeracy': 'numeracy',
        'calibration': 'calibration',
        'actively-open-minded': 'aot',
        'need-for-closure': 'nfc',
        'intent-attribution': 'intent',
        'anchoring': 'anchoring',
        'confidence': 'confidence'
    }
    
    for question in questions:
        question_id = str(question.get('id'))
        points = question.get('points', 0)
        
        # Skip non-scorable questions
        if points == 0:
            continue
            
        # Get user answer
        user_answer = answers.get(question_id, {}).get('answer') if isinstance(answers.get(question_id), dict) else answers.get(question_id)
        if user_answer is None:
            continue
            
        # Determine section from tags
        question_tags = question.get('tags', [])
        section = None
        
        for tag in question_tags:
            if tag in section_mappings:
                section = section_mappings[tag]
                break
        
        # Default section if no matching tag
        if not section:
            section = 'general'
            
        # Initialize section if needed
        if section not in section_scores:
            section_scores[section] = {
                'score': 0,
                'max_score': 0,
                'questions': []
            }
        
        # Calculate score based on question type
        score = 0
        question_type = question.get('type')
        
        if question_type == 'text_input':
            correct_answer = get_correct_answer(question)
            if correct_answer is not None:
                score = calculate_text_score(user_answer, correct_answer, points)
        elif question_type == 'multiple_choice':
            score = calculate_multiple_choice_score(user_answer, question, points)
        elif question_type in ['slider', 'rating']:
            # For likert-type questions, accumulate raw scores
            score = calculate_likert_score(user_answer, question)
            points = question.get('validation', {}).get('max_value', 5)  # Max possible value
        
        # Update section scores
        section_scores[section]['score'] += score
        section_scores[section]['max_score'] += points
        section_scores[section]['questions'].append(question_id)
    
    # Calculate percentages
    for section, data in section_scores.items():
        if data['max_score'] > 0:
            data['percentage'] = round((data['score'] / data['max_score']) * 100, 1)
        else:
            data['percentage'] = 0
            
    return section_scores


def calculate_calibration_score(confidence_answers: Dict[str, float], 
                              performance_scores: Dict[str, bool]) -> Dict[str, Any]:
    """
    Calculate calibration score based on confidence vs actual performance.
    
    Args:
        confidence_answers: Dict of question_id -> confidence (0-100)
        performance_scores: Dict of question_id -> correct/incorrect (True/False)
        
    Returns:
        Calibration metrics including overconfidence/underconfidence
    """
    if not confidence_answers or not performance_scores:
        return {
            'calibration_score': 0,
            'average_confidence': 0,
            'accuracy': 0,
            'overconfidence': 0,
            'num_questions': 0
        }
    
    # Calculate average confidence and accuracy
    confidences = []
    correct_count = 0
    calibration_error = 0
    
    for q_id, confidence in confidence_answers.items():
        # Get corresponding performance question ID (e.g., 2 -> 1, 4 -> 3)
        perf_q_id = str(int(q_id) - 1)
        
        if perf_q_id in performance_scores:
            confidence_pct = float(confidence) / 100.0
            actual = 1.0 if performance_scores[perf_q_id] else 0.0
            
            confidences.append(confidence_pct)
            correct_count += actual
            
            # Calculate calibration error (Brier score component)
            calibration_error += (confidence_pct - actual) ** 2
    
    if not confidences:
        return {
            'calibration_score': 0,
            'average_confidence': 0,
            'accuracy': 0,
            'overconfidence': 0,
            'num_questions': 0
        }
    
    avg_confidence = sum(confidences) / len(confidences) * 100
    accuracy = (correct_count / len(confidences)) * 100
    overconfidence = avg_confidence - accuracy
    
    # Calibration score: 100 - (average squared error * 100)
    # Perfect calibration = 100, worst = 0
    calibration_score = max(0, 100 - (calibration_error / len(confidences) * 100))
    
    return {
        'calibration_score': round(calibration_score, 1),
        'average_confidence': round(avg_confidence, 1),
        'accuracy': round(accuracy, 1),
        'overconfidence': round(overconfidence, 1),
        'num_questions': len(confidences),
        'interpretation': 'Well calibrated' if abs(overconfidence) < 10 else 
                         'Overconfident' if overconfidence > 10 else 'Underconfident'
    }


def calculate_assessment_scores(test_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to calculate all scores for an assessment.
    
    Args:
        test_id: Test identifier to load definition
        answers: User answers (can be dict of dicts or simple dict)
        
    Returns:
        Complete scoring data with overall and section scores
    """
    # Load test definition
    test_def = load_test_definition(test_id)
    if not test_def:
        print(f"Warning: Could not load test definition for {test_id}")
        return {
            'overall': {'score': 0, 'max_score': 0, 'percentage': 0},
            'sections': {},
            'error': 'Test definition not found'
        }
    
    # Calculate section scores
    section_scores = calculate_section_scores(test_def, answers)
    
    # Calculate overall scores
    total_score = sum(section['score'] for section in section_scores.values())
    total_max = sum(section['max_score'] for section in section_scores.values())
    overall_percentage = round((total_score / total_max * 100) if total_max > 0 else 0, 1)
    
    # Prepare final scoring structure
    scoring_data = {
        'overall': {
            'score': total_score,
            'max_score': total_max,
            'percentage': overall_percentage
        },
        'sections': section_scores
    }
    
    # Add special scoring for CRT if present
    if 'crt' in section_scores:
        crt_data = section_scores['crt']
        # For CRT, score is number of correct answers (0-3)
        scoring_data['crtScore'] = {
            'score': int(crt_data['score']),
            'total': len(crt_data['questions']),
            'percentage': crt_data['percentage'],
            'correctAnswers': []  # Could be enhanced to track which were correct
        }
    
    # Calculate calibration score if confidence questions present
    questions = test_def.get('questions', [])
    confidence_answers = {}
    performance_scores = {}
    
    for question in questions:
        question_id = str(question.get('id'))
        tags = question.get('tags', [])
        
        # Collect confidence ratings
        if 'confidence' in tags and question_id in answers:
            user_answer = answers.get(question_id, {}).get('answer') if isinstance(answers.get(question_id), dict) else answers.get(question_id)
            if user_answer is not None:
                try:
                    confidence_answers[question_id] = float(user_answer)
                except (ValueError, TypeError):
                    pass
        
        # Collect performance results for scored questions
        elif question.get('points', 0) > 0 and question_id in section_scores.get('crt', {}).get('questions', []):
            # Check if the answer was correct
            user_answer = answers.get(question_id, {}).get('answer') if isinstance(answers.get(question_id), dict) else answers.get(question_id)
            correct_answer = get_correct_answer(question)
            if user_answer is not None and correct_answer is not None:
                score = calculate_text_score(user_answer, correct_answer, 1)
                performance_scores[question_id] = score > 0
    
    # Add calibration score if we have matching confidence/performance pairs
    if confidence_answers and performance_scores:
        scoring_data['calibration'] = calculate_calibration_score(confidence_answers, performance_scores)
    
    return scoring_data