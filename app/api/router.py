from fastapi import APIRouter, Depends

from app.dependencies import get_invocation_service, get_router_service
from app.schemas.invocation import InvokeRequest, RouteAndInvokeResponse
from app.schemas.routing import RouteRequest, RouteResponse
from app.services.invocation_service import InvocationService
from app.services.router_service import RouterService

router = APIRouter(prefix="/api/v1", tags=["router"])


@router.post("/route", response_model=RouteResponse)
async def route(
    payload: RouteRequest,
    router_service: RouterService = Depends(get_router_service),
) -> RouteResponse:
    return await router_service.route(payload)


@router.post("/invoke")
async def invoke(
    payload: InvokeRequest,
    invocation_service: InvocationService = Depends(get_invocation_service),
):
    return await invocation_service.invoke(payload)


@router.post("/route-and-invoke", response_model=RouteAndInvokeResponse)
async def route_and_invoke(
    payload: RouteRequest,
    router_service: RouterService = Depends(get_router_service),
    invocation_service: InvocationService = Depends(get_invocation_service),
) -> RouteAndInvokeResponse:
    route_response = await router_service.route(payload)
    result = await invocation_service.invoke_from_route(payload, route_response)
    return RouteAndInvokeResponse(route=route_response.model_dump(), result=result)
