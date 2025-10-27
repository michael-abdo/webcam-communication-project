#!/bin/bash

# Script to migrate S3 bucket contents from old to new bucket
# Note: S3 buckets cannot be renamed, so we need to create a new one and copy contents

OLD_BUCKET="webcam-streaming"
NEW_BUCKET="psychometric-webcam-videos"
REGION="us-west-2"

echo "S3 Bucket Migration Script"
echo "=========================="
echo "From: $OLD_BUCKET"
echo "To: $NEW_BUCKET"
echo "Region: $REGION"
echo ""

# Check if old bucket exists
echo "Checking if source bucket exists..."
if aws s3 ls "s3://$OLD_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Source bucket $OLD_BUCKET does not exist. Nothing to migrate."
    exit 0
fi

# Create new bucket
echo "Creating new bucket $NEW_BUCKET..."
aws s3 mb "s3://$NEW_BUCKET" --region "$REGION" 2>/dev/null || echo "Bucket already exists or creation failed"

# Set CORS configuration
echo "Setting CORS configuration on new bucket..."
cat > cors-config.json << 'EOF'
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["POST", "PUT", "GET", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF

aws s3api put-bucket-cors \
  --bucket "$NEW_BUCKET" \
  --cors-configuration file://cors-config.json

# Clean up temporary file
rm cors-config.json

# Check if old bucket has any objects
echo "Checking for objects in source bucket..."
OBJECT_COUNT=$(aws s3 ls "s3://$OLD_BUCKET" --recursive | wc -l)

if [ "$OBJECT_COUNT" -eq 0 ]; then
    echo "No objects found in source bucket. Migration complete."
else
    echo "Found $OBJECT_COUNT objects to migrate."
    
    # Copy all objects
    echo "Starting copy operation..."
    aws s3 sync "s3://$OLD_BUCKET" "s3://$NEW_BUCKET" --acl bucket-owner-full-control
    
    echo "Migration complete!"
    echo ""
    echo "Summary:"
    echo "- Objects copied: $OBJECT_COUNT"
    echo "- New bucket: s3://$NEW_BUCKET"
    echo ""
    echo "IMPORTANT: Do NOT delete the old bucket until you've verified everything works!"
    echo "To delete the old bucket later (after verification):"
    echo "  aws s3 rb s3://$OLD_BUCKET --force"
fi

echo ""
echo "Next steps:"
echo "1. Test your application with the new bucket"
echo "2. Verify all videos are accessible"
echo "3. Only delete the old bucket after confirming everything works"