from fastapi import APIRouter

from app.api.routers import flows, documents, knowledge_bases, chatbots, health, flow_execution

api_router = APIRouter()

# Include all routers (will be implemented later)
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(flows.router, prefix="/flows", tags=["flows"])
api_router.include_router(flow_execution.router, prefix="/flow-execution", tags=["flow-execution"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(knowledge_bases.router, prefix="/knowledge-bases", tags=["knowledge-bases"])
api_router.include_router(chatbots.router, prefix="/chatbots", tags=["chatbots"]) 