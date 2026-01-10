"""
Trend Detection Services

AI-powered trend monitoring and detection for social media platforms.
"""

from app.services.trends.trend_detector import (
    TrendDetectorService,
    Trend,
    TrendAlert,
    TrendReport,
    TrendCategory,
    TrendVelocity,
)

__all__ = [
    "TrendDetectorService",
    "Trend",
    "TrendAlert",
    "TrendReport",
    "TrendCategory",
    "TrendVelocity",
]
