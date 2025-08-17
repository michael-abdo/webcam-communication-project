#!/usr/bin/env python3
"""
Create a meaningful report from Behavioral Signals API results
"""

import json
import sys
import os
from collections import defaultdict


def create_behavior_report(json_file: str, output_file: str = None):
    """
    Create a behavioral analysis report from API results
    
    Args:
        json_file: Path to JSON results file
        output_file: Path to output report file (optional)
    """
    with open(json_file, 'r') as f:
        data = json.load(f)

    results = data.get('results', [])

    # Group by task type
    by_task = defaultdict(list)
    for r in results:
        by_task[r.get('task')].append(r)

    report = []
    report.append("BEHAVIORAL SIGNALS ANALYSIS REPORT")
    report.append("=" * 70)
    report.append("Audio Duration: ~54 seconds\n")

    # Transcription
    if 'asr' in by_task:
        report.append("SPEECH TRANSCRIPTION:")
        for segment in by_task['asr']:
            text = segment.get('finalLabel', '')
            if text.strip():
                start = float(segment.get('startTime', 0))
                end = float(segment.get('endTime', 0))
                report.append(f"  [{start:.1f}s - {end:.1f}s]: {text.strip()}")
        report.append("")

    # Speaker Info
    if 'gender' in by_task and 'age' in by_task:
        report.append("SPEAKER PROFILE:")
        # Get dominant gender
        gender_segment = by_task['gender'][0]
        gender = gender_segment.get('finalLabel', 'Unknown')
        gender_conf = 0
        for pred in gender_segment.get('prediction', []):
            if pred.get('label') == gender:
                gender_conf = float(pred.get('posterior', 0))
        
        # Get dominant age
        age_segment = by_task['age'][0]
        age = age_segment.get('finalLabel', 'Unknown')
        age_conf = 0
        for pred in age_segment.get('prediction', []):
            if pred.get('label') == age:
                age_conf = float(pred.get('posterior', 0))
        
        report.append(f"  - Gender: {gender} (confidence: {gender_conf:.1%})")
        report.append(f"  - Age Group: {age} years (confidence: {age_conf:.1%})")
        
        # Language
        if 'language' in by_task:
            lang_segment = by_task['language'][0]
            lang = lang_segment.get('finalLabel', 'Unknown')
            lang_conf = 0
            for pred in lang_segment.get('prediction', []):
                if pred.get('label') == lang:
                    lang_conf = float(pred.get('posterior', 0))
            report.append(f"  - Language: {lang.upper()} (confidence: {lang_conf:.1%})")
        report.append("")

    # Emotional Analysis
    if 'emotion' in by_task:
        report.append("EMOTIONAL ANALYSIS:")
        report.append("  Timeline of Emotions:")
        for segment in by_task['emotion']:
            start = float(segment.get('startTime', 0))
            end = float(segment.get('endTime', 0))
            emotion = segment.get('finalLabel', 'Unknown')
            
            # Get confidence
            conf = 0
            for pred in segment.get('prediction', []):
                if pred.get('label') == emotion:
                    conf = float(pred.get('posterior', 0))
            
            report.append(f"    [{start:.1f}s - {end:.1f}s]: {emotion.upper()} (confidence: {conf:.1%})")
        report.append("")

    # Behavioral Characteristics
    report.append("BEHAVIORAL CHARACTERISTICS:")

    # Positivity
    if 'positivity' in by_task:
        positivity_counts = defaultdict(int)
        for segment in by_task['positivity']:
            positivity_counts[segment.get('finalLabel')] += 1
        
        report.append("  Positivity:")
        for sentiment, count in sorted(positivity_counts.items()):
            report.append(f"    - {sentiment}: {count} segments")

    # Strength
    if 'strength' in by_task:
        strength_counts = defaultdict(int)
        for segment in by_task['strength']:
            strength_counts[segment.get('finalLabel')] += 1
        
        report.append("  Voice Strength:")
        for strength, count in sorted(strength_counts.items()):
            report.append(f"    - {strength}: {count} segments")

    # Speaking Rate
    if 'speaking_rate' in by_task:
        rate_counts = defaultdict(int)
        for segment in by_task['speaking_rate']:
            rate_counts[segment.get('finalLabel')] += 1
        
        report.append("  Speaking Rate:")
        for rate, count in sorted(rate_counts.items()):
            report.append(f"    - {rate}: {count} segments")

    # Hesitation
    if 'hesitation' in by_task:
        hesitation_counts = defaultdict(int)
        for segment in by_task['hesitation']:
            hesitation_counts[segment.get('finalLabel')] += 1
        
        report.append("  Hesitation:")
        for hesitation, count in sorted(hesitation_counts.items()):
            report.append(f"    - {hesitation}: {count} segments")

    # Engagement
    if 'engagement' in by_task:
        engagement_counts = defaultdict(int)
        for segment in by_task['engagement']:
            engagement_counts[segment.get('finalLabel')] += 1
        
        report.append("  Engagement Level:")
        for engagement, count in sorted(engagement_counts.items()):
            report.append(f"    - {engagement}: {count} segments")

    report.append("\n" + "=" * 70)
    report.append("SUMMARY: The analysis reveals detailed insights about the speaker's")
    report.append("emotional state, speaking patterns, and behavioral characteristics")
    report.append("throughout the recording.")

    # Create report text
    report_text = '\n'.join(report)

    # Save report if output file specified
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(report_text)
        print(f"Report saved to: {output_file}")
    
    return report_text


def main():
    """Main function for command-line usage"""
    # Get filename from command line argument or use default
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = '../../data/results/process_45133_results.json'

    # Generate output filename based on input
    base_name = os.path.basename(json_file).replace('.json', '')
    output_file = f'../../data/reports/{base_name}_report.txt'

    report_text = create_behavior_report(json_file, output_file)
    print(report_text)


if __name__ == "__main__":
    main()