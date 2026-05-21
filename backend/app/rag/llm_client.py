"""Pluggable LLM client.

Both implementations expose the same `stream(messages) -> Iterator[str]`
interface. The chat-server doesn't care which one is configured.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from functools import lru_cache

import httpx

from app.core.config import settings
from app.rag.prompts import PromptMessage


class LLMClient:
    def stream(self, messages: list[PromptMessage]) -> Iterator[str]:
        raise NotImplementedError


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def stream(self, messages: list[PromptMessage]) -> Iterator[str]:
        oai_msgs = [{"role": m.role, "content": m.content} for m in messages]
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=oai_msgs,
            stream=True,
        )
        for event in stream:
            if not event.choices:
                continue
            delta = event.choices[0].delta
            if delta and delta.content:
                yield delta.content


class OllamaClient(LLMClient):
    """Streams chat from a local Ollama server."""

    def __init__(self, base_url: str, model: str) -> None:
        self._url = base_url.rstrip("/") + "/api/chat"
        self._model = model

    def stream(self, messages: list[PromptMessage]) -> Iterator[str]:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        with httpx.stream("POST", self._url, json=payload, timeout=None) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = data.get("message") or {}
                chunk = msg.get("content")
                if chunk:
                    yield chunk
                if data.get("done"):
                    break


class GeminiClient(LLMClient):
    """Streams chat from the Google Gemini API."""

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai
        from google.genai import types

        self._types = types
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def stream(self, messages: list[PromptMessage]) -> Iterator[str]:
        system_parts: list[str] = []
        contents = []
        for message in messages:
            if message.role == "system":
                system_parts.append(message.content)
                continue
            role = "model" if message.role == "assistant" else "user"
            contents.append(
                self._types.Content(
                    role=role,
                    parts=[self._types.Part.from_text(text=message.content)],
                )
            )
        config = None
        if system_parts:
            config = self._types.GenerateContentConfig(
                system_instruction="\n\n".join(system_parts)
            )
        stream = self._client.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=config,
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    if settings.llm_provider == "ollama":
        return OllamaClient(settings.ollama_base_url, settings.ollama_chat_model)
    if settings.llm_provider == "gemini":
        return GeminiClient(settings.gemini_api_key, settings.gemini_chat_model)
    return OpenAIClient(settings.openai_api_key, settings.openai_chat_model)
