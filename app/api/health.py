from fastapi import APIRouter

from app.dependencies import get_registry_service

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    registry = get_registry_service()
    state = await registry.load()
    return {
        "status": state.status,
        "registry_status": state.status,
        "active_source": state.active_source,
        "message": state.message,
    }
