#!/usr/bin/env python3
"""
Individual Speaker Analysis for Behavioral Signals Data
Generates detailed reports for each speaker in a conversation recording.
"""

import json
import sys
import os
from collections import defaultdict, Counter
from pathlib import Path
import argparse


def load_data(json_file):
    """Load and parse JSON data from file."""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{json_file}': {e}")
        sys.exit(1)


def group_by_speaker(data):
    """Group all utterances by speaker ID from diarization results."""
    speaker_data = defaultdict(lambda: defaultdict(list))
    
    # Get speaker mapping from diarization results
    utterance_speakers = {}
    for record in data:
        if record.get('task') == 'diarization':
            utterance_id = record.get('id')
            speaker_id = record.get('finalLabel')
            utterance_speakers[utterance_id] = speaker_id
    
    # Group all task results by speaker
    for record in data:
        utterance_id = record.get('id')
        task = record.get('task')
        
        if utterance_id in utterance_speakers:
            speaker_id = utterance_speakers[utterance_id]
            speaker_data[speaker_id][task].append(record)
    
    return dict(speaker_data)


def calculate_speaker_stats(speaker_tasks):
    """Calculate comprehensive statistics for a single speaker."""
    stats = {}
    
    # Basic utterance information
    if 'asr' in speaker_tasks:
        stats['total_utterances'] = len(speaker_tasks['asr'])
        stats['total_speaking_time'] = sum(
            float(r.get('endTime', 0)) - float(r.get('startTime', 0))
            for r in speaker_tasks['asr']
        )
        stats['avg_utterance_length'] = (
            stats['total_speaking_time'] / stats['total_utterances']
            if stats['total_utterances'] > 0 else 0
        )
    else:
        stats['total_utterances'] = 0
        stats['total_speaking_time'] = 0
        stats['avg_utterance_length'] = 0
    
    # Demographics
    stats['demographics'] = {}
    if 'gender' in speaker_tasks and speaker_tasks['gender']:
        gender_record = speaker_tasks['gender'][0]
        stats['demographics']['gender'] = gender_record.get('finalLabel')
        stats['demographics']['gender_confidence'] = 0.0
        for pred in gender_record.get('prediction', []):
            if pred.get('label') == stats['demographics']['gender']:
                stats['demographics']['gender_confidence'] = float(pred.get('posterior', 0))
    
    if 'age' in speaker_tasks and speaker_tasks['age']:
        age_record = speaker_tasks['age'][0]
        stats['demographics']['age_group'] = age_record.get('finalLabel')
        stats['demographics']['age_confidence'] = 0.0
        for pred in age_record.get('prediction', []):
            if pred.get('label') == stats['demographics']['age_group']:
                stats['demographics']['age_confidence'] = float(pred.get('posterior', 0))
    
    # Language
    if 'language' in speaker_tasks and speaker_tasks['language']:
        lang_record = speaker_tasks['language'][0]
        stats['language'] = lang_record.get('finalLabel')
        stats['language_confidence'] = 0.0
        for pred in lang_record.get('prediction', []):
            if pred.get('label') == stats['language']:
                stats['language_confidence'] = float(pred.get('posterior', 0))
    
    # Emotional analysis
    stats['emotions'] = {}
    if 'emotion' in speaker_tasks:
        emotion_counts = Counter(r.get('finalLabel') for r in speaker_tasks['emotion'])
        total_emotions = sum(emotion_counts.values())
        stats['emotions']['distribution'] = {
            emotion: count / total_emotions * 100
            for emotion, count in emotion_counts.items()
        }
        stats['emotions']['dominant'] = emotion_counts.most_common(1)[0] if emotion_counts else ('unknown', 0)
    
    # Positivity analysis
    if 'positivity' in speaker_tasks:
        positivity_counts = Counter(r.get('finalLabel') for r in speaker_tasks['positivity'])
        total_pos = sum(positivity_counts.values())
        stats['positivity'] = {
            sentiment: count / total_pos * 100
            for sentiment, count in positivity_counts.items()
        }
    
    # Speaking patterns
    stats['speaking_patterns'] = {}
    
    # Speaking rate
    if 'speaking_rate' in speaker_tasks:
        rate_counts = Counter(r.get('finalLabel') for r in speaker_tasks['speaking_rate'])
        total_rate = sum(rate_counts.values())
        stats['speaking_patterns']['rate'] = {
            rate: count / total_rate * 100
            for rate, count in rate_counts.items()
        }
    
    # Hesitation
    if 'hesitation' in speaker_tasks:
        hesitation_counts = Counter(r.get('finalLabel') for r in speaker_tasks['hesitation'])
        total_hesitation = sum(hesitation_counts.values())
        stats['speaking_patterns']['hesitation'] = {
            hesitation: count / total_hesitation * 100
            for hesitation, count in hesitation_counts.items()
        }
    
    # Engagement
    if 'engagement' in speaker_tasks:
        engagement_counts = Counter(r.get('finalLabel') for r in speaker_tasks['engagement'])
        total_engagement = sum(engagement_counts.values())
        stats['speaking_patterns']['engagement'] = {
            level: count / total_engagement * 100
            for level, count in engagement_counts.items()
        }
    
    # Voice strength
    if 'strength' in speaker_tasks:
        strength_counts = Counter(r.get('finalLabel') for r in speaker_tasks['strength'])
        total_strength = sum(strength_counts.values())
        stats['speaking_patterns']['strength'] = {
            strength: count / total_strength * 100
            for strength, count in strength_counts.items()
        }
    
    # Deepfake analysis
    if 'deepfake' in speaker_tasks:
        deepfake_counts = Counter(r.get('finalLabel') for r in speaker_tasks['deepfake'])
        total_deepfake = sum(deepfake_counts.values())
        stats['deepfake'] = {
            label: count / total_deepfake * 100
            for label, count in deepfake_counts.items()
        }
    
    return stats


