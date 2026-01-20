from fastapi import APIRouter
from app.api.routes import workflow
from app.api.routes import node
from app.api.routes import edge
from app.api.routes import chatbot




api_router = APIRouter()
api_router.include_router(workflow.router)
api_router.include_router(node.router)
api_router.include_router(edge.router)
api_router.include_router(chatbot.router)



