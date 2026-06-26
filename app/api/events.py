from fastapi import APIRouter, Depends

from app.dependencies import get_event_service, get_plan_service
from app.schemas.events import AgentEvent, AgentEventResponse
from app.services.event_service import EventService
from app.services.plan_service import PlanService

router = APIRouter(prefix="/api/v1", tags=["events"])


@router.post("/events/agent", response_model=AgentEventResponse)
async def agent_event(
    payload: AgentEvent,
    event_service: EventService = Depends(get_event_service),
    plan_service: PlanService = Depends(get_plan_service),
) -> AgentEventResponse:
    response = await event_service.record_agent_event(payload)
    if not response.duplicate:
        await plan_service.apply_agent_event(payload)
    return response


@router.post("/runs/{run_id}/events", response_model=AgentEventResponse)
async def run_agent_event(
    run_id: str,
    payload: AgentEvent,
    event_service: EventService = Depends(get_event_service),
    plan_service: PlanService = Depends(get_plan_service),
) -> AgentEventResponse:
    event = payload.model_copy(update={"run_id": payload.run_id or run_id})
    response = await event_service.record_agent_event(event)
    if not response.duplicate:
        await plan_service.apply_agent_event(event)
    return response
