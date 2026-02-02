"""
API Version Definitions

Defines supported API versions and their metadata.
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from functools import total_ordering
from typing import Optional


class VersionStatus(str, Enum):
    """Version lifecycle status."""
    CURRENT = "current"          # Active, fully supported
    SUPPORTED = "supported"      # Older but still supported
    DEPRECATED = "deprecated"    # Will be removed, warnings issued
    SUNSET = "sunset"            # No longer available


@total_ordering
@dataclass(frozen=True)
class APIVersion:
    """
    Represents an API version with its metadata.

    Attributes:
        major: Major version number
        minor: Minor version number
        status: Current lifecycle status
        deprecated_date: When this version was deprecated (if applicable)
        sunset_date: When this version will be/was removed (if applicable)
        changelog_url: URL to the changelog for this version
    """
    major: int
    minor: int
    status: VersionStatus = VersionStatus.CURRENT
    deprecated_date: Optional[date] = None
    sunset_date: Optional[date] = None
    changelog_url: Optional[str] = None

    @property
    def version_string(self) -> str:
        """Return version as string (e.g., 'v1.0')."""
        return f"v{self.major}.{self.minor}"

    @property
    def is_deprecated(self) -> bool:
        """Check if version is deprecated."""
        return self.status in (VersionStatus.DEPRECATED, VersionStatus.SUNSET)

    @property
    def is_available(self) -> bool:
        """Check if version is still available for use."""
        return self.status != VersionStatus.SUNSET

    def __str__(self) -> str:
        return self.version_string

    def __eq__(self, other) -> bool:
        if isinstance(other, APIVersion):
            return self.major == other.major and self.minor == other.minor
        if isinstance(other, str):
            return self.version_string == other
        return False

    def __lt__(self, other: "APIVersion") -> bool:
        if self.major != other.major:
            return self.major < other.major
        return self.minor < other.minor

    def __hash__(self) -> int:
        return hash((self.major, self.minor))


# Define supported versions
V1_0 = APIVersion(
    major=1,
    minor=0,
    status=VersionStatus.CURRENT,
    changelog_url="/docs/changelog/v1.0",
)

V1_1 = APIVersion(
    major=1,
    minor=1,
    status=VersionStatus.CURRENT,
    changelog_url="/docs/changelog/v1.1",
)

# Current and supported versions
CURRENT_VERSION = V1_1
SUPPORTED_VERSIONS: dict[str, APIVersion] = {
    "v1": V1_1,       # Default for v1 prefix
    "v1.0": V1_0,
    "v1.1": V1_1,
}

# Minimum supported version
MIN_SUPPORTED_VERSION = V1_0


def parse_version(version_string: str) -> Optional[APIVersion]:
    """
    Parse a version string and return the corresponding APIVersion.

    Args:
        version_string: Version string (e.g., 'v1', 'v1.0', '1.1')

    Returns:
        APIVersion if valid and supported, None otherwise.
    """
    # Normalize the version string
    version_string = version_string.strip().lower()

    # Remove 'v' prefix if present
    if version_string.startswith("v"):
        version_string = version_string[1:]

    # Try to match exact version first
    full_version = f"v{version_string}"
    if full_version in SUPPORTED_VERSIONS:
        return SUPPORTED_VERSIONS[full_version]

    # Try to parse as major.minor
    try:
        parts = version_string.split(".")
        if len(parts) == 1:
            # Just major version, use default minor
            major = int(parts[0])
            key = f"v{major}"
            return SUPPORTED_VERSIONS.get(key)
        elif len(parts) == 2:
            major = int(parts[0])
            minor = int(parts[1])
            key = f"v{major}.{minor}"
            return SUPPORTED_VERSIONS.get(key)
    except (ValueError, IndexError):
        pass

    return None


def get_latest_version() -> APIVersion:
    """Get the latest/current API version."""
    return CURRENT_VERSION


def is_version_supported(version: APIVersion) -> bool:
    """Check if a version is still supported."""
    return version.is_available and version >= MIN_SUPPORTED_VERSION
