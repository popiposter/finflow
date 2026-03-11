"""Transaction parsing service for free-form text.

This module provides heuristic parsing for Russian free-form text inputs.
The parser extracts amount and description from phrases like:
- "продукты во вкусвилле 1500 рублей"
- "кофе 300"
- "такси домой 1200 руб"

The parser is designed to be replaceable so an LLM-based parser can be
introduced later without rewriting the endpoint layer.
"""

import re
from decimal import Decimal

from app.models.types import TransactionType
from app.schemas.parse_create import ParsedResult

AMOUNT_PATTERN = re.compile(r"(\d+(?:[.,]\d{2})?)\s*(руб(?:лей)?|₽)?", re.IGNORECASE)
CURRENCY_KEYWORDS = {"руб", "рублей", "руб.", "₽"}
CATEGORY_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("продукты", "Продукты"),
    ("вкусвилл", "Продукты"),
    ("супермаркет", "Продукты"),
    ("кофе", "Кофе"),
    ("кафе", "Кофе"),
    ("обед", "Рестораны"),
    ("ресторан", "Рестораны"),
    ("доставка", "Доставка"),
    ("такси", "Такси"),
    ("метро", "Транспорт"),
    ("бензин", "Транспорт"),
    ("аптека", "Здоровье"),
    ("врач", "Здоровье"),
    ("коммуналка", "Коммунальные услуги"),
    ("интернет", "Коммунальные услуги"),
    ("одежда", "Одежда"),
    ("подарок", "Подарки"),
    ("зарплата", "Доход"),
    ("премия", "Доход"),
    ("возврат", "Возврат"),
)
INCOME_KEYWORDS = {"зарплата", "премия", "доход", "аванс"}
REFUND_KEYWORDS = {"возврат", "кэшбэк", "кешбэк", "refund"}


def extract_amount(text: str) -> Decimal | None:
    """Extract amount from text.

    Looks for patterns like:
    - "1500 рублей"
    - "300 руб"
    - "1200.50"

    Args:
        text: The text to parse.

    Returns:
        Decimal amount if found, None otherwise.
    """
    matches = list(AMOUNT_PATTERN.finditer(text))
    if not matches:
        return None

    currency_matches = [match for match in matches if match.group(2)]
    selected_match = currency_matches[-1] if currency_matches else matches[-1]

    amount_str = selected_match.group(1).replace(",", ".")
    try:
        return Decimal(amount_str)
    except Exception:
        return None


def infer_transaction_type(text: str, category_name: str | None = None) -> TransactionType:
    """Infer transaction type from text and detected category."""
    text_lower = text.lower()

    if category_name == "Доход" or any(keyword in text_lower for keyword in INCOME_KEYWORDS):
        return TransactionType.INCOME
    if category_name == "Возврат" or any(keyword in text_lower for keyword in REFUND_KEYWORDS):
        return TransactionType.REFUND

    return TransactionType.EXPENSE


def extract_category(text: str) -> str | None:
    """Extract category name from text using deterministic keyword mapping.

    Args:
        text: The text to parse.

    Returns:
        Canonical category name if detected, None otherwise.
    """
    text_lower = text.lower()
    for keyword, category_name in CATEGORY_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            return category_name
    return None


def extract_description(text: str) -> str:
    """Extract description from text by removing amount patterns.

    This removes numeric amounts and currency keywords to get the
    core description of the transaction.

    Args:
        text: The original text.

    Returns:
        Cleaned description text.
    """
    result = AMOUNT_PATTERN.sub("", text)
    for kw in CURRENCY_KEYWORDS:
        result = re.sub(rf"\b{re.escape(kw)}\b", "", result, flags=re.IGNORECASE)
    result = " ".join(result.split())
    return result.strip() if result.strip() else text


def parse_text(text: str) -> ParsedResult:
    """Parse free-form text into structured transaction data.

    This is a heuristic parser that extracts:
    - Amount (if present)
    - Description (core text without amount)
    - Category (if detectable from keywords)

    Args:
        text: The free-form text to parse (e.g., from iOS Shortcut).

    Returns:
        ParsedResult with extracted fields.
    """
    amount = extract_amount(text)
    category_name = extract_category(text)
    description = extract_description(text)

    return ParsedResult(
        amount=amount,
        description=description if description else text,
        category_name=category_name,
        transaction_type=infer_transaction_type(text, category_name),
        original_text=text,
    )


__all__ = [
    "parse_text",
    "ParsedResult",
    "extract_amount",
    "extract_category",
    "extract_description",
    "infer_transaction_type",
]
