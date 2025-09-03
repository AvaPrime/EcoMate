import os, uuid
import boto3
from botocore.client import Config

MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "ecomate-artifacts")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")

_s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ROOT_USER,
    aws_secret_access_key=MINIO_ROOT_PASSWORD,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

def ensure_bucket():
    try:
        _s3.head_bucket(Bucket=MINIO_BUCKET)
    except Exception:
        _s3.create_bucket(Bucket=MINIO_BUCKET)

def put_bytes(prefix: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    ensure_bucket()
    key = f"{prefix.strip('/')}/{uuid.uuid4().hex}"
    _s3.put_object(Bucket=MINIO_BUCKET, Key=key, Body=data, ContentType=content_type)
    return f"s3://{MINIO_BUCKET}/{key}"