"""
IDKit Celery Workers

Background task processing for:
- Content generation
- Video/audio processing
- Social media publishing
- Email/SMS campaigns
- Analytics processing
- Scheduled tasks
"""

from app.workers.celery_app import celery_app

__all__ = ["celery_app"]
