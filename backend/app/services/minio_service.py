import tempfile, os
from minio import Minio
from app.core.config import settings

class MinioSettings:
    MINIO_ENDPOINT = settings.MINIO_ENDPOINT
    MINIO_ACCESS_KEY = settings.MINIO_ACCESS_KEY
    MINIO_SECRET_KEY = settings.MINIO_SECRET_KEY
    MINIO_BUCKET = settings.MINIO_BUCKET

settings = MinioSettings()

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False
)

def ensure_bucket(bucket_name: str):
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

def upload_fileobj(bucket_name: str, object_name: str, fileobj):
    ensure_bucket(bucket_name)
    # fileobj must be a readable file-like object positioned at start
    fileobj.seek(0)
    # minio requires size or will stream; we'll read bytes to memory for simplicity (not ideal for huge files)
    data = fileobj.read()
    from io import BytesIO
    data_stream = BytesIO(data)
    minio_client.put_object(bucket_name, object_name, data_stream, length=len(data))

def download_to_temp(bucket_name: str, object_name: str) -> str:
    ensure_bucket(bucket_name)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix="_"+object_name)
    try:
        response = minio_client.get_object(bucket_name, object_name)
        with open(tmp.name, "wb") as f:
            for d in response.stream(32*1024):
                f.write(d)
        return tmp.name
    finally:
        try:
            response.close()
            response.release_conn()
        except:
            pass
