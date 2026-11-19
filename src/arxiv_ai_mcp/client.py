from __future__ import annotations

import asyncio
import time

import httpx

from arxiv_ai_mcp.parser import ArxivPaper, normalize_arxiv_id, parse_atom_feed

ARXIV_API_URL = "https://export.arxiv.org/api/query"
USER_AGENT = "arxiv-ai-mcp/0.1.0 (https://github.com/jsrv/arxiv-ai-mcp)"


class ArxivClient:
    """Async arXiv API client with built-in 3-second request pacing."""

    def __init__(self, min_interval_sec: float = 3.0, timeout_sec: float = 20.0) -> None:
        self._min_interval = min_interval_sec
        self._timeout = timeout_sec
        self._lock = asyncio.Lock()
        self._last_request_ts = 0.0

    async def _get(self, params: dict[str, str | int]) -> str:
        async with self._lock:
            elapsed = time.monotonic() - self._last_request_ts
            if self._last_request_ts > 0 and elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)

            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT},
            ) as client:
                response = await client.get(ARXIV_API_URL, params=params)
                self._last_request_ts = time.monotonic()
                response.raise_for_status()
                return response.text

    async def search(
        self,
        query: str,
        category: str = "",
        sort_by: str = "relevance",
        max_results: int = 5,
    ) -> list[ArxivPaper]:
        limit = max(1, min(max_results, 15))
        sort_field = "submittedDate" if sort_by == "submittedDate" else "relevance"

        cleaned_query = query.strip()
        search_expr = f"all:{cleaned_query}" if cleaned_query else "cat:cs.AI"
        if category.strip():
            search_expr = f"cat:{category.strip()} AND ({search_expr})"

        xml_text = await self._get({
            "search_query": search_expr,
            "start": 0,
            "max_results": limit,
            "sortBy": sort_field,
            "sortOrder": "descending",
        })
        return parse_atom_feed(xml_text)

    async def fetch_by_id(self, arxiv_id: str) -> ArxivPaper | None:
        clean_id = normalize_arxiv_id(arxiv_id)
        xml_text = await self._get({"id_list": clean_id})
        papers = parse_atom_feed(xml_text)
        return papers[0] if papers else None
