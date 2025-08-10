from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator, Optional
from functools import lru_cache
import logging
from supabase import create_client, Client
from fastapi import HTTPException, Header, status
from app.utils.database_utils import DatabaseType, create_database_config
from app.config.config import app_settings

Base = declarative_base()

logger = logging.getLogger(__name__)


class DatabaseService:
    _instance: Optional["DatabaseService"] = None

    def __init__(self):
        # Get database configuration for Supabase
        db_config = create_database_config(DatabaseType.SUPABASE)
        logger.info(
            f"Initializing database connection to: {db_config.connection_string}"
        )

        self.engine = create_async_engine(
            db_config.connection_string, **db_config.options
        )
        logger.info("Database engine created successfully")

        self.AsyncSessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Initialize Supabase client
        self.supabase: Client = create_client(
            app_settings.SUPABASE_URL, app_settings.SUPABASE_SERVICE_ROLE_KEY
        )
        logger.info("Supabase client initialized successfully")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def init_db(self):
        """Initialize database with tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def dispose(self):
        """Cleanup database connections"""
        if self.engine:
            await self.engine.dispose()

    @classmethod
    def get_instance(cls) -> "DatabaseService":
        if not cls._instance:
            cls._instance = DatabaseService()
        return cls._instance


# Dependency to get DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db_service = get_database_service()
    async for session in db_service.get_session():
        yield session


@lru_cache()
def get_database_service() -> DatabaseService:
    return DatabaseService.get_instance()


async def supabase_jwt_authenticate(
    authorization: str = Header(..., description="Bearer access token"),
) -> str:
    """
    FastAPI dependency that extracts user_id from a valid Supabase JWT token.
    Raises 401 Unauthorized if invalid.
    """
    db_service = get_database_service()

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )

    token = authorization[len("Bearer ") :].strip()

    try:
        user_response = db_service.supabase.auth.get_user(token)

        if not user_response or not getattr(user_response, "user", None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return user_response.user.id

    except Exception as e:
        # Optionally you can log e here if you want internal monitoring
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
