"""
GDPR & Data Privacy Service

Handles user data export, deletion, and privacy compliance.
"""

from app.services.gdpr.service import GDPRService, gdpr_service

__all__ = ["GDPRService", "gdpr_service"]
