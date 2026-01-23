from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.db.init_db import init_db

app = FastAPI(title="Static Chatbot API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.3.160:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup() -> None:
    init_db()

@app.get("/")
def health_check():
    return {"status": "ok"}

app.include_router(api_router)