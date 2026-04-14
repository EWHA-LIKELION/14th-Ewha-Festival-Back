import logging
from utils.redis_client import get_redis_client
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

SEARCH_RANKING_KEY = "ranking:search"
SEARCH_RANKING_SNAPSHOT_KEY = "ranking:search:snapshot"

def record_search(keyword: str) -> None:
    if not keyword or not keyword.strip():
        return
    try:
        get_redis_client().zincrby(SEARCH_RANKING_KEY, 1, keyword.strip())
    except Exception:
        logger.warning("record_search failed", exc_info=True)

def update_snapshot() -> None:
    try:
        r = get_redis_client()
        r.zunionstore(SEARCH_RANKING_SNAPSHOT_KEY, [SEARCH_RANKING_KEY])
        r.set("ranking:search:updated_at", datetime.now(timezone.utc).isoformat()) # 갱신 시각 저장
        logger.info("search snapshot updated")
    except Exception:
        logger.warning("update_snapshot failed", exc_info=True)

def get_popular_searches(top_n: int = 10) -> dict[str, Any]:
    try:
        r = get_redis_client()
        key = (
            SEARCH_RANKING_SNAPSHOT_KEY
            if r.exists(SEARCH_RANKING_SNAPSHOT_KEY)
            else SEARCH_RANKING_KEY
        )
        results = r.zrevrange(key, 0, top_n - 1, withscores=True)
        updated_at = r.get("ranking:search:updated_at")
        return {
            "updated_at": updated_at,
            "results": [
                {"rank": i+1, "keyword": kw, "count": int(score)}
                for i, (kw, score) in enumerate(results)
            ]
        }
    except Exception:
        logger.warning("get_popular_searches failed", exc_info=True)
        return {
            "updated_at": None, 
            "results": []
        }
