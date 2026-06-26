from app.core.config import Settings
from app.schemas.common import JsonDict
from app.schemas.routing import RouteContext, RouteRequest


class ContextService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_route_context(
        self,
        request: RouteRequest,
        *,
        candidate_agent_ids: list[str],
        host_history: list[JsonDict] | None = None,
        agent_history: list[JsonDict] | None = None,
        recent_results: list[JsonDict] | None = None,
        recent_events: list[JsonDict] | None = None,
        evidence: list[JsonDict] | None = None,
        intent_hint: str | None = None,
    ) -> RouteContext:
        relation = "new_task"
        current_agent_id = request.current_agent.agent_id if request.current_agent else None
        if request.current_agent:
            if request.source == "agent_chat":
                relation = "continue_current"
            elif request.input.text and current_agent_id:
                relation = "switch_agent"
        metadata = {
            "source": request.source,
            "session_id": request.session_id,
            "recent_results_count": len(recent_results or []),
            "recent_events_count": len(recent_events or []),
        }
        if request.frontend_context:
            metadata["frontend_context"] = request.frontend_context
        if host_history:
            metadata["host_history"] = host_history[: self.settings.router_max_host_history_messages]
        if agent_history:
            metadata["agent_history"] = agent_history[: self.settings.router_max_agent_history_messages]
        if recent_results:
            metadata["recent_results"] = recent_results[: self.settings.router_max_recent_results]
        if recent_events:
            metadata["recent_events"] = recent_events[: self.settings.router_max_recent_events]
        return RouteContext(
            relation=relation,
            current_agent_id=current_agent_id,
            candidate_agent_ids=candidate_agent_ids,
            intent_hint=intent_hint,
            evidence=evidence or [],
            metadata=metadata,
        )