def generate_speaker_report(speaker_id, stats, speaker_tasks):
    """Generate a comprehensive text report for a single speaker."""
    report = []
    
    # Header
    report.append("=" * 60)
    report.append(f"BEHAVIORAL SIGNALS ANALYSIS - {speaker_id}")
    report.append("=" * 60)
    report.append("")
    
    # Basic Information
    report.append("SPEAKER OVERVIEW")
    report.append("-" * 20)
    report.append(f"Speaker ID: {speaker_id}")
    report.append(f"Total Utterances: {stats['total_utterances']}")
    report.append(f"Total Speaking Time: {stats['total_speaking_time']:.2f} seconds")
    report.append(f"Average Utterance Length: {stats['avg_utterance_length']:.2f} seconds")
    report.append("")
    
    # Demographics
    if stats.get('demographics'):
        report.append("DEMOGRAPHICS")
        report.append("-" * 15)
        demo = stats['demographics']
        if 'gender' in demo:
            report.append(f"Gender: {demo['gender']} (confidence: {demo['gender_confidence']:.1%})")
        if 'age_group' in demo:
            report.append(f"Age Group: {demo['age_group']} (confidence: {demo['age_confidence']:.1%})")
        report.append("")
    
    # Language
    if stats.get('language'):
        report.append("LANGUAGE")
        report.append("-" * 10)
        report.append(f"Language: {stats['language'].upper()} (confidence: {stats['language_confidence']:.1%})")
        report.append("")
    
    # Emotional Profile
    if stats.get('emotions'):
        report.append("EMOTIONAL PROFILE")
        report.append("-" * 18)
        emotions = stats['emotions']
        if 'dominant' in emotions:
            dominant_emotion, dominant_count = emotions['dominant']
            report.append(f"Dominant Emotion: {dominant_emotion.upper()} ({dominant_count} utterances)")
        
        if 'distribution' in emotions:
            report.append("Emotion Distribution:")
            for emotion, percentage in sorted(emotions['distribution'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {emotion.capitalize()}: {percentage:.1f}%")
        report.append("")
    
    # Positivity Analysis
    if stats.get('positivity'):
        report.append("POSITIVITY ANALYSIS")
        report.append("-" * 19)
        for sentiment, percentage in sorted(stats['positivity'].items(), key=lambda x: x[1], reverse=True):
            report.append(f"{sentiment.capitalize()}: {percentage:.1f}%")
        report.append("")
    
    # Speaking Patterns
    if stats.get('speaking_patterns'):
        report.append("SPEAKING PATTERNS")
        report.append("-" * 17)
        patterns = stats['speaking_patterns']
        
        if 'rate' in patterns:
            report.append("Speaking Rate:")
            for rate, percentage in sorted(patterns['rate'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {rate.capitalize()}: {percentage:.1f}%")
        
        if 'hesitation' in patterns:
            report.append("Hesitation Patterns:")
            for hesitation, percentage in sorted(patterns['hesitation'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {hesitation.capitalize()}: {percentage:.1f}%")
        
        if 'engagement' in patterns:
            report.append("Engagement Level:")
            for level, percentage in sorted(patterns['engagement'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {level.capitalize()}: {percentage:.1f}%")
        
        if 'strength' in patterns:
            report.append("Voice Strength:")
            for strength, percentage in sorted(patterns['strength'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {strength.capitalize()}: {percentage:.1f}%")
        report.append("")
    
    # Deepfake Analysis
    if stats.get('deepfake'):
        report.append("AUTHENTICITY ANALYSIS")
        report.append("-" * 21)
        for label, percentage in sorted(stats['deepfake'].items(), key=lambda x: x[1], reverse=True):
            status = "Authentic" if label == "bonafide" else "Potentially Manipulated"
            report.append(f"{status}: {percentage:.1f}%")
        report.append("")
    
    # Transcriptions
    if 'asr' in speaker_tasks:
        report.append("SPEECH TRANSCRIPTIONS")
        report.append("-" * 21)
        for utterance in speaker_tasks['asr']:
            start_time = float(utterance.get('startTime', 0))
            end_time = float(utterance.get('endTime', 0))
            text = utterance.get('finalLabel', '').strip()
            if text:
                report.append(f"[{start_time:.1f}s - {end_time:.1f}s]: {text}")
        report.append("")
    
    # Summary
    report.append("SUMMARY")
    report.append("-" * 7)
    summary_points = []
    
    if stats.get('demographics'):
        demo = stats['demographics']
        if 'gender' in demo and 'age_group' in demo:
            summary_points.append(f"Demographics: {demo['age_group']} {demo['gender']}")
    
    if stats.get('emotions') and 'dominant' in stats['emotions']:
        dominant_emotion, _ = stats['emotions']['dominant']
        summary_points.append(f"Primary emotional tone: {dominant_emotion}")
    
    if stats.get('speaking_patterns'):
        patterns = stats['speaking_patterns']
        if 'rate' in patterns:
            dominant_rate = max(patterns['rate'].items(), key=lambda x: x[1])[0]
            summary_points.append(f"Speaking style: {dominant_rate} pace")
        
        if 'engagement' in patterns:
            dominant_engagement = max(patterns['engagement'].items(), key=lambda x: x[1])[0]
            summary_points.append(f"Engagement level: {dominant_engagement}")
    
    for point in summary_points:
        report.append(f"- {point}")
    
    report.append("")
    report.append("=" * 60)
    
    return '\n'.join(report)


def main():
    """Main function to process speaker analysis."""
    parser = argparse.ArgumentParser(description='Generate individual speaker analysis reports')
    parser.add_argument('json_file', help='Path to JSON file containing behavioral signals data')
    parser.add_argument('--output-dir', default='../../data/reports', 
                       help='Output directory for reports (default: ../../data/reports)')
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading data from {args.json_file}...")
    data = load_data(args.json_file)
    
    # Group by speakers
    print("Grouping data by speakers...")
    speaker_data = group_by_speaker(data)
    
    if not speaker_data:
        print("No speaker data found. Make sure the JSON file contains diarization results.")
        return
    
    print(f"Found {len(speaker_data)} speakers: {', '.join(sorted(speaker_data.keys()))}")
    
    # Process each speaker
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_filename = Path(args.json_file).stem
    
    for speaker_id in sorted(speaker_data.keys()):
        print(f"Processing {speaker_id}...")
        
        # Calculate statistics
        stats = calculate_speaker_stats(speaker_data[speaker_id])
        
        # Generate report
        report_content = generate_speaker_report(speaker_id, stats, speaker_data[speaker_id])
        
        # Save report
        output_file = output_dir / f"{base_filename}_{speaker_id}_analysis.txt"
        with open(output_file, 'w') as f:
            f.write(report_content)
        
        print(f"  Report saved: {output_file}")
        print(f"  Utterances: {stats['total_utterances']}, Speaking time: {stats['total_speaking_time']:.1f}s")
    
    print(f"\nCompleted analysis for {len(speaker_data)} speakers.")
    print(f"Reports saved to: {output_dir}")


if __name__ == "__main__":
    main()