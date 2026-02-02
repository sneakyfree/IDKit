"""
WebSocket Authentication

Handles JWT authentication for WebSocket connections.
"""

from typing import Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import async_session_factory
from app.models.user import User


async def websocket_auth(
    websocket: WebSocket,
    token: Optional[str] = None,
) -> Optional[User]:
    """
    Authenticate a WebSocket connection.

    Accepts token from:
    1. Query parameter: ws://...?token=xxx
    2. First message after connection

    Returns:
        User if authenticated, None otherwise.
    """
    # Try to get token from query params
    if token is None:
        token = websocket.query_params.get("token")

    if token is None:
        return None

    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        # Fetch user from database
        async with async_session_factory() as db:
            result = await db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = result.scalar_one_or_none()

            if user is None or not user.is_active:
                return None

            return user

    except (JWTError, ValueError) as e:
        return None


async def require_websocket_auth(
    websocket: WebSocket,
    token: Optional[str] = None,
) -> User:
    """
    Require authentication for WebSocket connection.

    Raises WebSocketException if not authenticated.
    """
    user = await websocket_auth(websocket, token)

    if user is None:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication required",
        )

    return user


class WebSocketAuthMiddleware:
    """
    WebSocket authentication middleware.

    Authenticates connection on first message if not authenticated via query param.
    """

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.user: Optional[User] = None
        self._authenticated = False

    async def authenticate(self) -> Optional[User]:
        """Authenticate from query parameter."""
        self.user = await websocket_auth(self.websocket)
        self._authenticated = self.user is not None
        return self.user

    async def authenticate_from_message(self, message: dict) -> Optional[User]:
        """
        Authenticate from message payload.

        Expected message format:
        {
            "type": "auth",
            "token": "jwt_token_here"
        }
        """
        if message.get("type") != "auth":
            return None

        token = message.get("token")
        if not token:
            return None

        self.user = await websocket_auth(self.websocket, token)
        self._authenticated = self.user is not None
        return self.user

    @property
    def is_authenticated(self) -> bool:
        """Check if connection is authenticated."""
        return self._authenticated

    def require_auth(self) -> User:
        """
        Require authentication.

        Raises WebSocketException if not authenticated.
        """
        if not self._authenticated or self.user is None:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Authentication required",
            )
        return self.user
