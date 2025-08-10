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
    NLTK_DATA_PATH: str | None = None
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
        return f"postgresql+asyncpg://{self.POSTGRES_DB_USER}:{self.POSTGRES_DB_PASSWORD}@{self.POSTGRES_DB_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB_NAME}"

    @computed_field
    def _supabase_url(self) -> str:
        # HOSTNAME = self.SUPABASE_URL.replace("https://", "").split(".")[0].strip()
        return f"postgresql+asyncpg://{self.POSTGRES_DB_USER}:{self.SUPABASE_PASSWORD}@{self.SUPABASE_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB_NAME}"


app_settings = AppSettings()
