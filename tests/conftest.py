import pytest

from app.core.config import Settings
from app.repositories.memory import (
    MemoryAgentDefinitionRepository,
    MemoryEventRepository,
    MemoryMessageRepository,
    MemoryPlanRepository,
    MemoryResultRepository,
    MemoryRouteLogRepository,
    MemoryRunRepository,
)
from app.schemas.agents import AgentDefinition
from app.services.registry_service import AgentRegistryService


@pytest.fixture
def settings() -> Settings:
    return Settings(
        storage_backend="memory",
        registry_backend="database",
        router_llm_provider="mock",
        admin_api_token="test-token",
    )


@pytest.fixture
def summarizer_agent() -> AgentDefinition:
    return AgentDefinition.model_validate(
        {
            "agent_id": "summarizer",
            "name": "Summarizer",
            "description": "Summarize text",
            "type": "mock",
            "capabilities": ["summarize"],
            "trigger": {"keywords": ["summarize"]},
            "access_policy": {"allow_roles": ["operator"], "allow_tenants": ["*"]},
            "required_inputs": ["text"],
            "input_schema": {
                "type": "object",
                "required": ["text"],
                "properties": {"text": {"type": "string"}},
            },
            "output_schema": {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
            },
            "invocation": {"type": "mock", "config": {"response": {"summary": "ok"}}},
        }
    )


@pytest.fixture
def task_creator_agent() -> AgentDefinition:
    return AgentDefinition.model_validate(
        {
            "agent_id": "task_creator",
            "name": "Task Creator",
            "description": "Create a task or to-do item from user instructions.",
            "type": "mock",
            "capabilities": ["create_task"],
            "trigger": {
                "keywords": ["task", "todo"],
                "positive_examples": ["create a task from this summary"],
            },
            "access_policy": {"allow_roles": ["operator"], "allow_tenants": ["*"]},
            "required_inputs": ["title"],
            "input_schema": {
                "type": "object",
                "required": ["title"],
                "properties": {"title": {"type": "string"}},
            },
            "output_schema": {
                "type": "object",
                "properties": {"task_id": {"type": "string"}, "title": {"type": "string"}},
            },
            "invocation": {
                "type": "mock",
                "config": {"response": {"task_id": "task_mock_001", "title": "Mock task"}},
            },
        }
    )


@pytest.fixture
def repositories():
    return {
        "registry": MemoryAgentDefinitionRepository(),
        "messages": MemoryMessageRepository(),
        "events": MemoryEventRepository(),
        "runs": MemoryRunRepository(),
        "results": MemoryResultRepository(),
        "plans": MemoryPlanRepository(),
        "route_logs": MemoryRouteLogRepository(),
    }


@pytest.fixture
async def registry_service(settings, repositories, summarizer_agent):
    await repositories["registry"].upsert(summarizer_agent)
    service = AgentRegistryService(settings=settings, repository=repositories["registry"])
    await service.load()
    return service
