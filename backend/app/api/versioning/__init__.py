"""
API Versioning Module

Provides version negotiation, deprecation warnings, and version-specific
response transformations for the IDKit API.
"""

from .version import APIVersion, CURRENT_VERSION, SUPPORTED_VERSIONS, V1_0, V1_1
from .negotiator import VersionNegotiator, get_requested_version
from .middleware import VersionMiddleware, get_version_middleware
from .deprecation import DeprecationWarning, add_deprecation_warning
from .transformers import VersionTransformer, register_transformer, versioned_response
from .dependencies import (
    get_api_version,
    require_minimum_version,
    require_exact_version,
    APIVersionDep,
    is_version,
    version_switch,
)

__all__ = [
    # Version definitions
    "APIVersion",
    "CURRENT_VERSION",
    "SUPPORTED_VERSIONS",
    "V1_0",
    "V1_1",
    # Negotiation
    "VersionNegotiator",
    "get_requested_version",
    # Middleware
    "VersionMiddleware",
    "get_version_middleware",
    # Deprecation
    "DeprecationWarning",
    "add_deprecation_warning",
    # Transformers
    "VersionTransformer",
    "register_transformer",
    "versioned_response",
    # Dependencies
    "get_api_version",
    "require_minimum_version",
    "require_exact_version",
    "APIVersionDep",
    "is_version",
    "version_switch",
]
