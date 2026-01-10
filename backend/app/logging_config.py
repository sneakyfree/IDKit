"""
Structured JSON Logging Configuration for IDKit

This module provides a centralized logging configuration using structlog
for structured JSON output that is optimized for log aggregation systems
like ELK, Datadog, or CloudWatch.

Features:
- JSON output format for machine parsing
- Request correlation IDs for tracing
- Structured fields (user_id, request_id, action)
- Log level filtering by environment
- Integration with standard library logging
- Colorized console output in development
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.config import settings


def add_environment_info(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add environment information to all log entries."""
    event_dict["environment"] = settings.environment
    event_dict["service"] = "idkit-api"
    event_dict["version"] = settings.version
    return event_dict


def add_request_id(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add request ID from context if available."""
    from contextvars import ContextVar

    # Request ID is set by middleware
    request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
    request_id = request_id_var.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def censor_sensitive_data(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Censor sensitive data from log entries."""
    sensitive_keys = {
        "password",
        "token",
        "secret",
        "api_key",
        "apikey",
        "authorization",
        "auth",
        "credential",
        "private_key",
        "access_token",
        "refresh_token",
        "jwt",
        "bearer",
    }

    def censor_dict(d: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for key, value in d.items():
            lower_key = key.lower()
            if any(sensitive in lower_key for sensitive in sensitive_keys):
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = censor_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    censor_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    return censor_dict(event_dict)


def get_log_level() -> int:
    """Get log level based on environment."""
    level_map = {
        "development": logging.DEBUG,
        "staging": logging.INFO,
        "production": logging.INFO,
    }
    return level_map.get(settings.environment, logging.INFO)


def get_processors() -> list[Processor]:
    """Get structlog processors based on environment."""
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_environment_info,
        censor_sensitive_data,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.environment == "development":
        # Development: colorized console output
        return shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production/Staging: JSON output
        return shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]


def configure_structlog() -> None:
    """Configure structlog for the application."""
    structlog.configure(
        processors=get_processors(),
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def configure_stdlib_logging() -> None:
    """Configure standard library logging to work with structlog."""
    log_level = get_log_level()

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create handler based on environment
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if settings.environment == "development":
        # Development: use structlog's ConsoleRenderer
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        # Production: JSON format for stdlib logs
        handler.setFormatter(
            logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s"}'
            )
        )

    root_logger.addHandler(handler)

    # Configure third-party loggers to be less verbose
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.debug else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)


def configure_logging() -> None:
    """Initialize all logging configuration."""
    configure_stdlib_logging()
    configure_structlog()


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structlog logger instance.

    Args:
        name: Logger name, defaults to caller's module name

    Returns:
        Configured structlog logger

    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", user_id="123", action="login")
    """
    return structlog.get_logger(name)


# Context variable for request-scoped logging
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)


def bind_request_context(request_id: str, user_id: str | None = None) -> None:
    """
    Bind request context for logging.

    This should be called at the start of each request to bind
    context variables that will be included in all log entries.

    Args:
        request_id: Unique request identifier
        user_id: Optional authenticated user ID
    """
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    structlog.contextvars.bind_contextvars(request_id=request_id)
    if user_id:
        structlog.contextvars.bind_contextvars(user_id=user_id)


def clear_request_context() -> None:
    """Clear request context after request completion."""
    request_id_var.set(None)
    user_id_var.set(None)
    structlog.contextvars.clear_contextvars()


class LoggingMiddleware:
    """
    ASGI middleware for request logging and context binding.

    This middleware:
    - Generates unique request IDs
    - Binds request context for structured logging
    - Logs request start/end with timing
    """

    def __init__(self, app: Any) -> None:
        self.app = app
        self.logger = get_logger("http")

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        import time
        import uuid

        # Generate request ID
        request_id = str(uuid.uuid4())[:8]

        # Extract request info
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        client = scope.get("client", ("unknown", 0))
        client_ip = client[0] if client else "unknown"

        # Bind context
        bind_request_context(request_id)

        # Track timing
        start_time = time.perf_counter()

        # Track response status
        response_status = 500

        async def send_wrapper(message: dict) -> None:
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message.get("status", 500)
            await send(message)

        try:
            self.logger.info(
                "Request started",
                method=method,
                path=path,
                client_ip=client_ip,
            )

            await self.app(scope, receive, send_wrapper)

        except Exception as e:
            self.logger.exception(
                "Request failed",
                method=method,
                path=path,
                error=str(e),
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            self.logger.info(
                "Request completed",
                method=method,
                path=path,
                status=response_status,
                duration_ms=round(duration_ms, 2),
            )

            clear_request_context()


# Convenience functions for common log patterns
def log_api_call(
    logger: structlog.stdlib.BoundLogger,
    action: str,
    **kwargs: Any,
) -> None:
    """Log an API call with standard fields."""
    logger.info(
        f"API call: {action}",
        action=action,
        **kwargs,
    )


def log_db_operation(
    logger: structlog.stdlib.BoundLogger,
    operation: str,
    table: str,
    **kwargs: Any,
) -> None:
    """Log a database operation with standard fields."""
    logger.debug(
        f"DB {operation} on {table}",
        db_operation=operation,
        db_table=table,
        **kwargs,
    )


def log_external_service(
    logger: structlog.stdlib.BoundLogger,
    service: str,
    operation: str,
    success: bool,
    duration_ms: float | None = None,
    **kwargs: Any,
) -> None:
    """Log an external service call."""
    level = "info" if success else "warning"
    getattr(logger, level)(
        f"External service: {service}.{operation}",
        external_service=service,
        external_operation=operation,
        success=success,
        duration_ms=duration_ms,
        **kwargs,
    )


def log_security_event(
    logger: structlog.stdlib.BoundLogger,
    event_type: str,
    **kwargs: Any,
) -> None:
    """Log a security-related event."""
    logger.warning(
        f"Security event: {event_type}",
        security_event=event_type,
        **kwargs,
    )


def log_business_metric(
    logger: structlog.stdlib.BoundLogger,
    metric_name: str,
    value: float | int,
    **kwargs: Any,
) -> None:
    """Log a business metric for later aggregation."""
    logger.info(
        f"Metric: {metric_name}",
        metric_name=metric_name,
        metric_value=value,
        **kwargs,
    )
