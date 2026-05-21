"""MinIO / S3 helpers."""

from __future__ import annotations

from functools import lru_cache

import boto3
from botocore.client import Config

from app.core.config import settings


def _make_s3_client(endpoint_url: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


@lru_cache(maxsize=1)
def get_s3_client():
    return _make_s3_client(settings.s3_endpoint_url)


@lru_cache(maxsize=1)
def get_s3_presign_client():
    return _make_s3_client(settings.s3_presign_endpoint_url)


def presigned_put_url(key: str, content_type: str, expires_in: int = 600) -> str:
    return get_s3_presign_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )


def get_object_bytes(key: str) -> bytes:
    obj = get_s3_client().get_object(Bucket=settings.s3_bucket, Key=key)
    return obj["Body"].read()
