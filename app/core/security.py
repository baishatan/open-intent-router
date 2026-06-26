from fastapi import Depends, Header, Request

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError


async def require_admin_token(
    request: Request,
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.admin_api_token
    if not expected:
        if settings.app_env == "local" and _is_loopback_client(request):
            return
        raise AuthenticationError("ADMIN_API_TOKEN is required outside local loopback access")

    token = x_admin_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    if token != expected:
        raise AuthenticationError("Invalid admin token")


def _is_loopback_client(request: Request) -> bool:
    host = request.client.host if request.client else ""
    return host in {"127.0.0.1", "::1", "localhost", "testclient"}
