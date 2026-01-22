from minio import Minio

def get_minio_client():
    return Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
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
