"""
Podcastfy API Module

Production-ready API for AI-powered podcast generation.
"""

__version__ = "1.0.0"

from .app import app
from .models import (
    PodcastGenerationRequest,
    PodcastGenerationResponse,
    JobStatusResponse,
    ErrorResponse,
    HealthCheckResponse,
    JobStatus,
    TTSModel
)
from .auth import APIKey, verify_api_key
from .database import get_db, DatabaseManager
from .storage import StorageManager
from .tasks import generate_podcast_task, celery_app

__all__ = [
    "app",
    "PodcastGenerationRequest",
    "PodcastGenerationResponse", 
    "JobStatusResponse",
    "ErrorResponse",
    "HealthCheckResponse",
    "JobStatus",
    "TTSModel",
    "APIKey",
    "verify_api_key",
    "get_db",
    "DatabaseManager",
    "StorageManager",
    "generate_podcast_task",
    "celery_app",
    "__version__"
] 