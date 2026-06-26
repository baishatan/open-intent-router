from fastapi import APIRouter, Depends

from app.dependencies import get_chat_history_service
from app.schemas.sessions import ChatHistoryResponse
from app.services.chat_history_service import ChatHistoryService

router = APIRouter(prefix="/api/v1", tags=["sessions"])


@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryResponse)
async def session_messages(
    session_id: str,
    chat_history: ChatHistoryService = Depends(get_chat_history_service),
) -> ChatHistoryResponse:
    messages = await chat_history.get_host_history(session_id)
    return ChatHistoryResponse(session_id=session_id, messages=messages)
