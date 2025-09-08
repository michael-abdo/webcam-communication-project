#!/bin/bash

# Authentication Fix Script for greg@altoinc.com
# Run this with AWS administrative credentials configured

echo "=== Greg Authentication Fix Script ==="
echo "Account: 221082191449 (from login URL)"
echo "Username: greg-altoinc"
echo "Required access: Both webcam-streaming and psychometric-webcam-videos buckets"
echo ""

# Step 1: Delete existing invalid user (if exists)
echo "Step 1: Cleaning up existing IAM user..."
aws iam delete-user-policy --user-name greg-altoinc --policy-name greg-webcam-bucket-access 2>/dev/null
aws iam list-access-keys --user-name greg-altoinc --query 'AccessKeyMetadata[*].AccessKeyId' --output text | \
    xargs -r -n1 aws iam delete-access-key --user-name greg-altoinc --access-key-id 2>/dev/null
aws iam delete-user --user-name greg-altoinc 2>/dev/null

# Step 2: Create new user
echo "Step 2: Creating new IAM user..."
aws iam create-user --user-name greg-altoinc

# Step 3: Create access keys
echo "Step 3: Generating new access keys..."
aws iam create-access-key --user-name greg-altoinc > greg-credentials-new.json

# Step 4: Apply the fixed policy (grants access to both buckets)
echo "Step 4: Applying IAM policy for both S3 buckets..."
aws iam put-user-policy \
  --user-name greg-altoinc \
  --policy-name greg-webcam-bucket-access \
  --policy-document file://greg-s3-policy.json

# Step 5: Create the required bucket if it doesn't exist
echo "Step 5: Ensuring psychometric-webcam-videos bucket exists..."
aws s3 mb s3://psychometric-webcam-videos --region us-west-2 2>/dev/null || echo "Bucket already exists"

# Step 6: Set CORS on the bucket
echo "Step 6: Configuring CORS on psychometric-webcam-videos..."
cat > temp-cors.json << 'EOF'
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

aws s3api put-bucket-cors --bucket psychometric-webcam-videos --cors-configuration file://temp-cors.json
rm temp-cors.json

echo ""
echo "✅ Authentication fix complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update greg-credentials.json with contents from greg-credentials-new.json"
echo "2. Test access: aws s3 ls s3://psychometric-webcam-videos/"
echo "3. Run migration if needed: ./migrate-s3-bucket.sh"
echo ""
echo "🔑 Greg can now use these credentials:"
echo "- Console: https://221082191449.signin.aws.amazon.com/console"
echo "- Username: greg-altoinc"  
echo "- Temp Password: TempPassword123!"
echo ""
echo "⚠️  IMPORTANT: Secure the new credentials and delete greg-credentials-new.json after sharing!"