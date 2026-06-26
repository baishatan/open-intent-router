from app.schemas.invocation import InvokeRequest
from app.schemas.routing import RouteRequest
from app.services.invocation_service import InvocationService, build_default_invoker_registry
from app.services.router_service import RouterService


async def test_mock_router_returns_invocation_preview(settings, registry_service) -> None:
    service = RouterService(settings=settings, registry=registry_service)
    response = await service.route(
        RouteRequest.model_validate(
            {
                "session_id": "s1",
                "user": {"id": "u1", "roles": ["operator"], "attributes": {"tenant_id": "t1"}},
                "input": {"text": "summarize this text"},
            }
        )
    )
    assert response.decision.action == "open_agent"
    assert response.invocation
    assert response.invocation.input["text"] == "summarize this text"


async def test_mock_invocation_persists_run_and_result(settings, registry_service, repositories) -> None:
    service = InvocationService(
        registry=registry_service,
        run_repository=repositories["runs"],
        result_repository=repositories["results"],
        invokers=build_default_invoker_registry(settings),
    )
    result = await service.invoke(
        InvokeRequest(
            session_id="s1",
            agent_id="summarizer",
            user={"id": "u1", "roles": ["operator"]},
            input={"text": "hello"},
        )
    )
    assert result.status == "completed"
    assert await repositories["runs"].get_run(result.run_id)
    assert (await repositories["results"].list_recent("s1"))[0].run_id == result.run_id
