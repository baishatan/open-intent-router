from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_repository_bundle

router = APIRouter(prefix="/api/v1", tags=["runs"])


@router.get("/runs/{run_id}")
async def get_run(run_id: str, repositories: dict = Depends(get_repository_bundle)):
    run = await repositories["runs"].get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
