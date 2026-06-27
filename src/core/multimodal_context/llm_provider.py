"""LLM Provider abstraction — swap Ollama for any compatible backend via config.

Scalability note: For high concurrency, use a connection pool of httpx clients
and implement circuit-breaker logic (tenacity) to gracefully degrade when
the LLM is overloaded.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.logging_config import get_logger

log = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract LLM provider. Implement this to add new backends."""

    @abstractmethod
    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    @abstractmethod
    async def stream_chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Yield text chunks as generated. Implementations without native streaming
        MUST simulate it by chunking the full response."""
        ...

    @abstractmethod
    async def aclose(self) -> None:
        """Release any held resources (HTTP clients, SDK connections, etc.)."""
        ...


class OllamaProvider(LLMProvider):
    """Ollama-compatible provider (works with llama.cpp server too).

    Uses streaming-compatible /api/chat endpoint. Non-streaming for simplicity;
    add SSE streaming by switching to httpx stream context manager.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.llm.base_url).rstrip("/")
        self._model = model or settings.llm.model
        self._timeout = timeout or settings.llm.timeout
        self._default_temp = settings.llm.temperature
        self._default_max_tokens = settings.llm.max_tokens
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": False,
            "options": {
                "temperature": temperature or self._default_temp,
                "num_predict": max_tokens or self._default_max_tokens,
            },
        }
        log.debug("llm_request", model=self._model, turns=len(messages))
        resp = await self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        content: str = data["message"]["content"]
        log.debug("llm_response", tokens=data.get("eval_count", "?"))
        return content

    async def embed(self, text: str) -> list[float]:
        resp = await self._client.post(
            "/api/embeddings", json={"model": self._model, "prompt": text}
        )
        resp.raise_for_status()
        return resp.json()["embedding"]

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    async def stream_chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Simulate streaming by yielding the full Ollama response word by word.
        Native Ollama SSE streaming is left as a future optimisation."""
        full = await self.chat(system_prompt, messages, temperature, max_tokens)
        for word in full.split(" "):
            yield word + " "
            await asyncio.sleep(0.04)

    async def aclose(self) -> None:
        await self._client.aclose()
