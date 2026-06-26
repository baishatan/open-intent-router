import json
from pathlib import Path

import yaml

from app.schemas.routing import LLMRouteInput


DEFAULT_SYSTEM_PROMPT = (
    "你是一个意图识别与 Agent 路由器。"
    "你必须只返回符合 response_schema_hint 的严格 JSON。"
    "target_agent_id 只能从 candidate_agent_ids 中选择。"
)

DEFAULT_USER_TEMPLATE = (
    "请根据 request、candidate_agents 和 context 进行意图识别与路由决策。\n\n"
    "输入数据：\n{payload_json}\n\n"
    "输出要求：只返回 JSON，不要返回 Markdown、解释或代码块。"
)


class RouterPromptTemplate:
    def __init__(
        self,
        *,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        user_template: str = DEFAULT_USER_TEMPLATE,
    ) -> None:
        self.system_prompt = system_prompt
        self.user_template = user_template

    @classmethod
    def from_file(cls, path: str | Path | None) -> "RouterPromptTemplate":
        if not path:
            return cls()
        prompt_path = Path(path)
        if not prompt_path.exists():
            return cls()
        data = yaml.safe_load(prompt_path.read_text(encoding="utf-8")) or {}
        return cls(
            system_prompt=data.get("system_prompt") or DEFAULT_SYSTEM_PROMPT,
            user_template=data.get("user_template") or DEFAULT_USER_TEMPLATE,
        )

    def messages(self, payload: LLMRouteInput) -> list[dict[str, str]]:
        prompt_payload = {
            "request": payload.request.model_dump(mode="json"),
            "candidate_agents": [agent.model_dump(mode="json") for agent in payload.candidates],
            "context": payload.context.model_dump(mode="json"),
            "response_schema_hint": route_response_schema_hint(
                [agent.agent_id for agent in payload.candidates]
            ),
        }
        payload_json = json.dumps(prompt_payload, ensure_ascii=False)
        return [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": self.user_template.replace("{payload_json}", payload_json),
            },
        ]


def route_response_schema_hint(candidate_agent_ids: list[str]) -> dict:
    return {
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
            "candidate_agent_ids": candidate_agent_ids,
            "intent_hint": "string|null",
            "evidence": [],
            "metadata": {},
        },
        "plan": None,
        "invocation": None,
    }
