from __future__ import annotations

from io import BytesIO
import os
import tempfile
import boto3
from botocore.client import Config

from app.core.config import get_settings


def _client(*, endpoint_url: str | None = None):
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url or s.media_s3_endpoint,
        aws_access_key_id=s.media_s3_access_key,
        aws_secret_access_key=s.media_s3_secret_key,
        region_name=s.media_s3_region,
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket() -> None:
    s = get_settings()
    c = _client()
    try:
        c.head_bucket(Bucket=s.media_s3_bucket)
    except Exception:
        c.create_bucket(Bucket=s.media_s3_bucket)


def download_bytes(key: str) -> bytes:
    s = get_settings()
    obj = _client().get_object(Bucket=s.media_s3_bucket, Key=key)
    return obj["Body"].read()


def download_to_tempfile(key: str, *, suffix: str = ".mp4") -> str:
    """Stream a media object to a bounded temporary file for local processing."""
    s = get_settings()
    client = _client()
    metadata = client.head_object(Bucket=s.media_s3_bucket, Key=key)
    size = int(metadata.get("ContentLength", 0))
    if size > s.media_max_recording_bytes:
        raise ValueError("MEDIA_FILE_TOO_LARGE")
    fd, path = tempfile.mkstemp(prefix="iarh-media-", suffix=suffix)
    os.close(fd)
    try:
        response = client.get_object(Bucket=s.media_s3_bucket, Key=key)
        body = response["Body"]
        written = 0
        try:
            with open(path, "wb") as output:
                for chunk in iter(lambda: body.read(8 * 1024 * 1024), b""):
                    written += len(chunk)
                    if written > s.media_max_recording_bytes:
                        raise ValueError("MEDIA_FILE_TOO_LARGE")
                    output.write(chunk)
        finally:
            body.close()
        return path
    except Exception:
        try:
            os.remove(path)
        except OSError:
            pass
        raise


def upload_bytes(key: str, data: bytes, *, content_type: str) -> None:
    s = get_settings()
    _client().put_object(
        Bucket=s.media_s3_bucket,
        Key=key,
        Body=BytesIO(data),
        ContentType=content_type,
        ServerSideEncryption="AES256",
    )


def delete_object(key: str) -> None:
    s = get_settings()
    _client().delete_object(Bucket=s.media_s3_bucket, Key=key)


def presigned_get_url(key: str, *, expires: int | None = None) -> str:
    s = get_settings()
    client = _client(endpoint_url=s.media_s3_public_endpoint or s.media_s3_endpoint)
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": s.media_s3_bucket, "Key": key},
        ExpiresIn=expires or s.media_s3_presigned_ttl_seconds,
    )
