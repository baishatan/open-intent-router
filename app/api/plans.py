from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_plan_service
from app.schemas.plans import Plan, PlanActionRequest, PlanActionResponse
from app.services.plan_service import PlanService

router = APIRouter(prefix="/api/v1", tags=["plans"])


@router.get("/plans/{plan_id}", response_model=Plan)
async def get_plan(
    plan_id: str,
    plan_service: PlanService = Depends(get_plan_service),
) -> Plan:
    plan = await plan_service.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/plans/{plan_id}/actions", response_model=PlanActionResponse)
async def plan_action(
    plan_id: str,
    payload: PlanActionRequest,
    plan_service: PlanService = Depends(get_plan_service),
) -> PlanActionResponse:
    try:
        if payload.action == "confirm":
            return await plan_service.confirm(plan_id)
        return await plan_service.cancel(plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
