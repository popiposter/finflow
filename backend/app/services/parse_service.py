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

from app.schemas.parse_create import ParsedResult

# Regex patterns for amount extraction
# Matches numbers optionally followed by decimals
AMOUNT_PATTERN = re.compile(r"(\d+(?:[.,]\d{2})?)\s*(руб(?:лей)?|₽)?", re.IGNORECASE)

# Currency keywords
CURRENCY_KEYWORDS = {"руб", "рублей", "руб.", "₽"}

# Common words that might indicate category or payee but not amount
CATEGORY_INDICATORS = {
    "продукты",
    "продукт",
    "супермаркет",
    "супер",
    "вкусвилл",
    "фрукты",
    "овощи",
    "мясо",
    "рыба",
    "молоко",
    "хлеб",
    "кондитер",
    "кондитерская",
    "пекарня",
    "кофе",
    "кафе",
    "ресторан",
    "обед",
    "ужин",
    "завтрак",
    "доставка",
    "спецпредложение",
    "каршеринг",
    "такси",
    "метро",
    "автобус",
    "трамвай",
    "троллейбус",
    "бензин",
    "АЗС",
    "машина",
    "ремонт",
    "авто",
    "товары",
    " техника",
    "электроника",
    "телефон",
    "телефоны",
    "одежда",
    "обувь",
    "магазин",
    "сбермаркет",
    "пятёрочка",
    "перекрёсток",
    "лента",
    "магнит",
    "афити",
    "спорт",
    "здоровье",
    "аптека",
    "врач",
    "лекарство",
    "коммуналка",
    "квартплата",
    "жкх",
    "электричество",
    "вода",
    "газ",
    "интернет",
    "связь",
    "телефония",
    "абонентская",
    "плата",
    "услуга",
    "сервис",
    "подписка",
    "стриминг",
    "кино",
    "фильмы",
    "музыка",
    "книги",
    "книжный",
    "бумага",
    "канцелярия",
    "хозяйственный",
    "бытовой",
    "химия",
    "чистящий",
    "порошок",
    "шампунь",
    "гель",
    "мыло",
    "туалет",
    "салфетки",
    "полотенце",
    "мочалка",
    "щетка",
    "мытьё",
    "прачечная",
    "стирка",
    "гладка",
    "глажка",
    "прачечный",
    "техника",
    "посуда",
    "сковорода",
    "кастрюля",
    "ложка",
    "вилка",
    "нож",
    "тарелка",
    "стакан",
    "чашка",
    "блюдце",
    "сервировка",
    "праздник",
    "подарок",
    "цветы",
    "принес",
    "получил",
    "зарплата",
    "премия",
    "бонус",
    "выплата",
    "аванс",
    "возврат",
    "возврат средств",
    "комиссия",
    "штраф",
    "налог",
    "страховка",
    "страхование",
    "вклад",
    "депозит",
    "процент",
    "доход",
    "инвестиция",
    "акция",
    "облигация",
    "фонд",
    "актив",
    "деньги",
    "наличные",
    "карта",
    "сбербанк",
    "т-банк",
    "киви",
    "вайз",
    "альфа",
    "втб",
    "газпром",
    "сбер",
    "сбермегаполис",
    "тинькофф",
}


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
    # First try to find amount with currency keyword
    match = AMOUNT_PATTERN.search(text)
    if match:
        amount_str = match.group(1)
        # Replace comma with dot for proper decimal parsing
        amount_str = amount_str.replace(",", ".")
        try:
            return Decimal(amount_str)
        except Exception:
            pass
    return None


def extract_category(text: str) -> str | None:
    """Extract category name from text using keyword matching.

    Args:
        text: The text to parse.

    Returns:
        Category name if detected, None otherwise.
    """
    text_lower = text.lower()
    for keyword in CATEGORY_INDICATORS:
        if keyword in text_lower:
            # Find the word and return it as-is (or capitalized)
            match = re.search(rf"\b{re.escape(keyword)}\b", text_lower)
            if match:
                return match.group(0).capitalize()
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
    # Remove amount patterns
    result = AMOUNT_PATTERN.sub("", text)
    # Remove currency keywords that might remain
    for kw in CURRENCY_KEYWORDS:
        result = re.sub(rf"\b{re.escape(kw)}\b", "", result, flags=re.IGNORECASE)
    # Clean up extra whitespace
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
        original_text=text,
    )


__all__ = [
    "parse_text",
    "ParsedResult",
    "extract_amount",
    "extract_category",
    "extract_description",
]
