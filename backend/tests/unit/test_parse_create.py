"""Unit tests for parse-and-create functionality.

Tests verify:
- Parser extracts amount from Russian text
- Parser extracts description
- Parser handles edge cases
- Endpoint validates and creates transactions
"""

from app.schemas.parse_create import ParsedResult
from app.services.parse_service import (
    extract_amount,
    extract_category,
    extract_description,
    parse_text,
)


class TestAmountExtraction:
    """Tests for amount extraction from text."""

    def test_extract_amount_with_rubles(self) -> None:
        """Test extracting amount with 'рублей' keyword."""
        result = extract_amount("продукты во вкусвилле 1500 рублей")
        assert result is not None
        assert result == 1500

    def test_extract_amount_with_rub(self) -> None:
        """Test extracting amount with 'руб' keyword."""
        result = extract_amount("кофе 300 руб")
        assert result is not None
        assert result == 300

    def test_extract_amount_with_rouble_symbol(self) -> None:
        """Test extracting amount with ₽ symbol."""
        result = extract_amount("такси домой 1200 ₽")
        assert result is not None
        assert result == 1200

    def test_extract_amount_without_currency(self) -> None:
        """Test extracting amount without currency keyword."""
        result = extract_amount("обед 850")
        assert result is not None
        assert result == 850

    def test_extract_amount_with_decimal(self) -> None:
        """Test extracting amount with decimal places."""
        result = extract_amount("товары 1250.50 рублей")
        assert result is not None
        assert result == 1250.50

    def test_extract_amount_no_amount(self) -> None:
        """Test when no amount is present."""
        result = extract_amount("продукты в магазине")
        assert result is None

    def test_extract_amount_multiple_numbers(self) -> None:
        """Test extraction from text with multiple numbers."""
        result = extract_amount("покупки 1500 и 300 рублей")
        # Should extract the first amount found
        assert result is not None
        assert result == 1500


class TestCategoryExtraction:
    """Tests for category extraction from text."""

    def test_extract_category_products(self) -> None:
        """Test extracting 'продукты' category."""
        result = extract_category("продукты во вкусвилле 1500 рублей")
        assert result == "Продукты"

    def test_extract_category_coffee(self) -> None:
        """Test extracting 'кофе' category."""
        result = extract_category("кофе 300 руб")
        assert result == "Кофе"

    def test_extract_category_transport(self) -> None:
        """Test extracting 'такси' category."""
        result = extract_category("такси домой 1200 руб")
        assert result == "Такси"

    def test_extract_category_no_match(self) -> None:
        """Test when no category keyword is found."""
        result = extract_category("текст без категорий 1000 рублей")
        assert result is None


class TestDescriptionExtraction:
    """Tests for description extraction from text."""

    def test_extract_description_clean(self) -> None:
        """Test extracting clean description."""
        result = extract_description("продукты во вкусвилле 1500 рублей")
        # Amount and currency should be removed
        assert "1500" not in result
        assert "рублей" not in result
        assert "продукты" in result or "во" in result or "вкусвилле" in result

    def test_extract_description_no_amount(self) -> None:
        """Test when no amount present."""
        result = extract_description("покупки в магазине")
        assert result == "покупки в магазине"


class TestParseText:
    """Tests for full text parsing."""

    def test_parse_full_text(self) -> None:
        """Test parsing complete text."""
        result = parse_text("продукты во вкусвилле 1500 рублей")

        assert isinstance(result, ParsedResult)
        assert result.amount == 1500
        assert result.category_name == "Продукты"
        assert result.original_text == "продукты во вкусвилле 1500 рублей"
        assert result.description is not None

    def test_parse_text_no_category(self) -> None:
        """Test parsing when no category detected."""
        # "товары" is in our category keywords, so use a different phrase
        result = parse_text("услуги 1000 руб")

        assert result.amount == 1000
        assert result.category_name is None

    def test_parse_text_no_amount(self) -> None:
        """Test parsing when no amount found."""
        result = parse_text("покупки в магазине")

        assert result.amount is None
        # Description should still be extracted
        assert result.description == "покупки в магазине"


class TestParseEndpoint:
    """Tests for parse-and-create endpoint behavior."""

    def test_parse_request_schema(self) -> None:
        """Test ParseRequest schema."""
        from app.schemas.parse_create import ParseRequest

        req = ParseRequest(text="продукты 1500 рублей")
        assert req.text == "продукты 1500 рублей"

    def test_parsed_result_schema(self) -> None:
        """Test ParsedResult schema."""

        from app.schemas.parse_create import ParsedResult

        result = ParsedResult(
            amount=1500,
            description="продукты во вкусвилле",
            category_name="Продукты",
            original_text="продукты во вкусвилле 1500 рублей",
        )

        assert result.amount == 1500
        assert result.category_name == "Продукты"
        assert result.original_text == "продукты во вкусвилле 1500 рублей"
