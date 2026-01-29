from minio import Minio
from app.core.config import settings

def get_minio_client():
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )

def upload_pdf(file_path: str, object_name: str):
    client = get_minio_client()

    if not client.bucket_exists("documents"):
        client.make_bucket("documents")

    client.fput_object(
        bucket_name="documents",
        object_name=object_name,
        file_path=file_path,
    )
