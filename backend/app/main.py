from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api.router import api_router
from app.db.init_db import init_db
from app.rag.milvus_schema import create_all_collections
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema
from app.core.config import settings

app = FastAPI(title="Static Chatbot API")

# Add Session Middleware (required for OAuth state management)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.3.160:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup() -> None:
    init_db()
    try:
        create_all_collections()
        print("✅ Milvus collections initialized")
    except Exception as e:
        print(f"⚠️ Failed to initialize Milvus: {e}")

@app.get("/")
def health_check():
    return {"status": "ok"}

app.include_router(api_router)

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql") 
