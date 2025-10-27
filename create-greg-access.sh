#!/bin/bash

# Script to create IAM user for greg@altoinc.com with S3 access

echo "Creating IAM user for greg@altoinc.com..."
aws iam create-user --user-name greg-altoinc

echo "Generating access keys..."
aws iam create-access-key --user-name greg-altoinc > greg-credentials.json

echo "Creating S3 policy for webcam bucket..."
cat > greg-s3-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::webcam-streaming",
        "arn:aws:s3:::webcam-streaming/*"
      ]
    }
  ]
}
EOF

echo "Attaching policy to user..."
aws iam put-user-policy \
  --user-name greg-altoinc \
  --policy-name greg-webcam-bucket-access \
  --policy-document file://greg-s3-policy.json

echo "Done! Access keys saved to greg-credentials.json"
echo ""
echo "Greg can access the webcam-streaming bucket using:"
echo "1. Configure AWS CLI with: aws configure"
echo "2. Enter the Access Key ID and Secret Access Key from greg-credentials.json"
echo "3. Use commands like:"
echo "   - List files: aws s3 ls s3://webcam-streaming/"
echo "   - Download: aws s3 cp s3://webcam-streaming/file.mp4 ./"
echo "   - Upload: aws s3 cp video.mp4 s3://webcam-streaming/"
echo ""
echo "IMPORTANT: Securely share greg-credentials.json and delete it after sharing!"