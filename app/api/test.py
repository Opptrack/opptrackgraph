from typing import Any, Dict

from fastapi import APIRouter, Query

from app.services.database_service import get_database_service
from app.core.logger import logger

router = APIRouter(prefix="/test", tags=["test"])


@router.get("")
async def placeholder():
    return {"status": "ok"}


@router.get("/supabase")
async def supabase_probe(
    table: str = Query("v_conversations_enriched"),
) -> Dict[str, Any]:
    """Probe Supabase via API key by selecting 1 row from a table/view.

    Returns minimal info to verify connectivity without exposing data.
    """
    db_service = get_database_service()
    try:
        # Using Supabase PostgREST (HTTP) rather than direct DB connection
        resp = db_service.supabase.table(table).select("*").limit(1).execute()
        count = len(getattr(resp, "data", []) or [])
        logger.info(
            "Supabase probe ok for table '%s' (rows fetched: %s)", table, count
        )
        return {"ok": True, "table": table, "rows": count}
    except Exception as e:
        logger.error("Supabase probe failed for table '%s': %s", table, str(e))
        return {"ok": False, "table": table, "error": str(e)}
