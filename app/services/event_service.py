from app.schemas.events import AgentEvent, AgentEventResponse, ConversationEvent


class EventService:
    def __init__(self, repository) -> None:
        self.repository = repository

    async def record_conversation_event(self, event: ConversationEvent) -> ConversationEvent:
        return await self.repository.add_conversation_event(event)

    async def record_agent_event(self, event: AgentEvent) -> AgentEventResponse:
        saved, duplicate = await self.repository.add_agent_event(event)
        return AgentEventResponse(event_id=saved.event_id, accepted=True, duplicate=duplicate)
