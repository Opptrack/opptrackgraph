from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from app.core.handler.insights_handler import InsightsHandler


router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/industries")
async def list_industries(limit: int = Query(50, ge=1, le=500)) -> Dict[str, Any]:
    """Aggregate industry counts via Supabase REST.

    If the REST API doesn’t support aggregation directly, fetch a sample and
    aggregate client-side (bounded by limit). For larger datasets, prefer a
    dedicated RPC or materialized view.
    """
    handler = InsightsHandler()
    # Fetch a larger sample to make aggregation meaningful, cap at 1000
    sample_limit = min(max(limit * 20, 100), 1000)
    try:
        from app.services.database_service import (
            get_database_service,
        )

        db_service = get_database_service()
        tbl = db_service.supabase.table("v_conversations_enriched")
        # not_.is_(...) is not always available; filter with neq and rely on server defaults
        resp = (
            tbl.select("account_industry,is_won")
            .neq("account_industry", "")
            .limit(sample_limit)
            .execute()
        )
        data = getattr(resp, "data", []) or []
        agg: Dict[str, Dict[str, int]] = {}
        for r in data:
            ind = str(r.get("account_industry", "")).strip()
            if not ind:
                continue
            a = agg.setdefault(
                ind,
                {
                    "conversation_count": 0,
                    "won_count": 0,
                    "not_won_count": 0,
                },
            )
            a["conversation_count"] += 1
            if bool(r.get("is_won")):
                a["won_count"] += 1
            else:
                a["not_won_count"] += 1
        # Sort by conversation_count desc and apply limit
        industries: List[Dict[str, Any]] = [
            {
                "account_industry": k,
                **v,
            }
            for k, v in sorted(
                agg.items(),
                key=lambda kv: kv[1]["conversation_count"],
                reverse=True,
            )
        ][: limit]
        return {"industries": industries}
    except Exception as e:
        # Fallback empty
        return {"industries": []}


def _safe_load_transcript(raw: Any) -> Dict[str, Any] | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    # asyncpg may already decode jsonb; if string, try to parse
    try:
        import json

        return json.loads(raw)
    except Exception:
        return None


def _summarize_transcript(transcript: Dict[str, Any], max_chars: int = 1500) -> str:
    utterances: List[Dict[str, Any]] = transcript.get("utterances", [])  # type: ignore
    if not utterances:
        return ""
    texts: List[str] = []
    for u in utterances:
        text_piece = str(u.get("text", "")).strip()
        if text_piece:
            texts.append(text_piece)
        if sum(len(t) for t in texts) > max_chars:
            break
    summary = " ".join(texts)
    if len(summary) > max_chars:
        summary = summary[: max_chars - 3] + "..."
    return summary


@router.get("/industry")
async def industry_insights(
    account_industry: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=500),
) -> Dict[str, Any]:
    handler = InsightsHandler()
    result = await handler.compute_industry_insights(account_industry, limit)
    if not result:
        raise HTTPException(
            status_code=404, detail="No conversations found for industry"
        )
    return result


@router.get("/overall")
async def overall_insights(
    limit: int = Query(50, ge=1, le=500),
) -> Dict[str, Any]:
    handler = InsightsHandler()
    result = await handler.compute_overall_insights(limit)
    if not result:
        raise HTTPException(status_code=404, detail="No conversations found")
    return result
