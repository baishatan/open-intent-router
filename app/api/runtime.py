from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.dependencies import get_registry_service
from app.schemas.runtime import RuntimeConfigResponse
from app.services.registry_service import AgentRegistryService

router = APIRouter(prefix="/api/v1", tags=["runtime"])


@router.get("/runtime/config", response_model=RuntimeConfigResponse)
async def runtime_config(
    settings: Settings = Depends(get_settings),
    registry: AgentRegistryService = Depends(get_registry_service),
) -> RuntimeConfigResponse:
    if registry.state.active_source == "none":
        await registry.load()
    admin_auth_mode = _admin_auth_mode(settings)
    registry_mutation_mode = _registry_mutation_mode(settings, admin_auth_mode)
    return RuntimeConfigResponse(
        app_env=settings.app_env,
        storage_backend=settings.storage_backend,
        registry_backend=settings.registry_backend,
        registry_status=registry.state.status,
        registry_active_source=registry.state.active_source,
        registry_message=registry.state.message,
        registry_agent_count=len(registry.state.agents),
        route_mode=settings.route_mode,
        router_llm_provider=settings.router_llm_provider,
        router_llm_model=settings.router_llm_model,
        router_llm_base_url=settings.router_llm_base_url,
        router_prompt_file=settings.router_prompt_file,
        router_llm_api_key_configured=bool(settings.router_llm_api_key),
        admin_api_token_configured=bool(settings.admin_api_token),
        admin_auth_mode=admin_auth_mode,
        registry_mutation_mode=registry_mutation_mode,
        evidence_provider_enabled=settings.evidence_provider_enabled,
        evidence_fixed_questions_path=settings.evidence_fixed_questions_path,
        agent_http_timeout_seconds=settings.agent_http_timeout_seconds,
    )


def _admin_auth_mode(settings: Settings) -> str:
    if settings.admin_api_token:
        return "token_required"
    if settings.app_env == "local":
        return "local_loopback_open"
    return "token_missing"


def _registry_mutation_mode(settings: Settings, admin_auth_mode: str) -> str:
    if settings.registry_backend == "file":
        return "read_only_file"
    if admin_auth_mode == "local_loopback_open":
        return "local_dev_write_enabled"
    if admin_auth_mode == "token_required":
        return "token_required"
    return "disabled_token_missing"
