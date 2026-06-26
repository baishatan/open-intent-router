import json
from uuid import uuid4

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import LLMError
from app.prompts.router_prompt import RouterPromptTemplate
from app.schemas.routing import LLMRouteInput, RouteResponse


class OpenAICompatibleLLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.prompt_template = RouterPromptTemplate.from_file(settings.router_prompt_file)

    async def route(self, payload: LLMRouteInput) -> RouteResponse:
        if not self.settings.router_llm_base_url:
            raise LLMError("ROUTER_LLM_BASE_URL is required for OpenAI-compatible routing")
        if not self.settings.router_llm_api_key:
            raise LLMError("ROUTER_LLM_API_KEY is required for OpenAI-compatible routing")
        if self.settings.router_llm_api_key.strip() in {
            "replace-with-real-key",
            "your-api-key",
            "your-deepseek-api-key",
        }:
            raise LLMError(
                "ROUTER_LLM_API_KEY is still a placeholder; configure a valid provider API key",
                details={"setting": "ROUTER_LLM_API_KEY"},
            )

        url = self.settings.router_llm_base_url.rstrip("/") + "/v1/chat/completions"
        body = {
            "model": self.settings.router_llm_model,
            "messages": self.prompt_template.messages(payload),
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
        parsed = _normalize_route_response(parsed, payload)
        try:
            return RouteResponse.model_validate(parsed)
        except ValidationError as exc:
            raise LLMError(
                "OpenAI-compatible LLM returned a response that does not match RouteResponse",
                details={"errors": exc.errors()},
            ) from exc


def _normalize_route_response(parsed: object, payload: LLMRouteInput) -> object:
    if not isinstance(parsed, dict):
        return parsed

    candidate_ids = [agent.agent_id for agent in payload.candidates]
    normalized = dict(parsed)
    normalized["request_id"] = normalized.get("request_id") or payload.request.request_id or f"req_{uuid4().hex}"
    normalized["session_id"] = normalized.get("session_id") or payload.request.session_id

    context = normalized.get("context")
    if isinstance(context, dict):
        normalized["context"] = {
            **payload.context.model_dump(mode="json"),
            **context,
            "candidate_agent_ids": context.get("candidate_agent_ids") or candidate_ids,
        }
    else:
        normalized["context"] = {
            **payload.context.model_dump(mode="json"),
            "candidate_agent_ids": candidate_ids,
        }

    return normalized
