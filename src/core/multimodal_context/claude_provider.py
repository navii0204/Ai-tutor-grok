"""ClaudeProvider — Anthropic Claude backend for BrainEcosystem.

Architect lesson: The LLMProvider ABC absorbs this entire integration.
Zero changes needed in DialogueManager, SocraticGuard, or any service layer.
Swap LLM_PROVIDER=claude in .env and the whole Socratic pipeline upgrades.
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import AsyncIterator, Any

import anthropic
from anthropic import AsyncAnthropic, AuthenticationError, APIError
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.logging_config import get_logger
from .llm_provider import LLMProvider

log = get_logger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-6"


class ClaudeProvider(LLMProvider):
    """Anthropic Claude backend. Implements the LLMProvider ABC."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        resolved_key = api_key or settings.llm.api_key
        if not resolved_key:
            raise ValueError(
                "Claude API key is required. "
                "Set LLM_API_KEY=sk-ant-... in your .env file. "
                "Get a key at https://console.anthropic.com/"
            )
        self._model = model or settings.llm.model or _DEFAULT_MODEL
        self._default_max_tokens = settings.llm.max_tokens
        self._default_temp = settings.llm.temperature
        self._client = AsyncAnthropic(api_key=resolved_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        log.debug("claude_request", model=self._model, turns=len(messages))
        response = await self._client.messages.create(
            model=self._model,
            system=system_prompt,
            messages=messages,  # already in {"role", "content"} form — no transform needed
            max_tokens=max_tokens or self._default_max_tokens,
            temperature=temperature or self._default_temp,
        )
        content: str = response.content[0].text
        log.debug(
            "claude_response",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return content

    async def stream_chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Native Claude streaming — yields text chunks as Claude produces them."""
        async with self._client.messages.stream(
            model=self._model,
            system=system_prompt,
            messages=messages,
            max_tokens=max_tokens or self._default_max_tokens,
            temperature=temperature or self._default_temp,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def embed(self, text: str) -> list[float]:
        # Anthropic has no embeddings API. Reuse the deterministic MD5 hash stub
        # from MockLLMProvider — embeddings are not on the critical Socratic path.
        h = hashlib.md5(text.encode()).digest()
        return [b / 255.0 for b in h[:8]] + [0.0] * 760

    async def health_check(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except (AuthenticationError, APIError, Exception):
            return False

    async def aclose(self) -> None:
        await self._client.close()
