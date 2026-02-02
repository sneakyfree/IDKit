"""
API Dependencies Re-export Module

This module re-exports dependencies from app.api.v1.deps for backward compatibility.
"""

from app.api.v1.deps import (
    get_db,
    get_current_user,
    get_current_user_optional,
    require_admin,
    require_verified,
    get_pagination,
    RateLimitDep,
    security,
)

__all__ = [
    "get_db",
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
    "require_verified",
    "get_pagination",
    "RateLimitDep",
    "security",
]
