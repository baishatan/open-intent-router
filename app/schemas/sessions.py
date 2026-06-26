from datetime import datetime

from pydantic import Field

from app.schemas.common import JsonDict, MessageSource, ParticipantRole, StrictBaseModel


class ChatMessage(StrictBaseModel):
    message_id: str
    session_id: str
    user_id: str | None = None
    source: MessageSource
    role: ParticipantRole
    content: str = Field(min_length=1)
    agent_id: str | None = None
    agent_session_id: str | None = None
    request_id: str | None = None
    event_id: str | None = None
    metadata: JsonDict = Field(default_factory=dict)
    created_at: datetime | None = None


class ChatHistoryResponse(StrictBaseModel):
    session_id: str
    messages: list[ChatMessage]
