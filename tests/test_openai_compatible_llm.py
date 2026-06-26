import pytest

from app.core.config import Settings
from app.core.errors import LLMError
from app.llm.openai_compatible import OpenAICompatibleLLMClient, _normalize_route_response
from app.schemas.routing import LLMRouteInput, RouteContext, RouteRequest


async def test_openai_compatible_llm_rejects_placeholder_api_key() -> None:
    client = OpenAICompatibleLLMClient(
        Settings(
            router_llm_provider="openai_compatible",
            router_llm_base_url="https://api.deepseek.com",
            router_llm_api_key="replace-with-real-key",
        )
    )

    with pytest.raises(LLMError) as exc_info:
        await client.route(
            LLMRouteInput(
                request=RouteRequest.model_validate(
                    {
                        "session_id": "s1",
                        "user": {"id": "u1", "roles": ["operator"]},
                        "input": {"text": "hello"},
                    }
                ),
                candidates=[],
                context=RouteContext(candidate_agent_ids=[]),
            )
        )

    assert "placeholder" in exc_info.value.message


def test_openai_compatible_llm_normalizes_framework_fields() -> None:
    payload = _payload()

    normalized = _normalize_route_response(
        {
            "request_id": None,
            "session_id": None,
            "decision": {
                "status": "ok",
                "action": "open_agent",
                "target_agent_id": "summarizer",
                "confidence": 0.8,
                "reason": "Matched summarization intent.",
                "message": "Routing to summarizer.",
            },
            "context": {"relation": "new_task", "candidate_agent_ids": []},
            "plan": None,
            "invocation": None,
        },
        payload,
    )

    assert isinstance(normalized, dict)
    assert normalized["request_id"].startswith("req_")
    assert normalized["session_id"] == "s1"
    assert normalized["context"]["candidate_agent_ids"] == ["summarizer"]


def test_openai_compatible_llm_normalizes_incomplete_plan() -> None:
    payload = _multi_agent_payload()

    normalized = _normalize_route_response(
        {
            "decision": {
                "status": "ok",
                "action": "show_plan",
                "target_agent_id": "summarizer",
                "confidence": 0.8,
                "reason": "Multi-step request.",
                "message": "Show plan.",
            },
            "context": {"relation": "multi_task"},
            "plan": {
                "steps": [
                    {
                        "agent_id": "summarizer",
                        "description": "Summarize the text.",
                    },
                    {
                        "agent_id": "task_creator",
                        "description": "Create a task.",
                        "depends_on": ["step_1"],
                    },
                ]
            },
        },
        payload,
    )

    assert isinstance(normalized, dict)
    assert normalized["decision"]["target_agent_id"] is None
    assert normalized["plan"]["plan_id"].startswith("plan_")
    assert normalized["plan"]["session_id"] == "s1"
    assert normalized["plan"]["current_step_id"] == "step_1"
    assert normalized["plan"]["steps"][0]["status"] == "pending"


def test_openai_compatible_llm_builds_fallback_plan_for_show_plan_without_steps() -> None:
    payload = _multi_agent_payload()

    normalized = _normalize_route_response(
        {
            "decision": {
                "status": "ok",
                "action": "show_plan",
                "target_agent_id": None,
                "confidence": 0.8,
                "reason": "Multi-step request.",
                "message": "Show plan.",
            },
            "context": {"relation": "multi_task"},
            "plan": None,
        },
        payload,
    )

    assert isinstance(normalized, dict)
    assert normalized["plan"]["steps"][0]["agent_id"] == "summarizer"
    assert normalized["plan"]["steps"][1]["agent_id"] == "task_creator"


def _payload() -> LLMRouteInput:
    from app.schemas.agents import CandidateAgent

    return LLMRouteInput(
        request=RouteRequest.model_validate(
            {
                "session_id": "s1",
                "user": {"id": "u1", "roles": ["operator"]},
                "input": {"text": "summarize this text"},
            }
        ),
        candidates=[
            CandidateAgent(agent_id="summarizer", name="Summarizer", description="Summarize text")
        ],
        context=RouteContext(candidate_agent_ids=["summarizer"]),
    )


def _multi_agent_payload() -> LLMRouteInput:
    from app.schemas.agents import CandidateAgent

    return LLMRouteInput(
        request=RouteRequest.model_validate(
            {
                "session_id": "s1",
                "user": {"id": "u1", "roles": ["operator"]},
                "input": {"text": "first summarize this text, then create a task"},
            }
        ),
        candidates=[
            CandidateAgent(agent_id="summarizer", name="Summarizer", description="Summarize text"),
            CandidateAgent(
                agent_id="task_creator",
                name="Task Creator",
                description="Create a task from instructions",
            ),
        ],
        context=RouteContext(candidate_agent_ids=["summarizer", "task_creator"]),
    )
