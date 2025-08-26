# AWS Credentials Setup for Heroku

## Prerequisites
- AWS account with appropriate S3 permissions
- AWS Access Key ID and Secret Access Key
- Heroku CLI installed

## Required AWS Permissions
The IAM user needs the following permissions for the S3 bucket `webcam-streaming`:
- `s3:PutObject`
- `s3:PutObjectAcl`
- `s3:GetObject`
- `s3:ListBucket`
- `s3:CreateBucket`
- `s3:PutBucketCORS`

## Setting AWS Credentials on Heroku

### Option 1: Using Heroku CLI (Recommended)
```bash
heroku config:set AWS_ACCESS_KEY_ID=your_access_key_id
heroku config:set AWS_SECRET_ACCESS_KEY=your_secret_access_key
heroku config:set AWS_DEFAULT_REGION=us-west-2
```

### Option 2: Using Heroku Dashboard
1. Go to your app at https://dashboard.heroku.com/apps/fatigue-detection-api
2. Navigate to Settings tab
3. Click "Reveal Config Vars"
4. Add the following key-value pairs:
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
   - `AWS_DEFAULT_REGION`: us-west-2

## Verifying Configuration
Check if credentials are set:
```bash
heroku config
```

## Creating AWS Access Keys
1. Log in to AWS Console
2. Go to IAM → Users
3. Select your user or create a new one
4. Go to Security credentials tab
5. Click "Create access key"
6. Select "Application running outside AWS"
7. Save the credentials securely

## S3 Bucket Configuration
The app expects a bucket named `webcam-streaming` in the `us-west-2` region.

To create it manually:
```bash
aws s3 mb s3://webcam-streaming --region us-west-2
```

The app will attempt to create the bucket automatically with proper CORS configuration if it doesn't exist.

## Troubleshooting

### Error: "AWS credentials not configured"
This means the environment variables are not set. Follow the setup steps above.

### Error: "Invalid Access Key ID"
Double-check that your AWS_ACCESS_KEY_ID is correct and doesn't have extra spaces.

### Error: "Signature does not match"
Your AWS_SECRET_ACCESS_KEY is incorrect. Make sure to copy it exactly.

### Error: "Access Denied"
Your IAM user doesn't have the required S3 permissions. Update the IAM policy.

## Security Best Practices
1. Never commit AWS credentials to Git
2. Use IAM users with minimal required permissions
3. Rotate access keys regularly
4. Consider using AWS IAM roles for production deployments

## Local Development
For local development, you can either:
1. Set the same environment variables locally
2. Configure AWS CLI with profile 'zenex': `aws configure --profile zenex`