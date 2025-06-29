"""
Data models for the Podcastfy API.

This module contains Pydantic models for request/response validation
and SQLAlchemy models for database operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator, HttpUrl
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class JobStatus(str, Enum):
    """Enumeration of job statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TTSModel(str, Enum):
    """Available TTS models."""
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    EDGE = "edge"
    GEMINI = "gemini"
    GEMINIMULTI = "geminimulti"


class PodcastGenerationRequest(BaseModel):
    """Request model for podcast generation."""
    urls: Optional[List[HttpUrl]] = Field(None, description="List of URLs to process")
    text: Optional[str] = Field(None, description="Raw text input to process")
    topic: Optional[str] = Field(None, description="Topic to generate podcast about")
    tts_model: TTSModel = Field(TTSModel.OPENAI, description="TTS model to use")
    voices: Optional[Dict[str, str]] = Field(None, description="Voice configuration")
    creativity: float = Field(0.7, ge=0.0, le=1.0, description="Creativity level")
    conversation_style: Optional[List[str]] = Field(None, description="Conversation style")
    roles_person1: Optional[str] = Field(None, description="Role for person 1")
    roles_person2: Optional[str] = Field(None, description="Role for person 2")
    dialogue_structure: Optional[List[str]] = Field(None, description="Dialogue structure")
    podcast_name: Optional[str] = Field(None, description="Podcast name")
    podcast_tagline: Optional[str] = Field(None, description="Podcast tagline")
    output_language: str = Field("English", description="Output language")
    user_instructions: Optional[str] = Field(None, description="Additional instructions")
    engagement_techniques: Optional[List[str]] = Field(None, description="Engagement techniques")
    is_long_form: bool = Field(False, description="Generate long-form content")
    webhook_url: Optional[HttpUrl] = Field(None, description="Webhook URL for completion notification")
    
    @validator('urls', 'text', 'topic')
    def validate_input(cls, v, values):
        """Ensure at least one input is provided."""
        if not any([values.get('urls'), values.get('text'), values.get('topic'), v]):
            raise ValueError("At least one of 'urls', 'text', or 'topic' must be provided")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "urls": ["https://example.com/article"],
                "tts_model": "openai",
                "creativity": 0.7,
                "output_language": "English",
                "is_long_form": False
            }
        }


class PodcastGenerationResponse(BaseModel):
    """Response model for podcast generation."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="Job creation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "message": "Podcast generation job queued successfully",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class JobStatusResponse(BaseModel):
    """Response model for job status queries."""
    job_id: str
    status: JobStatus
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage")
    message: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    audio_url: Optional[str] = None
    transcript_url: Optional[str] = None
    error_detail: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "progress": 100.0,
                "message": "Podcast generated successfully",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:05:00Z",
                "completed_at": "2024-01-01T00:05:00Z",
                "audio_url": "https://storage.example.com/podcasts/550e8400.mp3",
                "transcript_url": "https://storage.example.com/transcripts/550e8400.txt"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid request parameters",
                "detail": {"field": "urls", "error": "At least one URL must be provided"},
                "request_id": "req_123456"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current timestamp")
    services: Dict[str, bool] = Field(..., description="Service dependencies status")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-01T00:00:00Z",
                "services": {
                    "database": True,
                    "redis": True,
                    "storage": True
                }
            }
        }


# SQLAlchemy Models
class PodcastJob(Base):
    """Database model for podcast generation jobs."""
    __tablename__ = "podcast_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, default=JobStatus.PENDING)
    progress = Column(Float, default=0.0)
    request_data = Column(JSON, nullable=False)
    result_data = Column(JSON)
    error_detail = Column(Text)
    audio_path = Column(String(500))
    transcript_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    created_by = Column(String(100))  # API key identifier
    webhook_url = Column(String(500))
    retry_count = Column(Integer, default=0)
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "audio_path": self.audio_path,
            "transcript_path": self.transcript_path,
            "error_detail": self.error_detail,
        } 