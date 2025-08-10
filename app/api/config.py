from typing import Any, Dict

import re
from fastapi import APIRouter

from app.config.config import app_settings


router = APIRouter(prefix="/config", tags=["config"])


def _present(value: Any) -> bool:
    return value is not None and value != ""


def _mask(text: str) -> str:
    # Hide :password@ in URLs and full API keys
    masked = re.sub(r":[^:@]+@", ":****@", text)
    if len(masked) > 12:
        return masked[:6] + "****" + masked[-4:]
    return "****"


@router.get("/check")
async def check_config() -> Dict[str, Any]:
    # Core groups
    llm = {
        "api_base_url": _present(app_settings.LLM_API_BASE_URL),
        "model_name": _present(app_settings.LLM_MODEL_NAME),
        "api_key": _present(app_settings.LLM_API_KEY),
    }

    embedding = {
        "api_base_url": _present(app_settings.EMBEDDING_API_BASE_URL),
        "model_name": _present(app_settings.EMBEDDING_MODEL_NAME),
        "api_key": _present(app_settings.EMBEDDING_API_KEY),
    }

    supabase = {
        "url": _present(app_settings.SUPABASE_URL),
        "service_role_key": _present(app_settings.SUPABASE_SERVICE_ROLE_KEY),
        "host": _present(app_settings.SUPABASE_HOST),
        "password": _present(app_settings.SUPABASE_PASSWORD),
    }

    postgres = {
        "db_name": _present(app_settings.POSTGRES_DB_NAME),
        "user": _present(app_settings.POSTGRES_DB_USER),
        "password": _present(app_settings.POSTGRES_DB_PASSWORD),
        "host": _present(app_settings.POSTGRES_DB_HOST),
        "port": _present(app_settings.POSTGRES_DB_PORT),
    }

    # Masked connection strings if computable
    urls = {}
    try:
        supa_url = getattr(app_settings, "_supabase_url", None)
        if isinstance(supa_url, str) and supa_url:
            urls["supabase"] = _mask(supa_url)
    except Exception:
        pass

    try:
        db_url = getattr(app_settings, "_database_url", None)
        if isinstance(db_url, str) and db_url:
            urls["postgres"] = _mask(db_url)
    except Exception:
        pass

    return {
        "llm": llm,
        "embedding": embedding,
        "supabase": supabase,
        "postgres": postgres,
        "urls": urls,
        "log_level": app_settings.LOG_LEVEL,
    }
