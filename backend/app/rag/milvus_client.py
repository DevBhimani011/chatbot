from pymilvus import connections
from app.core.config import settings

def connect_milvus():
    connections.connect(
        alias="default",
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT
    )
