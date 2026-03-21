"""SearXNG 웹 검색 모듈 - RAG 보완용 외부 검색."""

import logging
import hashlib

import httpx
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# 시간에 민감한 키워드 목록
TIME_SENSITIVE_KEYWORDS = [
    '최근', '2025', '2026', '트렌드', '동향',
    'latest', 'recent', 'news', '최신', '업데이트',
]

CACHE_TTL = 60 * 30  # 30분


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """SearXNG JSON API를 통해 웹 검색 수행.

    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수

    Returns:
        [{'title': str, 'url': str, 'snippet': str}, ...]
    """
    # 캐시 키 생성
    cache_key = f"web_search:{hashlib.md5(query.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    searxng_url = getattr(settings, 'SEARXNG_URL', 'http://blog-jun-searxng:8080')
    search_endpoint = f"{searxng_url}/search"

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                search_endpoint,
                params={
                    'q': query,
                    'format': 'json',
                    'language': 'auto',
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("SearXNG 검색 실패: %s", e)
        return []

    results = []
    for item in data.get('results', [])[:max_results]:
        results.append({
            'title': item.get('title', ''),
            'url': item.get('url', ''),
            'snippet': item.get('content', ''),
        })

    # 캐시에 저장
    cache.set(cache_key, results, CACHE_TTL)
    return results


def should_search_web(query: str, blog_count: int) -> bool:
    """웹 검색이 필요한지 판단.

    블로그 검색 결과가 부족하거나 시간에 민감한 쿼리일 때 True 반환.

    Args:
        query: 사용자 질문
        blog_count: 블로그 검색 결과 수

    Returns:
        웹 검색 필요 여부
    """
    if blog_count < 2:
        return True

    query_lower = query.lower()
    return any(keyword in query_lower for keyword in TIME_SENSITIVE_KEYWORDS)
