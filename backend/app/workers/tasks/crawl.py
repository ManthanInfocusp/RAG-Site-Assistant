"""Same-domain BFS crawler with sitemap support and retry.

Strategy:
1. Parse sitemap.xml (from robots.txt directives or well-known path) to seed the queue.
2. BFS crawl with httpx (fast, no JS), retrying transient errors with backoff.
3. If a page has very little textual content, retry once with Playwright headless.
4. Respect robots.txt for the seed host.
5. Cap by `max_pages` and `max_depth`.
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import dataclass
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import get_logger
from app.workers.tasks.parse import parse_html

log = get_logger("crawler")

_FETCH_TIMEOUT = settings.crawl_timeout_seconds
_RETRY_DELAYS = (1, 3)  # seconds between attempts (2 retries total)


@dataclass
class CrawledPage:
    url: str
    title: str | None
    text: str


def _same_host(seed: str, candidate: str) -> bool:
    return urlparse(seed).netloc.lower() == urlparse(candidate).netloc.lower()


def _normalise(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/")


def _extract_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        if not absolute.startswith(("http://", "https://")):
            continue
        out.append(_normalise(absolute))
    return out


def _load_robots(seed: str) -> RobotFileParser:
    rp = RobotFileParser()
    parsed = urlparse(seed)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        rp.set_url(robots_url)
        rp.read()
    except Exception:
        rp.parse([])
    return rp


def _fetch_robots_sitemaps(seed: str) -> list[str]:
    """Read Sitemap: directives from robots.txt."""
    parsed = urlparse(seed)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    sitemaps: list[str] = []
    try:
        with httpx.Client(timeout=10, follow_redirects=True, headers={"User-Agent": settings.crawl_user_agent}) as c:
            r = c.get(robots_url)
            if r.status_code < 400:
                for line in r.text.splitlines():
                    if line.lower().startswith("sitemap:"):
                        url = line.split(":", 1)[1].strip()
                        sitemaps.append(url)
    except Exception:
        pass
    return sitemaps


def _parse_sitemap(
    sitemap_url: str,
    seed: str,
    robots: RobotFileParser,
    out: list[str],
    visited: set[str],
    depth: int = 0,
) -> None:
    if depth > 3 or sitemap_url in visited:
        return
    visited.add(sitemap_url)
    try:
        with httpx.Client(timeout=10, follow_redirects=True, headers={"User-Agent": settings.crawl_user_agent}) as c:
            r = c.get(sitemap_url)
            if r.status_code >= 400:
                return
        root = ET.fromstring(r.text)
        ns = (root.tag.split("}")[0] + "}") if "}" in root.tag else ""
        # Sitemap index — recurse into child sitemaps
        for child in root.findall(f"{ns}sitemap"):
            loc = child.find(f"{ns}loc")
            if loc is not None and loc.text:
                _parse_sitemap(loc.text.strip(), seed, robots, out, visited, depth + 1)
        # Regular sitemap — collect URLs
        for url_el in root.findall(f"{ns}url"):
            loc = url_el.find(f"{ns}loc")
            if loc is not None and loc.text:
                u = _normalise(loc.text.strip())
                if _same_host(seed, u) and robots.can_fetch(settings.crawl_user_agent, u):
                    out.append(u)
    except Exception as exc:
        log.debug("sitemap.parse_failed", url=sitemap_url, error=str(exc))


def _fetch_sitemap_urls(seed: str, robots: RobotFileParser) -> list[str]:
    """Return deduplicated same-host URLs discovered via sitemaps."""
    parsed = urlparse(seed)
    candidates = _fetch_robots_sitemaps(seed)
    if not candidates:
        candidates = [
            f"{parsed.scheme}://{parsed.netloc}/sitemap.xml",
            f"{parsed.scheme}://{parsed.netloc}/sitemap_index.xml",
        ]
    urls: list[str] = []
    visited_sitemaps: set[str] = set()
    for candidate in candidates:
        _parse_sitemap(candidate, seed, robots, urls, visited_sitemaps)
    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    log.info("sitemap.found", seed=seed, count=len(deduped))
    return deduped


def _fetch_static(url: str) -> str | None:
    last_exc: Exception | None = None
    for attempt, delay in enumerate((*_RETRY_DELAYS, None)):
        try:
            with httpx.Client(
                timeout=_FETCH_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": settings.crawl_user_agent},
            ) as client:
                resp = client.get(url)
                if resp.status_code >= 500 and delay is not None:
                    time.sleep(delay)
                    continue
                if resp.status_code >= 400:
                    return None
                ctype = resp.headers.get("content-type", "")
                if "html" not in ctype.lower():
                    return None
                return resp.text
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            last_exc = exc
            if delay is not None:
                time.sleep(delay)
    log.warning("crawl.fetch_failed", url=url, error=str(last_exc))
    return None


def _fetch_dynamic(url: str) -> str | None:
    """Playwright fallback for JS-rendered pages. Loaded lazily."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                ctx = browser.new_context(user_agent=settings.crawl_user_agent)
                page = ctx.new_page()
                page.goto(url, wait_until="networkidle", timeout=_FETCH_TIMEOUT * 1000)
                html = page.content()
                return html
            finally:
                browser.close()
    except Exception as exc:  # noqa: BLE001
        log.warning("crawl.dynamic_failed", url=url, error=str(exc))
        return None


def crawl_site(
    seed_url: str,
    *,
    max_pages: int | None = None,
    max_depth: int | None = None,
) -> list[CrawledPage]:
    max_pages = max_pages or settings.crawl_max_pages
    max_depth = max_depth or settings.crawl_max_depth
    seed_url = _normalise(seed_url)
    robots = _load_robots(seed_url)

    visited: set[str] = set()
    pages: list[CrawledPage] = []

    # Seed queue: sitemap URLs first (depth=0), then the seed URL itself.
    sitemap_urls = _fetch_sitemap_urls(seed_url, robots)
    initial = list(dict.fromkeys([seed_url, *sitemap_urls]))  # seed first, then sitemap
    queue: deque[tuple[str, int]] = deque((u, 0) for u in initial)

    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        if not robots.can_fetch(settings.crawl_user_agent, url):
            log.info("crawl.robots_blocked", url=url)
            continue

        html = _fetch_static(url)
        if not html:
            continue

        text, title = parse_html(html)
        if len(text) < 200:
            dyn = _fetch_dynamic(url)
            if dyn:
                text, title = parse_html(dyn)
                html = dyn

        if text:
            pages.append(CrawledPage(url=url, title=title, text=text))
            log.info("crawl.page", url=url, chars=len(text), depth=depth)

        if depth < max_depth:
            for link in _extract_links(url, html):
                if link in visited or not _same_host(seed_url, link):
                    continue
                queue.append((link, depth + 1))

    return pages
