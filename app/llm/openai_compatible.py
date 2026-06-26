import json

import httpx

from app.core.config import Settings
from app.core.errors import LLMError
from app.schemas.routing import LLMRouteInput, RouteResponse


class OpenAICompatibleLLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def route(self, payload: LLMRouteInput) -> RouteResponse:
        if not self.settings.router_llm_base_url:
            raise LLMError("ROUTER_LLM_BASE_URL is required for OpenAI-compatible routing")
        if not self.settings.router_llm_api_key:
            raise LLMError("ROUTER_LLM_API_KEY is required for OpenAI-compatible routing")

        url = self.settings.router_llm_base_url.rstrip("/") + "/v1/chat/completions"
        body = {
            "model": self.settings.router_llm_model,
            "messages": _messages(payload),
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.router_llm_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.router_llm_timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=body)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError("OpenAI-compatible LLM request failed", details={"error": str(exc)}) from exc

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LLMError("OpenAI-compatible LLM returned invalid JSON") from exc
        return RouteResponse.model_validate(parsed)


def _messages(payload: LLMRouteInput) -> list[dict[str, str]]:
    candidates = [agent.model_dump() for agent in payload.candidates]
    context = payload.context.model_dump()
    request = payload.request.model_dump()
    schema_hint = {
        "request_id": "string",
        "session_id": "string",
        "decision": {
            "status": "ok|clarify|unsupported|error",
            "action": "reply|clarify|open_agent|continue_agent|exit_agent|show_plan|unsupported|silent",
            "target_agent_id": "string|null",
            "confidence": "number|null",
            "reason": "string",
            "message": "string",
        },
        "context": {
            "relation": "new_task|continue_current|switch_agent|exit_agent|multi_task|unsupported",
            "current_agent_id": "string|null",
            "artifact_refs": [],
            "candidate_agent_ids": [agent.agent_id for agent in payload.candidates],
        },
        "plan": None,
        "invocation": None,
    }
    return [
        {
            "role": "system",
            "content": (
                "You are an intent router. Return only strict JSON matching the schema. "
                "Choose target_agent_id only from candidate_agent_ids."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "request": request,
                    "candidate_agents": candidates,
                    "context": context,
                    "response_schema_hint": schema_hint,
                },
                ensure_ascii=False,
            ),
        },
    ]
