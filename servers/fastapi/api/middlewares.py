import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from utils.get_env import get_can_change_keys_env
from utils.user_config import update_env_with_user_config

logger = logging.getLogger(__name__)


class UserConfigEnvUpdateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if get_can_change_keys_env() != "false":
            try:
                update_env_with_user_config()
            except Exception as e:
                logger.error(f"Error updating env with user config: {e}")
        return await call_next(request)
