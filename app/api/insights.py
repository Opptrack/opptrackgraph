from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database_service import get_db
from app.core.handler.insights_handler import InsightsHandler


router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/industries")
async def list_industries(
    limit: int = Query(50, ge=1, le=500), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    sql = text(
        """
        SELECT account_industry,
               COUNT(*) as conversation_count,
               SUM(CASE WHEN is_won THEN 1 ELSE 0 END) AS won_count,
               SUM(CASE WHEN is_won THEN 0 ELSE 1 END) AS not_won_count
        FROM v_conversations_enriched
        WHERE account_industry IS NOT NULL
          AND account_industry <> ''
        GROUP BY account_industry
        ORDER BY conversation_count DESC
        LIMIT :limit
        """
    )

    result = await db.execute(sql, {"limit": limit})
    rows = result.mappings().all()
    return {"industries": [dict(r) for r in rows]}


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
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    handler = InsightsHandler()
    rows = await handler.fetch_industry_rows(db, account_industry, limit)
    if not rows:
        raise HTTPException(
            status_code=404, detail="No conversations found for industry"
        )

    texts = handler.extract_texts(rows)
    import math

    k = max(2, min(8, int(math.sqrt(max(1, len(texts))))))
    labels, _vectors, _centroids = await handler.cluster_texts(texts, k=k)
    response = await handler.generate_cluster_insights(account_industry, rows, labels)
    return {"industry": account_industry, "count": len(rows), "insights": response}
