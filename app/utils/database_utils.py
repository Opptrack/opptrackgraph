from enum import Enum
from typing import Optional, Dict, Any
import uuid
from pydantic import BaseModel, Field
from app.config.config import app_settings


class DatabaseType(Enum):
    SUPABASE = "supabase"
    POSTGRES = "postgres"


class DatabaseConfig(BaseModel):
    type: DatabaseType
    connection_string: str
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


def create_database_config(db_type: DatabaseType) -> DatabaseConfig:
    """Create full database configuration"""
    connection_string = create_connection_string(db_type)

    # Add database-specific options
    options = {
        "echo": True,
        "pool_size": 5,
        "max_overflow": 10,
        "connect_args": {"ssl": "require"},
    }

    if db_type == DatabaseType.SUPABASE:
        options = {
            "future": True,
            "connect_args": {
                "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
            },
        }

    return DatabaseConfig(
        type=db_type, connection_string=connection_string, options=options
    )


def create_connection_string(db_type: DatabaseType) -> str:
    """
    Create database connection string based on database type and environment variables
    """

    if db_type == DatabaseType.SUPABASE:
        return app_settings._supabase_url

    elif db_type == DatabaseType.POSTGRES:
        postgres_url = app_settings._supabase_url
        if not postgres_url:
            raise ValueError("PostgreSQL connection URL is required")
        return postgres_url
