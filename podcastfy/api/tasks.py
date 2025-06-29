"""
Celery tasks for asynchronous podcast generation.

This module contains background tasks for processing podcast generation requests.
"""

import os
import uuid
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests

from celery import Celery, Task
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.orm import Session

from .database import get_db_context, DatabaseManager
from .models import PodcastJob, JobStatus
from .storage import StorageManager
from ..client import generate_podcast
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize Celery
celery_app = Celery(
    'podcastfy',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=86400,  # Results expire after 24 hours
)

# Initialize storage manager
storage_manager = StorageManager()


class PodcastGenerationTask(Task):
    """Base task class with error handling and retries."""
    
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60  # seconds
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        job_id = kwargs.get('job_id')
        if job_id:
            with get_db_context() as db:
                job = db.query(PodcastJob).filter_by(id=job_id).first()
                if job:
                    job.status = JobStatus.FAILED
                    job.error_detail = str(exc)
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    
                    # Send webhook notification if configured
                    if job.webhook_url:
                        send_webhook_notification(job)
        
        logger.error(f"Task {task_id} failed: {str(exc)}")
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(base=PodcastGenerationTask, bind=True)
def generate_podcast_task(self, job_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asynchronous task to generate a podcast.
    
    Args:
        job_id: Unique job identifier
        request_data: Podcast generation parameters
        
    Returns:
        Dictionary with job results
    """
    try:
        logger.info(f"Starting podcast generation for job {job_id}")
        
        # Update job status to processing
        with get_db_context() as db:
            job = db.query(PodcastJob).filter_by(id=job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            job.status = JobStatus.PROCESSING
            job.progress = 10.0
            db.commit()
        
        # Extract parameters
        urls = request_data.get('urls', [])
        text = request_data.get('text')
        topic = request_data.get('topic')
        tts_model = request_data.get('tts_model', 'openai')
        is_long_form = request_data.get('is_long_form', False)
        
        # Build conversation config
        conversation_config = {
            'creativity': request_data.get('creativity', 0.7),
            'conversation_style': request_data.get('conversation_style', []),
            'roles_person1': request_data.get('roles_person1'),
            'roles_person2': request_data.get('roles_person2'),
            'dialogue_structure': request_data.get('dialogue_structure', []),
            'podcast_name': request_data.get('podcast_name'),
            'podcast_tagline': request_data.get('podcast_tagline'),
            'output_language': request_data.get('output_language', 'English'),
            'user_instructions': request_data.get('user_instructions', ''),
            'engagement_techniques': request_data.get('engagement_techniques', []),
            'text_to_speech': {
                'default_tts_model': tts_model,
                'default_voices': request_data.get('voices', {})
            }
        }
        
        # Update progress
        update_job_progress(job_id, 20.0, "Starting content generation...")
        
        # Generate podcast
        try:
            result_path = generate_podcast(
                urls=[str(url) for url in urls] if urls else None,
                text=text,
                topic=topic,
                tts_model=tts_model,
                conversation_config=conversation_config,
                longform=is_long_form,
            )
        except Exception as e:
            logger.error(f"Podcast generation failed: {str(e)}")
            raise
        
        # Update progress
        update_job_progress(job_id, 80.0, "Uploading files to storage...")
        
        # Upload to storage
        audio_filename = f"podcasts/{job_id}.mp3"
        audio_url = storage_manager.upload_file(result_path, audio_filename)
        
        # Get transcript path (assuming it's saved with similar name pattern)
        transcript_path = result_path.replace('.mp3', '.txt').replace('/audio/', '/transcripts/')
        transcript_url = None
        if os.path.exists(transcript_path):
            transcript_filename = f"transcripts/{job_id}.txt"
            transcript_url = storage_manager.upload_file(transcript_path, transcript_filename)
        
        # Clean up local files
        try:
            os.remove(result_path)
            if transcript_path and os.path.exists(transcript_path):
                os.remove(transcript_path)
        except Exception as e:
            logger.warning(f"Failed to clean up local files: {str(e)}")
        
        # Update job as completed
        with get_db_context() as db:
            job = db.query(PodcastJob).filter_by(id=job_id).first()
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.audio_path = audio_url
            job.transcript_path = transcript_url
            job.completed_at = datetime.utcnow()
            job.result_data = {
                'audio_url': audio_url,
                'transcript_url': transcript_url,
                'duration': None,  # Could be calculated if needed
                'size_bytes': os.path.getsize(result_path) if os.path.exists(result_path) else None
            }
            db.commit()
            
            # Send webhook notification
            if job.webhook_url:
                send_webhook_notification(job)
        
        logger.info(f"Podcast generation completed for job {job_id}")
        
        return {
            'job_id': job_id,
            'status': 'completed',
            'audio_url': audio_url,
            'transcript_url': transcript_url
        }
        
    except Exception as e:
        logger.error(f"Error in podcast generation task: {str(e)}\n{traceback.format_exc()}")
        
        # Update job status
        with get_db_context() as db:
            job = db.query(PodcastJob).filter_by(id=job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_detail = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        
        # Retry the task
        raise self.retry(exc=e)


def update_job_progress(job_id: str, progress: float, message: Optional[str] = None):
    """Update job progress in database."""
    try:
        with get_db_context() as db:
            job = db.query(PodcastJob).filter_by(id=job_id).first()
            if job:
                job.progress = progress
                if message:
                    job.result_data = job.result_data or {}
                    job.result_data['current_step'] = message
                db.commit()
    except Exception as e:
        logger.error(f"Failed to update job progress: {str(e)}")


def send_webhook_notification(job: PodcastJob):
    """Send webhook notification for job completion."""
    if not job.webhook_url:
        return
    
    try:
        payload = {
            'job_id': str(job.id),
            'status': job.status,
            'audio_url': job.audio_path,
            'transcript_url': job.transcript_path,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error': job.error_detail
        }
        
        response = requests.post(
            job.webhook_url,
            json=payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code >= 400:
            logger.error(f"Webhook notification failed: {response.status_code} - {response.text}")
        else:
            logger.info(f"Webhook notification sent for job {job.id}")
            
    except Exception as e:
        logger.error(f"Failed to send webhook notification: {str(e)}")


@celery_app.task
def cleanup_old_jobs():
    """Periodic task to clean up old jobs and files."""
    try:
        with get_db_context() as db:
            # Find jobs older than 7 days
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            old_jobs = db.query(PodcastJob).filter(
                PodcastJob.created_at < cutoff_date
            ).all()
            
            for job in old_jobs:
                # Delete files from storage
                if job.audio_path:
                    storage_manager.delete_file(job.audio_path)
                if job.transcript_path:
                    storage_manager.delete_file(job.transcript_path)
                
                # Delete job record
                db.delete(job)
            
            db.commit()
            logger.info(f"Cleaned up {len(old_jobs)} old jobs")
            
    except Exception as e:
        logger.error(f"Failed to clean up old jobs: {str(e)}")


# Configure periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'podcastfy.api.tasks.cleanup_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
} 