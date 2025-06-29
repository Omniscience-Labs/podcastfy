"""
Database configuration and connection management.

This module handles database connections, session management, and migrations.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://podcastfy:podcastfy@localhost:5432/podcastfy"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_context() as db:
            # Use db session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


class DatabaseManager:
    """Manage database operations and health checks."""
    
    @staticmethod
    def create_tables():
        """Create all tables in the database."""
        try:
            from .models import Base
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise
    
    @staticmethod
    def drop_tables():
        """Drop all tables in the database."""
        try:
            from .models import Base
            Base.metadata.drop_all(bind=engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {str(e)}")
            raise
    
    @staticmethod
    def health_check() -> bool:
        """
        Check database connectivity.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    @staticmethod
    def get_pool_status() -> dict:
        """
        Get connection pool status.
        
        Returns:
            Dictionary with pool statistics
        """
        pool = engine.pool
        return {
            "size": pool.size() if hasattr(pool, 'size') else 0,
            "checked_in": pool.checkedin() if hasattr(pool, 'checkedin') else 0,
            "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else 0,
            "overflow": pool.overflow() if hasattr(pool, 'overflow') else 0,
            "total": pool.total() if hasattr(pool, 'total') else 0
        }


# Connection event listeners for debugging and monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log new database connections."""
    logger.debug("New database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkouts from pool."""
    logger.debug("Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection returns to pool."""
    logger.debug("Connection returned to pool")


# Initialize database on module import
def init_db():
    """Initialize database schema."""
    try:
        DatabaseManager.create_tables()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        # Don't raise here - let the app start even if DB is down
        # Health checks will catch this


# Run initialization
if os.getenv("AUTO_INIT_DB", "true").lower() == "true":
    init_db() 