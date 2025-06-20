# Webcam Dataset Validation Guide

## Overview

The validation system has been set up to test the cognitive overload detection system with real webcam videos. This ensures the system works with actual human faces, not just synthetic test data.

## Current Status

✅ **Synthetic Video Validation: PASSED**
- Detection Rate: 100%
- Processing Speed: 44.3 fps
- Cognitive Metrics: Successfully calculated
- Stress Score: Stable at ~0.63

## System Components

### 1. Dataset Validator (`dataset_validator.py`)
Main validation engine that:
- Processes video datasets
- Calculates detection rates
- Analyzes cognitive metrics
- Generates comprehensive reports

### 2. Dataset Preparer (`download_sample_dataset.py`)
Helps prepare datasets by:
- Setting up directory structure
- Providing recording scripts
- Organizing test videos

### 3. Recording Script (`record_sample_videos.py`)
Assists in creating test videos with:
- Different cognitive load scenarios
- Guided recording sessions
- Automatic file organization

## Validation Results Analysis

### Synthetic Face Results
```
- Brow Furrow Distance: 95.4 ± 2.6 pixels
- Eye Openness: 0.151 ± 0.008 (15.1% of eye width)
- Mouth Compression: 0.003 ± 0.006 (minimal)
- Cognitive Stress Score: 0.631 ± 0.010 (stable)
```

These metrics show:
- Consistent landmark detection
- Stable measurements across frames
- Reasonable value ranges for a neutral face

## Next Steps: Real Face Validation

### Option 1: Quick Recording (Recommended)
```bash
# Run the recording script
cd /home/Mike/projects/webcam/cognitive_overload/validation
python3 ./webcam_datasets/record_sample_videos.py

# This will guide you through recording:
# - Baseline relaxed state
# - Reading simple text
# - Reading complex text
# - Mental math (easy/hard)
# - Problem solving
```

### Option 2: Use Existing Videos
Place any webcam videos (MP4, AVI, MOV) in:
```
./webcam_datasets/sample_dataset/
```

Requirements:
- Clear face visibility
- Good lighting
- 480p resolution or higher
- 15+ fps

### Option 3: Download Public Datasets
Consider:
- YouTube Faces Database
- CelebA Video Dataset
- LFW (Labeled Faces in the Wild)

## Running Validation

### Basic Validation
```bash
# Validate all videos in dataset
python3 dataset_validator.py ./webcam_datasets/sample_dataset

# Limit to first 10 videos
python3 dataset_validator.py ./webcam_datasets/sample_dataset --max-videos 10
```

### Quick Test
```bash
# Use the quick validation script
python3 quick_validate.py
```

### Full System Test
```bash
# Run complete validation workflow
./validate_system.sh
```

## Success Criteria

For the system to be considered validated:

1. **Detection Rate**: >70% average across all videos
2. **Processing Speed**: >30 fps (real-time capable)
3. **Cognitive Metrics**: 
   - Reasonable ranges for all metrics
   - Temporal stability (no wild fluctuations)
   - Differentiation between cognitive states

## Interpreting Results

### Good Results
- Detection rate: 70-100%
- Consistent metrics across frames
- Clear differences between cognitive states
- Processing speed >30 fps

### Issues to Watch For
- Detection rate <50%: Poor lighting or video quality
- Unstable metrics: Landmark tracking issues
- No state differentiation: Need more varied test scenarios

## Cognitive Metric Ranges (Expected)

Based on synthetic face baseline:
- **Brow Furrow**: 80-120 pixels (closer = more stress)
- **Eye Openness**: 0.10-0.25 (lower = more strain)
- **Mouth Compression**: 0.0-0.2 (higher = more tension)
- **Stress Score**: 0.3-0.8 (higher = more overload)

## Troubleshooting

### Low Detection Rate
- Check video lighting
- Ensure face is clearly visible
- Try lowering detection confidence to 0.5

### Unstable Metrics
- Increase tracking confidence
- Use better quality videos
- Ensure minimal camera shake

### Performance Issues
- Reduce frame processing interval
- Use lower resolution videos
- Enable static image mode for accuracy over speed

## Summary

The validation system is ready and has been tested with synthetic faces. The next critical step is validation with real human faces to ensure the cognitive overload detection works in real-world conditions.

**Current Status**: Awaiting real face video validation
**Recommendation**: Record test videos using the provided script for immediate validation