"""LLM-backed fallback parser for ambiguous finance text."""

from __future__ import annotations

import json
import logging

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.integrations.ollama_client import OllamaClient
from app.schemas.llm import LLMTransactionParse
from app.schemas.parse_create import ParsedResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a financial text extraction engine.
Return only valid JSON.
Do not include markdown, comments, or explanations.
If the amount is unclear, set amount to null and needs_confirmation to true.
If confidence is low, set needs_confirmation to true.
Use transaction_type only from: income, expense, refund.
Use category_hint only when you have a reasonable guess.
""".strip()


class LLMParseService:
    """Converts free-form finance text into structured transaction data."""

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()

    async def parse_text(self, text: str) -> ParsedResult | None:
        """Return a structured fallback parse or None when not reliable."""
        if not settings.ollama_parse_enabled:
            return None

        if not settings.ollama_api_key:
            logger.debug("Skipping Ollama parse because OLLAMA_API_KEY is not configured")
            return None

        try:
            content = await self.client.chat(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=self._build_user_prompt(text),
            )
            payload = self._extract_json_payload(content)
            parsed = LLMTransactionParse.model_validate(payload)
        except (httpx.HTTPError, ValueError, ValidationError, json.JSONDecodeError) as exc:
            logger.warning("LLM parse fallback failed: %s", exc)
            return None

        if parsed.amount is None:
            return None
        if parsed.needs_confirmation:
            return None
        if parsed.confidence < settings.ollama_parse_min_confidence:
            return None

        return ParsedResult(
            amount=parsed.amount,
            description=parsed.description or parsed.merchant or text,
            category_name=parsed.category_hint,
            transaction_type=parsed.transaction_type,
            original_text=text,
        )

    def _build_user_prompt(self, text: str) -> str:
        return (
            "Extract a finance transaction from the text below.\n"
            "Return JSON with keys: "
            "amount, currency_code, transaction_type, description, merchant, "
            "date, category_hint, confidence, needs_confirmation, reason.\n"
            f"Text: {text}"
        )

    def _extract_json_payload(self, content: str) -> dict[str, object]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("LLM response did not contain JSON")

        parsed = json.loads(cleaned[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("LLM response JSON was not an object")
        return parsed

__all__ = ["LLMParseService"]
