"""
Production-ready FastAPI application for Podcastfy.

This module provides the main API application with authentication, rate limiting,
background job processing, and comprehensive error handling.
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .auth import AuthMiddleware, verify_api_key, APIKey
from .database import get_db, DatabaseManager
from .models import (
    PodcastGenerationRequest,
    PodcastGenerationResponse,
    JobStatusResponse,
    ErrorResponse,
    HealthCheckResponse,
    PodcastJob,
    JobStatus
)
from .tasks import generate_podcast_task
from .storage import StorageManager
from ..utils.logger import setup_logger
from .auth import redis_client

logger = setup_logger(__name__)

# Initialize Sentry for error tracking (optional)
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        environment=os.getenv("ENVIRONMENT", "production"),
    )

# Create FastAPI app
app = FastAPI(
    title="Podcastfy API",
    description="Production-ready API for AI-powered podcast generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)

# Add middleware
app.add_middleware(AuthMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-*", "X-Quota-*"],
)

# Add Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# Initialize storage manager
storage_manager = StorageManager()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="ValidationError",
            message="Invalid request parameters",
            detail={"errors": errors},
            request_id=getattr(request.state, "request_id", None)
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            request_id=getattr(request.state, "request_id", None)
        ).dict(),
        headers=getattr(exc, "headers", None)
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            request_id=getattr(request.state, "request_id", None)
        ).dict()
    )


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Podcastfy API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring.
    
    Returns service status and dependency health.
    """
    # Check database
    db_healthy = DatabaseManager.health_check()
    
    # Check Redis
    redis_healthy = True
    try:
        redis_client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_healthy = False
    
    # Check storage
    storage_healthy = storage_manager.health_check()
    
    # Overall health
    all_healthy = db_healthy and redis_healthy and storage_healthy
    
    return HealthCheckResponse(
        status="healthy" if all_healthy else "degraded",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services={
            "database": db_healthy,
            "redis": redis_healthy,
            "storage": storage_healthy
        }
    )


@app.post("/api/v1/podcasts", 
         response_model=PodcastGenerationResponse,
         status_code=status.HTTP_202_ACCEPTED,
         summary="Generate a podcast",
         description="Submit a podcast generation request. The podcast will be generated asynchronously.")
async def generate_podcast(
    request: PodcastGenerationRequest,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db),
    request_obj: Request = None
):
    """
    Generate a podcast from URLs, text, or topic.
    
    This endpoint accepts various input sources and queues a background job
    to generate the podcast. Use the returned job_id to check status.
    """
    try:
        # Create job record
        job = PodcastJob(
            id=uuid.uuid4(),
            status=JobStatus.PENDING,
            request_data=request.dict(),
            created_by=api_key.name,
            webhook_url=str(request.webhook_url) if request.webhook_url else None
        )
        db.add(job)
        db.commit()
        
        # Queue background task
        generate_podcast_task.delay(
            job_id=str(job.id),
            request_data=request.dict()
        )
        
        logger.info(f"Queued podcast generation job {job.id} for API key {api_key.name}")
        
        return PodcastGenerationResponse(
            job_id=str(job.id),
            status=job.status,
            message="Podcast generation job queued successfully",
            created_at=job.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to queue podcast generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to queue podcast generation"
        )


@app.get("/api/v1/podcasts/{job_id}",
         response_model=JobStatusResponse,
         summary="Get job status",
         description="Check the status of a podcast generation job.")
async def get_job_status(
    job_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get the status of a podcast generation job.
    
    Returns the current status, progress, and results (if completed).
    """
    # Validate UUID format
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID format"
        )
    
    # Get job from database
    job = db.query(PodcastJob).filter_by(id=job_uuid).first()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    # Check if user has access to this job
    if job.created_by != api_key.name and api_key.name != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access denied to this job"
        )
    
    # Build response
    response = JobStatusResponse(
        job_id=str(job.id),
        status=job.status,
        progress=job.progress or 0.0,
        message=f"Job is {job.status}",
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        audio_url=job.audio_path,
        transcript_url=job.transcript_path,
        error_detail=job.error_detail,
        metadata=job.result_data
    )
    
    return response


@app.delete("/api/v1/podcasts/{job_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Cancel a job",
            description="Cancel a pending or running podcast generation job.")
async def cancel_job(
    job_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Cancel a podcast generation job.
    
    Only pending or processing jobs can be cancelled.
    """
    # Validate UUID format
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID format"
        )
    
    # Get job from database
    job = db.query(PodcastJob).filter_by(id=job_uuid).first()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    # Check if user has access to this job
    if job.created_by != api_key.name and api_key.name != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access denied to this job"
        )
    
    # Check if job can be cancelled
    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    # Update job status
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.utcnow()
    db.commit()
    
    # TODO: Actually cancel the Celery task
    
    logger.info(f"Cancelled job {job_id}")
    
    return None


@app.get("/api/v1/podcasts",
         response_model=Dict[str, Any],
         summary="List jobs",
         description="List podcast generation jobs for the authenticated user.")
async def list_jobs(
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
    status: Optional[JobStatus] = None
):
    """
    List podcast generation jobs.
    
    Returns a paginated list of jobs created by the authenticated API key.
    """
    # Build query
    query = db.query(PodcastJob)
    
    # Filter by creator (unless admin)
    if api_key.name != "admin":
        query = query.filter_by(created_by=api_key.name)
    
    # Filter by status if provided
    if status:
        query = query.filter_by(status=status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    jobs = query.order_by(PodcastJob.created_at.desc()).limit(limit).offset(offset).all()
    
    # Build response
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "jobs": [
            {
                "job_id": str(job.id),
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "audio_url": job.audio_path,
                "transcript_url": job.transcript_path
            }
            for job in jobs
        ]
    }


@app.get("/api/v1/stats",
         response_model=Dict[str, Any],
         summary="Get usage statistics",
         description="Get usage statistics for the authenticated API key.")
async def get_stats(
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for the authenticated API key.
    
    Returns daily usage, total jobs, and other metrics.
    """
    # Get usage from rate limiter
    from .auth import rate_limiter
    daily_usage = rate_limiter.get_daily_usage(api_key.key)
    
    # Get job statistics
    query = db.query(PodcastJob)
    if api_key.name != "admin":
        query = query.filter_by(created_by=api_key.name)
    
    total_jobs = query.count()
    completed_jobs = query.filter_by(status=JobStatus.COMPLETED).count()
    failed_jobs = query.filter_by(status=JobStatus.FAILED).count()
    
    return {
        "api_key": api_key.name,
        "daily_usage": daily_usage,
        "daily_quota": api_key.quota_daily,
        "rate_limit": api_key.rate_limit,
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "success_rate": round(completed_jobs / total_jobs * 100, 2) if total_jobs > 0 else 0
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 4))
    
    uvicorn.run(
        "podcastfy.api.app:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    ) 