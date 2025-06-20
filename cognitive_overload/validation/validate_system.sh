#!/bin/bash
# Validation System Setup Script

echo "=== COGNITIVE OVERLOAD VALIDATION SYSTEM ==="
echo "Setting up validation for real webcam videos..."

# Change to validation directory
cd "$(dirname "$0")"

# Step 1: Prepare sample dataset
echo -e "\n📁 Step 1: Preparing sample dataset..."
python3 download_sample_dataset.py

# Check if user wants to record videos
echo -e "\n📹 Would you like to record sample videos now? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    python3 ./webcam_datasets/record_sample_videos.py
fi

# Step 2: Run validation
echo -e "\n🔍 Step 2: Running validation on dataset..."
echo "Using dataset: ./webcam_datasets/sample_dataset"

# Run validation with max 10 videos for initial test
python3 dataset_validator.py ./webcam_datasets/sample_dataset --max-videos 10

echo -e "\n✅ Validation complete!"
echo "Check ./validation_results/ for detailed results"