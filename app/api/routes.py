from fastapi import APIRouter, Depends, status

from app.models.chat import ChatRequest, ChatResponse, HealthResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="", tags=["SHL Recommender"])


def get_chat_service() -> ChatService:
    return ChatService()


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", message="SHL Assessment Recommender is healthy.")


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)) -> ChatResponse:
    return await chat_service.handle_chat(request)
