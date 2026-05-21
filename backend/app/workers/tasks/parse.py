"""File / HTML parsing utilities.

We deliberately keep these as plain functions so they can also be called
directly from tests or a CLI without going through Celery.
"""

from __future__ import annotations

import io
from typing import BinaryIO


def parse_pdf(stream: BinaryIO) -> str:
    from pypdf import PdfReader

    reader = PdfReader(stream)
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(p for p in parts if p.strip())


def parse_docx(stream: BinaryIO) -> str:
    from docx import Document as DocxDocument

    doc = DocxDocument(stream)
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paragraphs)


def parse_text(stream: BinaryIO, encoding: str = "utf-8") -> str:
    data = stream.read()
    if isinstance(data, str):
        return data
    return data.decode(encoding, errors="replace")


def parse_html(html: str) -> tuple[str, str | None]:
    """Return (clean_text, title)."""
    import trafilatura
    from bs4 import BeautifulSoup

    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    )
    title: str | None = None
    try:
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
    except Exception:
        pass
    return (text or "").strip(), title


def parse_bytes_by_filename(filename: str, data: bytes) -> str:
    name = filename.lower()
    buf = io.BytesIO(data)
    if name.endswith(".pdf"):
        return parse_pdf(buf)
    if name.endswith(".docx"):
        return parse_docx(buf)
    if name.endswith((".txt", ".md", ".markdown")):
        return parse_text(buf)
    if name.endswith((".html", ".htm")):
        text, _ = parse_html(data.decode("utf-8", errors="replace"))
        return text
    # Best-effort fallback.
    try:
        return parse_text(io.BytesIO(data))
    except Exception:
        return ""
