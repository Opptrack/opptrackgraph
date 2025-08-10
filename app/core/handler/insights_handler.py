from typing import Any, Dict, List, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.services.embedding_service import EmbeddingService
from app.core.tools.clustering import kmeans
from app.services.llm_service import LLMService
from app.schema.llm.message import Message


def _summarize_texts(texts: List[str], max_chars: int = 1200) -> str:
    acc: List[str] = []
    total = 0
    for t in texts:
        t = t.strip()
        if not t:
            continue
        if total + len(t) > max_chars:
            break
        acc.append(t)
        total += len(t)
    s = " ".join(acc)
    if len(s) > max_chars:
        s = s[: max_chars - 3] + "..."
    return s


class InsightsHandler:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.llm = LLMService()

    async def fetch_industry_rows(
        self, db: AsyncSession, industry: str, limit: int
    ) -> List[Dict[str, Any]]:
        sql = text(
            """
            SELECT conversation_id, account_name, is_won,
                   opportunity_stage, transcript
            FROM v_conversations_enriched
            WHERE account_industry = :industry
              AND transcript IS NOT NULL
            ORDER BY external_event_timestamp DESC
            LIMIT :limit
            """
        )
        result = await db.execute(sql, {"industry": industry, "limit": limit})
        return [dict(r) for r in result.mappings().all()]

    @staticmethod
    def extract_texts(rows: List[Dict[str, Any]]) -> List[str]:
        texts: List[str] = []
        for r in rows:
            tr = r.get("transcript")
            if isinstance(tr, dict):
                utterances = tr.get("utterances", [])
            elif isinstance(tr, str):
                try:
                    import json

                    utterances = json.loads(tr).get("utterances", [])
                except Exception:
                    utterances = []
            else:
                utterances = []
            merged = " ".join(str(u.get("text", "")).strip() for u in utterances)
            texts.append(merged)
        return texts

    async def cluster_texts(
        self, texts: List[str], k: int
    ) -> Tuple[List[int], List[List[float]], List[List[float]]]:
        vectors = await self.embedder.embed_texts(texts)
        labels, centroids = kmeans(vectors, k=k)
        return labels, vectors, centroids

    async def generate_cluster_insights(
        self, industry: str, rows: List[Dict[str, Any]], labels: List[int]
    ) -> Dict[str, Any]:
        clusters: Dict[int, List[Dict[str, Any]]] = {}
        for row, label in zip(rows, labels):
            clusters.setdefault(label, []).append(row)

        cluster_summaries: List[str] = []
        for cid, items in clusters.items():
            texts = self.extract_texts(items)
            summary = _summarize_texts(texts)
            won = sum(1 for it in items if bool(it.get("is_won")))
            lost = len(items) - won
            cluster_summaries.append(
                f"cluster={cid} size={len(items)} won={won} lost={lost}\n{summary}"
            )

        system = Message(
            role="system",
            content=(
                "You analyze clusters of sales conversations to extract actionable "
                "insights per cluster and overall. Return STRICT JSON with keys: "
                "clusters (list with {id, size, won, lost, themes, action_items, "
                "competitors, win_reasons, loss_reasons}), and overall (summary, "
                "recommendations)."
            ),
        )
        user = Message(
            role="user",
            content=(
                f"Industry: {industry}\n\n"
                "Each block below describes one cluster. Provide structured insights:\n\n"
                + "\n\n".join(cluster_summaries)
            ),
        )

        resp = await self.llm.query_llm([system, user], json_response=True)
        return resp  # type: ignore
