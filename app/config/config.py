from pydantic_settings import BaseSettings
from pydantic import computed_field


class AppSettings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LLM_API_BASE_URL: str | None = None
    LLM_MODEL_NAME: str | None = None
    EMBEDDING_API_BASE_URL: str | None = None
    EMBEDDING_MODEL_NAME: str | None = None
    LLM_API_KEY: str | None = None
    EMBEDDING_API_KEY: str | None = None
    GEMINI_MODEL_NAME: str | None = None
    GEMINI_API_KEY: str | None = None
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_PASSWORD: str | None = None
    SUPABASE_HOST: str | None = None
    RESEND_API_KEY: str | None = None
    # Database config
    POSTGRES_DB_NAME: str | None = None
    POSTGRES_DB_USER: str | None = None
    POSTGRES_DB_PASSWORD: str | None = None
    POSTGRES_DB_HOST: str | None = None
    POSTGRES_DB_PORT: str | None = None
    # Removed Sentry for generic template

    class ConfigDict:
        env_prefix = ""
        case_sensitive = True

    @computed_field
    def _database_url(self) -> str:
        user = self.POSTGRES_DB_USER
        pwd = self.POSTGRES_DB_PASSWORD
        host = self.POSTGRES_DB_HOST
        port = self.POSTGRES_DB_PORT
        name = self.POSTGRES_DB_NAME
        return (
            "postgresql+asyncpg://"
            f"{user}:{pwd}@{host}:{port}/{name}"
        )

    @computed_field
    def _supabase_url(self) -> str:
        user = self.POSTGRES_DB_USER
        pwd = self.SUPABASE_PASSWORD
        host = self.SUPABASE_HOST
        port = self.POSTGRES_DB_PORT
        name = self.POSTGRES_DB_NAME

        # Fallback: derive host from SUPABASE_URL if SUPABASE_HOST not set
        if not host and isinstance(self.SUPABASE_URL, str):
            try:
                # Expect https://<ref>.supabase.co
                import re

                m = re.match(r"https?://([^.]+)\.supabase\.co", self.SUPABASE_URL)
                if m:
                    ref = m.group(1)
                    host = f"db.{ref}.supabase.co"
            except Exception:
                pass

        return (
            "postgresql+asyncpg://"
            f"{user}:{pwd}@{host}:{port}/{name}"
        )


app_settings = AppSettings()
