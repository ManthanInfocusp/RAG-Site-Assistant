"""Same-domain BFS crawler.

Strategy:
1. Try fetching with `httpx` (fast, no JS).
2. If the page has very little textual content, retry with Playwright headless.
3. Respect robots.txt for the seed host.
4. Cap by `max_pages` and `max_depth`.
"""

from __future__ import annotations

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
        # If robots.txt is unreachable, fall back to permissive behaviour.
        rp.parse([])
    return rp


def _fetch_static(url: str) -> str | None:
    try:
        with httpx.Client(
            timeout=settings.crawl_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": settings.crawl_user_agent},
        ) as client:
            resp = client.get(url)
            if resp.status_code >= 400:
                return None
            ctype = resp.headers.get("content-type", "")
            if "html" not in ctype.lower():
                return None
            return resp.text
    except Exception as exc:  # noqa: BLE001
        log.warning("crawl.fetch_failed", url=url, error=str(exc))
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
                page.goto(url, wait_until="networkidle", timeout=settings.crawl_timeout_seconds * 1000)
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
    queue: deque[tuple[str, int]] = deque([(seed_url, 0)])

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
            # Likely JS-rendered. Retry with Playwright.
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
