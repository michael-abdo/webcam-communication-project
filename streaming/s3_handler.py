"""S3 handler for generating presigned URLs for direct browser uploads."""

import os
import boto3
from datetime import datetime
import uuid
from botocore.exceptions import ClientError

# AWS Configuration
AWS_PROFILE = 'zenex'
AWS_REGION = 'us-west-2'
S3_BUCKET = 'xendoex-webcam-streaming-2025'

# Initialize S3 client with specific profile
def get_s3_client():
    """Get S3 client with proper configuration."""
    try:
        # In production (Heroku), use environment variables
        if os.environ.get('AWS_ACCESS_KEY_ID'):
            print("Using AWS environment variables for S3 client")
            return boto3.client(
                's3', 
                region_name=AWS_REGION,
                endpoint_url=f'https://s3.{AWS_REGION}.amazonaws.com',
                config=boto3.session.Config(
                    s3={'addressing_style': 'virtual'},
                    signature_version='s3v4',
                    region_name=AWS_REGION
                )
            )
        else:
            # Development mode - try AWS profile
            try:
                print(f"Attempting to use AWS profile: {AWS_PROFILE}")
                session = boto3.Session(profile_name=AWS_PROFILE)
                return session.client(
                    's3', 
                    region_name=AWS_REGION,
                    endpoint_url=f'https://s3.{AWS_REGION}.amazonaws.com',
                    config=boto3.session.Config(
                        s3={'addressing_style': 'virtual'},
                        signature_version='s3v4',
                        region_name=AWS_REGION
                    )
                )
            except Exception as profile_error:
                error_msg = (
                    f"Failed to use AWS profile '{AWS_PROFILE}': {profile_error}\n"
                    "AWS credentials not configured. Please either:\n"
                    "1. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables\n"
                    "2. Configure AWS profile 'zenex' locally\n"
                    "For Heroku deployment, use: heroku config:set AWS_ACCESS_KEY_ID=your_key AWS_SECRET_ACCESS_KEY=your_secret"
                )
                print(error_msg)
                raise Exception(error_msg)
    except Exception as e:
        print(f"Error creating S3 client: {e}")
        raise

def generate_presigned_post(session_id=None, chunk_number=0):
    """
    Generate a presigned POST URL for direct browser upload to S3.
    
    Args:
        session_id: Unique session identifier (generated if not provided)
        chunk_number: Sequential chunk number for this session
        
    Returns:
        dict: Contains 'url' and 'fields' for the presigned POST, or None on error
    """
    try:
        # Attempt to get S3 client - this will raise exception if credentials missing
        s3_client = get_s3_client()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create S3 key with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        key = f"recordings/{session_id}/{timestamp}_chunk_{chunk_number:04d}.webm"
        
        # Generate presigned POST URL
        # Expires in 5 minutes
        response = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET,
            Key=key,
            ExpiresIn=300,  # 5 minutes
            Conditions=[
                {'content-type': 'video/webm'},
                ['content-length-range', 0, 50 * 1024 * 1024]  # Max 50MB
            ]
        )
        
        # Add additional fields for browser upload
        response['fields']['Content-Type'] = 'video/webm'
        response['key'] = key
        response['session_id'] = session_id
        
        return response
        
    except ClientError as e:
        error_msg = f"AWS S3 Error generating presigned URL: {e}"
        print(error_msg)
        # Check if it's a credentials error
        if e.response['Error']['Code'] == 'InvalidAccessKeyId':
            print("Invalid AWS Access Key ID - check your credentials")
        elif e.response['Error']['Code'] == 'SignatureDoesNotMatch':
            print("Invalid AWS Secret Access Key - check your credentials")
        return None
    except Exception as e:
        # This will catch credential configuration errors from get_s3_client
        print(f"Error in generate_presigned_post: {e}")
        return None

def ensure_bucket_exists():
    """Ensure S3 bucket exists with proper configuration."""
    try:
        s3_client = get_s3_client()
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=S3_BUCKET)
            print(f"Bucket {S3_BUCKET} exists")
            return True
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                # Bucket doesn't exist, create it
                print(f"Creating bucket {S3_BUCKET}")
                s3_client.create_bucket(
                    Bucket=S3_BUCKET,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                )
                
                # Set CORS configuration for browser uploads
                cors_config = {
                    'CORSRules': [{
                        'AllowedHeaders': ['*'],
                        'AllowedMethods': ['POST', 'PUT'],
                        'AllowedOrigins': ['*'],
                        'ExposeHeaders': ['ETag'],
                        'MaxAgeSeconds': 3000
                    }]
                }
                s3_client.put_bucket_cors(
                    Bucket=S3_BUCKET,
                    CORSConfiguration=cors_config
                )
                
                print(f"Bucket {S3_BUCKET} created with CORS configuration")
                return True
            else:
                print(f"Error checking bucket: {e}")
                return False
                
    except Exception as e:
        print(f"Error ensuring bucket exists: {e}")
        return False