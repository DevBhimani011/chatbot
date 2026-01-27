from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.db.init_db import init_db

app = FastAPI(title="Static Chatbot API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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