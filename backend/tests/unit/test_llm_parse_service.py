"""Unit tests for Ollama-backed parse fallback."""

from decimal import Decimal

from app.core.config import settings
from app.schemas.parse_create import ParsedResult
from app.services.llm_parse_service import LLMParseService


class _FakeClient:
    def __init__(self, content: str) -> None:
        self.content = content

    async def chat(self, *, system_prompt: str, user_prompt: str) -> str:
        assert system_prompt
        assert user_prompt
        return self.content


class TestLLMParseService:
    async def test_parse_text_returns_structured_result_when_confident(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(settings, "ollama_parse_enabled", True)
        monkeypatch.setattr(settings, "ollama_api_key", "test-key")
        monkeypatch.setattr(settings, "ollama_parse_min_confidence", 0.75)

        service = LLMParseService(
            client=_FakeClient(
                """
                {
                  "amount": "430.00",
                  "currency_code": "RUB",
                  "transaction_type": "expense",
                  "description": "кофе и круассан",
                  "merchant": "Surf Coffee",
                  "date": null,
                  "category_hint": "Кофе",
                  "confidence": 0.91,
                  "needs_confirmation": false,
                  "reason": "Detected a purchase and ruble amount"
                }
                """
            )
        )

        result = await service.parse_text("кофе и круассан за четыреста тридцать рублей")

        assert isinstance(result, ParsedResult)
        assert result is not None
        assert result.amount == Decimal("430.00")
        assert result.category_name == "Кофе"
        assert result.transaction_type == "expense"

    async def test_parse_text_returns_none_when_confidence_is_too_low(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(settings, "ollama_parse_enabled", True)
        monkeypatch.setattr(settings, "ollama_api_key", "test-key")
        monkeypatch.setattr(settings, "ollama_parse_min_confidence", 0.75)

        service = LLMParseService(
            client=_FakeClient(
                """
                {
                  "amount": "430.00",
                  "currency_code": "RUB",
                  "transaction_type": "expense",
                  "description": "что-то по еде",
                  "merchant": null,
                  "date": null,
                  "category_hint": null,
                  "confidence": 0.49,
                  "needs_confirmation": false,
                  "reason": "Low certainty"
                }
                """
            )
        )

        result = await service.parse_text("что-то вкусное рублей на четыреста+")

        assert result is None

    async def test_parse_text_returns_none_when_ollama_disabled(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(settings, "ollama_parse_enabled", False)
        monkeypatch.setattr(settings, "ollama_api_key", "test-key")

        service = LLMParseService(
            client=_FakeClient(
                '{"amount":"100.00","transaction_type":"expense","confidence":0.99}'
            )
        )

        result = await service.parse_text("обед без цифр")

        assert result is None
