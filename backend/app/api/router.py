from fastapi import APIRouter
from app.api.routes import workflow
from app.api.routes import chatbot
from app.api.routes import tree_workflow
from app.api.routes import documents
from app.api.routes import auth

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(workflow.router)
api_router.include_router(chatbot.router)
api_router.include_router(tree_workflow.router)
api_router.include_router(documents.router)
from app.api.routes import chat_ws
api_router.include_router(chat_ws.router, prefix="/chat", tags=["Realtime Chat"])



