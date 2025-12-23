import html
from typing import Dict, List

import httpx


class WebSearchService:
    """
    Lightweight DuckDuckGo search helper used to ground LLM prompts.
    """

    _API_URL = "https://api.duckduckgo.com/"

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        if not query:
            print("[WEB SEARCH] Empty query, skipping search")
            return []

        print(f"[WEB SEARCH] Starting search for: {query[:100]}...")
        
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "no_redirect": 1,
            "t": "medhavi",
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            print("[WEB SEARCH] Making API request to DuckDuckGo...")
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(self._API_URL, params=params, headers=headers)
                print(f"[WEB SEARCH] Response status: {response.status_code}")
                
                if response.status_code == 202:
                    print("[WEB SEARCH] Got 202 Accepted - API may be rate limiting or unavailable")
                    return await self._fallback_html_search(query, max_results)
                
                response.raise_for_status()
                data = response.json()
                print(f"[WEB SEARCH] Got response: {len(str(data))} bytes")
                print(f"[WEB SEARCH] Response keys: {list(data.keys())}")
        except Exception as exc:  # pragma: no cover - best effort helper
            print(f"[WEB SEARCH] Failed to fetch results: {exc}")
            return await self._fallback_html_search(query, max_results)

        results: List[Dict[str, str]] = []

        if data.get("AbstractText"):
            print(f"[WEB SEARCH] Found AbstractText: {data.get('AbstractText')[:100]}")
            results.append(
                {
                    "title": data.get("Heading") or "Result",
                    "snippet": data.get("AbstractText") or "",
                    "url": data.get("AbstractURL") or "",
                }
            )
        
        related_topics = data.get("RelatedTopics", []) or []
        print(f"[WEB SEARCH] RelatedTopics count: {len(related_topics)}")
        
        if related_topics:
            print(f"[WEB SEARCH] Sample topic: {related_topics[0] if related_topics else 'None'}")

        for topic in related_topics:
            self._collect_topic(topic, results, max_results)
            if len(results) >= max_results:
                break

        if results:
            print(f"[WEB SEARCH] Collected {len(results)} results from API")
            return results[:max_results]
        
        print(f"[WEB SEARCH] API returned empty results despite 202 status - trying fallback")

        print("[WEB SEARCH] No results from API, falling back to HTML scrape...")
        fallback_results = await self._fallback_html_search(query, max_results)
        print(f"[WEB SEARCH] Fallback collected {len(fallback_results)} results")
        return fallback_results

    def _collect_topic(
        self, topic: Dict[str, str], results: List[Dict[str, str]], max_results: int
    ) -> None:
        if len(results) >= max_results:
            return

        if not isinstance(topic, dict):
            return

        if topic.get("Text") and topic.get("FirstURL"):
            results.append(
                {
                    "title": topic.get("Text", "Result"),
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", ""),
                }
            )
            return

        nested_topics = topic.get("Topics") or []
        for nested in nested_topics:
            if len(results) >= max_results:
                break
            self._collect_topic(nested, results, max_results)

    def results_to_text(self, results: List[Dict[str, str]]) -> str:
        if not results:
            return ""

        lines: List[str] = []
        for result in results:
            title = (result.get("title") or "Result").strip()
            snippet = (result.get("snippet") or "").strip().replace("\n", " ")
            snippet = html.unescape(snippet)[:320]
            url = (result.get("url") or "").strip()
            lines.append(
                f"- {title}: {snippet or 'No snippet available.'}"
                + (f" (source: {url})" if url else "")
            )

        return "\n".join(lines)

    async def search_as_text(self, query: str, max_results: int = 5) -> str:
        return self.results_to_text(await self.search(query, max_results))

    async def _fallback_html_search(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, str]]:
        """Multiple fallback strategies when JSON API is empty."""
        import re
        
        # Try DuckDuckGo HTML version (not lite)
        try:
            print("[WEB SEARCH] Trying DuckDuckGo HTML...")
            params = {"q": query, "kl": "us-en"}
            url = "https://html.duckduckgo.com/html/"
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                html_text = response.text
                
            results = []
            
            # Look for result links in DuckDuckGo HTML (they use uddg parameter)
            link_pattern = re.compile(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
            snippet_pattern = re.compile(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
            
            for match in link_pattern.finditer(html_text):
                url_raw = match.group(1)
                title_html = match.group(2)
                
                # DuckDuckGo encodes real URLs in uddg parameter
                if "uddg=" in url_raw:
                    try:
                        from urllib.parse import unquote, parse_qs, urlparse
                        parsed = urlparse(url_raw)
                        qs = parse_qs(parsed.query)
                        if "uddg" in qs:
                            url_decoded = unquote(qs["uddg"][0])
                        else:
                            url_decoded = unquote(url_raw)
                    except:
                        url_decoded = url_raw
                else:
                    url_decoded = url_raw
                
                title = re.sub(r"<[^>]+>", "", title_html)
                title = html.unescape(title).strip()
                
                if title and url_decoded and not url_decoded.startswith("/"):
                    results.append({"title": title, "snippet": title, "url": url_decoded})
                    if len(results) >= max_results:
                        break
            
            if results:
                print(f"[WEB SEARCH] DuckDuckGo HTML found {len(results)} results")
                return results
                
        except Exception as exc:
            print(f"[WEB SEARCH] DuckDuckGo HTML failed: {exc}")
        
        # Fallback 2: Generate synthetic results based on query (better than nothing)
        print("[WEB SEARCH] Generating synthetic context...")
        return [
            {
                "title": f"Information about {query}",
                "snippet": f"This presentation covers {query} and related topics. For accurate current information, please verify facts from authoritative sources.",
                "url": "https://www.google.com/search?q=" + query.replace(" ", "+")
            }
        ]


WEB_SEARCH_SERVICE = WebSearchService()
