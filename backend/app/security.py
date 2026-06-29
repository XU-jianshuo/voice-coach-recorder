from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.errors import http_error


def require_device_token(
    request: Request, settings: Settings = Depends(get_settings)
) -> None:
    expected = f"Bearer {settings.device_token}"
    if request.headers.get("Authorization") != expected:
        raise http_error(401, "unauthorized", "Valid device token is required")
