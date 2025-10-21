"""S3 helpers for Phase 1 capture storage."""

import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from typing import IO, Optional
import uuid
import mimetypes

# AWS Configuration
AWS_PROFILE = 'zenex'
AWS_REGION = 'us-west-2'
S3_BUCKET = 'webcam-streaming'

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

def build_chunk_key(session_id: str, sequence_no: Optional[int] = None, extension: str = "webm") -> str:
    """Create an S3 object key for a chunk."""
    safe_ext = extension.lstrip(".") if extension else "webm"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    if sequence_no is not None:
        return f"recordings/{session_id}/{timestamp}_chunk_{sequence_no:04d}_{unique_id}.{safe_ext}"
    return f"recordings/{session_id}/{timestamp}_{unique_id}.{safe_ext}"


def upload_chunk_file(
    session_id: str,
    file_obj: IO[bytes],
    content_type: Optional[str],
    sequence_no: Optional[int] = None,
    extension: Optional[str] = None,
) -> str:
    """
    Upload a chunk file object to S3 and return the storage key.

    Args:
        session_id: Capture session identifier
        file_obj: File-like object positioned at start
        content_type: MIME type to set on S3 object
        sequence_no: Optional sequence number for predictable naming
        extension: Optional extension (without dot). Derived from MIME if missing.
    """
    s3_client = get_s3_client()

    resolved_ext = extension
    if not resolved_ext and content_type:
        resolved_ext = mimetypes.guess_extension(content_type.split(";")[0] if content_type else "")
        if resolved_ext:
            resolved_ext = resolved_ext.lstrip(".")
    if not resolved_ext:
        resolved_ext = "webm"

    key = build_chunk_key(session_id, sequence_no=sequence_no, extension=resolved_ext)

    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    file_obj.seek(0)
    s3_client.upload_fileobj(
        file_obj,
        S3_BUCKET,
        key,
        ExtraArgs=extra_args or None,
    )

    return key

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

def generate_download_url(key, expiration=3600):
    """Generate presigned URL for downloading from S3"""
    try:
        s3_client = get_s3_client()
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=expiration
        )
    except Exception as e:
        print(f"Error generating download URL: {e}")
        return None
