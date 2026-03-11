"""Unit tests for planned payment model and schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.models.planned_payment import PlannedPayment
from app.models.types import Recurrence
from app.schemas.finance import (
    PlannedPaymentCreate,
    PlannedPaymentOut,
    ProjectionGenerationResult,
)


class TestPlannedPaymentModel:
    """Tests for the PlannedPayment model."""

    def test_planned_payment_creation(self) -> None:
        """Test creating a planned payment instance."""
        payment = PlannedPayment(
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            account_id=UUID("22345678-1234-1234-1234-123456789012"),
            amount=Decimal("1500.00"),
            recurrence=Recurrence.MONTHLY,
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 2, 1),
            is_active=True,
        )

        assert payment.amount == Decimal("1500.00")
        assert payment.recurrence == Recurrence.MONTHLY
        assert payment.is_active is True
        assert payment.start_date == date(2024, 1, 1)
        assert payment.next_due_at == date(2024, 2, 1)

    def test_planned_payment_with_optional_fields(self) -> None:
        """Test planned payment with optional fields set."""
        payment = PlannedPayment(
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            account_id=UUID("22345678-1234-1234-1234-123456789012"),
            category_id=UUID("32345678-1234-1234-1234-123456789012"),
            amount=Decimal("2500.50"),
            recurrence=Recurrence.WEEKLY,
            start_date=date(2024, 3, 15),
            next_due_at=date(2024, 3, 22),
            description="Weekly rent payment",
            end_date=date(2025, 3, 15),
            is_active=True,
        )

        assert payment.category_id is not None
        assert payment.description == "Weekly rent payment"
        assert payment.end_date == date(2025, 3, 15)


class TestPlannedPaymentSchemas:
    """Tests for planned payment schemas."""

    def test_planned_payment_create_schema(self) -> None:
        """Test PlannedPaymentCreate schema validation."""
        data = {
            "account_id": "12345678-1234-1234-1234-123456789012",
            "category_id": "22345678-1234-1234-1234-123456789012",
            "amount": "1500.00",
            "description": "Monthly subscription",
            "recurrence": "monthly",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
            "is_active": True,
        }

        schema = PlannedPaymentCreate(**data)

        assert schema.amount == Decimal("1500.00")
        assert schema.recurrence == Recurrence.MONTHLY
        assert schema.start_date == date(2024, 1, 1)

    def test_planned_payment_create_minimal(self) -> None:
        """Test PlannedPaymentCreate with minimal required fields."""
        data = {
            "account_id": "12345678-1234-1234-1234-123456789012",
            "amount": "500.00",
            "recurrence": "daily",
            "start_date": "2024-01-01",
        }

        schema = PlannedPaymentCreate(**data)

        assert schema.category_id is None
        assert schema.description is None
        assert schema.end_date is None
        assert schema.is_active is True  # default

    def test_planned_payment_out_schema(self) -> None:
        """Test PlannedPaymentOut schema."""
        payment = PlannedPayment(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            account_id=UUID("22345678-1234-1234-1234-123456789012"),
            category_id=None,
            amount=Decimal("1500.00"),
            recurrence=Recurrence.MONTHLY,
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 2, 1),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        schema = PlannedPaymentOut.model_validate(payment)

        assert schema.id == payment.id
        assert schema.user_id == payment.user_id
        assert schema.amount == Decimal("1500.00")
        assert schema.recurrence == Recurrence.MONTHLY

    def test_planned_payment_out_full(self) -> None:
        """Test PlannedPaymentOut with all fields."""
        payment = PlannedPayment(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            account_id=UUID("22345678-1234-1234-1234-123456789012"),
            category_id=UUID("32345678-1234-1234-1234-123456789012"),
            amount=Decimal("2500.50"),
            recurrence=Recurrence.WEEKLY,
            start_date=date(2024, 3, 15),
            next_due_at=date(2024, 3, 22),
            description="Weekly rent",
            end_date=date(2025, 3, 15),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        schema = PlannedPaymentOut.model_validate(payment)

        assert schema.category_id == payment.category_id
        assert schema.description == "Weekly rent"
        assert schema.end_date == date(2025, 3, 15)

    def test_projection_generation_result_schema(self) -> None:
        """Test ProjectionGenerationResult schema."""
        result = ProjectionGenerationResult(
            planned_payment_id=UUID("12345678-1234-1234-1234-123456789012"),
            generated_projections=[
                UUID("a2345678-1234-1234-1234-123456789012"),
                UUID("b2345678-1234-1234-1234-123456789012"),
            ],
            next_due_at=date(2024, 3, 1),
            skipped_occurrences=0,
        )

        assert len(result.generated_projections) == 2
        assert result.next_due_at == date(2024, 3, 1)
        assert result.skipped_occurrences == 0


class TestRecurrenceLogic:
    """Tests for recurrence date computation."""

    def test_daily_recurrence(self) -> None:
        """Test daily recurrence date computation."""
        from app.services.planned_payment_service import (
            PlannedPaymentGenerationService,
        )

        # Test using the service's method
        start = date(2024, 1, 1)
        current = date(2024, 1, 1)
        service = PlannedPaymentGenerationService.__new__(
            PlannedPaymentGenerationService
        )

        next_date = service._compute_next_due_date(start, current, Recurrence.DAILY)
        assert next_date == date(2024, 1, 2)

    def test_weekly_recurrence(self) -> None:
        """Test weekly recurrence date computation."""
        from app.services.planned_payment_service import (
            PlannedPaymentGenerationService,
        )

        start = date(2024, 1, 1)
        current = date(2024, 1, 1)
        service = PlannedPaymentGenerationService.__new__(
            PlannedPaymentGenerationService
        )

        next_date = service._compute_next_due_date(start, current, Recurrence.WEEKLY)
        assert next_date == date(2024, 1, 8)

    def test_monthly_recurrence(self) -> None:
        """Test monthly recurrence date computation."""
        from app.services.planned_payment_service import (
            PlannedPaymentGenerationService,
        )

        start = date(2024, 1, 15)
        current = date(2024, 1, 15)
        service = PlannedPaymentGenerationService.__new__(
            PlannedPaymentGenerationService
        )

        next_date = service._compute_next_due_date(start, current, Recurrence.MONTHLY)
        assert next_date == date(2024, 2, 15)

    def test_monthly_recurrence_end_of_month(self) -> None:
        """Test monthly recurrence when start date is at month end."""
        from app.services.planned_payment_service import (
            PlannedPaymentGenerationService,
        )

        # Start on Jan 31, should go to Feb 28/29
        start = date(2024, 1, 31)
        current = date(2024, 1, 31)
        service = PlannedPaymentGenerationService.__new__(
            PlannedPaymentGenerationService
        )

        next_date = service._compute_next_due_date(start, current, Recurrence.MONTHLY)
        assert next_date == date(2024, 2, 29)  # 2024 is leap year

    def test_monthly_recurrence_31st_to_30th(self) -> None:
        """Test monthly recurrence from 31st to next month's last day."""
        from app.services.planned_payment_service import (
            PlannedPaymentGenerationService,
        )

        # Start on 31st, July has 31 days
        start = date(2024, 1, 31)
        current = date(2024, 3, 31)  # March 31
        service = PlannedPaymentGenerationService.__new__(
            PlannedPaymentGenerationService
        )

        next_date = service._compute_next_due_date(start, current, Recurrence.MONTHLY)
        # April has 30 days, so should be April 30
        assert next_date == date(2024, 4, 30)
