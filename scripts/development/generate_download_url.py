#!/usr/bin/env python3
"""Generate download URL for uploaded WebM chunk."""

from streaming.s3_handler import get_s3_client, S3_BUCKET

# Generate download URL for the first chunk from your session
session_id = 'session_1755360928824_cacnxl8'
chunk_key = f'recordings/{session_id}/20250816_161534_chunk_0000.webm'

try:
    s3_client = get_s3_client()
    
    # Generate presigned download URL (expires in 1 hour)
    download_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': chunk_key},
        ExpiresIn=3600  # 1 hour
    )
    
    print(f'Download URL for chunk 0000:')
    print(download_url)
    print()
    print(f'File: {chunk_key}')
    
except Exception as e:
    print(f'Error generating download URL: {e}')