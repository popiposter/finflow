"""API tests for unified cashflow ledger endpoints."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.db import async_session_factory
from app.models.projected_transaction import ProjectedTransaction
from app.models.transaction import Transaction
from app.models.types import (
    ProjectedTransactionStatus,
    ProjectedTransactionType,
    TransactionType,
)

pytestmark = pytest.mark.api


class TestCashflowAPI:
    """Tests for /api/v1/cashflow endpoints."""

    async def test_cashflow_report_requires_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Ledger report should require auth."""
        response = await async_client.get(
            "/api/v1/cashflow/report",
            params={"from": "2024-01-01", "to": "2024-01-31"},
        )
        assert response.status_code == 401

    async def test_cashflow_report_mixed_mode(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Ledger report should return actual and projected rows together."""
        account_id = user_with_account_category["account_id"]
        category_id = user_with_account_category["category_id"]
        access_token = user_with_account_category["access_token"]
        user_id = UUID(user_with_account_category["user_id"])
        opening_date = date.today() - timedelta(days=7)
        report_date = date.today() + timedelta(days=3)

        payment_response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "category_id": str(category_id),
                "amount": "250.00",
                "description": "Upcoming bill",
                "recurrence": "monthly",
                "start_date": report_date.isoformat(),
                "next_due_at": report_date.isoformat(),
                "is_active": True,
            },
        )
        planned_payment_id = UUID(payment_response.json()["id"])

        async with async_session_factory() as session:
            session.add(
                Transaction(
                    user_id=user_id,
                    account_id=account_id,
                    category_id=category_id,
                    amount=Decimal("1000.00"),
                    type=TransactionType.INCOME,
                    description="Salary",
                    date_accrual=datetime.combine(
                        opening_date, datetime.min.time(), tzinfo=UTC
                    ),
                    date_cash=datetime.combine(
                        opening_date, datetime.min.time(), tzinfo=UTC
                    ),
                    planned_payment_id=None,
                )
            )
            session.add(
                ProjectedTransaction(
                    planned_payment_id=planned_payment_id,
                    origin_date=report_date,
                    origin_amount=Decimal("250.00"),
                    origin_description="Upcoming bill",
                    origin_category_id=category_id,
                    type=ProjectedTransactionType.EXPENSE,
                    projected_date=report_date,
                    projected_amount=Decimal("250.00"),
                    projected_description="Upcoming bill",
                    projected_category_id=category_id,
                    status=ProjectedTransactionStatus.PENDING,
                )
            )
            await session.commit()

        response = await async_client.get(
            "/api/v1/cashflow/report",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"from": report_date.isoformat(), "to": report_date.isoformat()},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["opening_balance"] == "1000.00"
        assert len(data["rows"]) == 1
        assert data["rows"][0]["row_type"] == "projected"
        assert data["rows"][0]["planned_payment_id"] == str(planned_payment_id)
        assert data["rows"][0]["amount"] == "-250.00"

    async def test_cashflow_forecast_summary(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Forecast endpoint should summarize pending projections."""
        account_id = user_with_account_category["account_id"]
        category_id = user_with_account_category["category_id"]
        access_token = user_with_account_category["access_token"]
        projection_date = date.today() + timedelta(days=5)
        target_date = date.today() + timedelta(days=10)

        payment_response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "category_id": str(category_id),
                "amount": "90.00",
                "description": "Subscription",
                "recurrence": "monthly",
                "start_date": projection_date.isoformat(),
                "next_due_at": projection_date.isoformat(),
                "is_active": True,
            },
        )
        planned_payment_id = UUID(payment_response.json()["id"])

        async with async_session_factory() as session:
            session.add(
                ProjectedTransaction(
                    planned_payment_id=planned_payment_id,
                    origin_date=projection_date,
                    origin_amount=Decimal("90.00"),
                    origin_description="Subscription",
                    origin_category_id=category_id,
                    type=ProjectedTransactionType.EXPENSE,
                    projected_date=projection_date,
                    projected_amount=Decimal("90.00"),
                    projected_description="Subscription",
                    projected_category_id=category_id,
                    status=ProjectedTransactionStatus.PENDING,
                )
            )
            await session.commit()

        response = await async_client.get(
            "/api/v1/cashflow/forecast",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"target_date": target_date.isoformat()},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["projected_expense"] == "90.00"
        assert data["pending_count"] == 1

    async def test_cashflow_report_reflects_patched_transaction_amount_and_date(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Ledger should reflect patched transaction values on the next read."""
        account_id = str(user_with_account_category["account_id"])
        category_id = str(user_with_account_category["category_id"])
        access_token = user_with_account_category["access_token"]

        salary_response = await async_client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "category_id": category_id,
                "amount": "1000.00",
                "type": "income",
                "date_accrual": "2024-01-10T09:00:00Z",
                "date_cash": "2024-01-10T09:00:00Z",
                "description": "Salary",
            },
        )
        expense_response = await async_client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "category_id": category_id,
                "amount": "200.00",
                "type": "expense",
                "date_accrual": "2024-01-11T09:00:00Z",
                "date_cash": "2024-01-11T09:00:00Z",
                "description": "Rent",
            },
        )
        transaction_id = expense_response.json()["id"]

        patch_response = await async_client.patch(
            f"/api/v1/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "amount": "150.00",
                "date_cash": "2024-01-09T09:00:00Z",
            },
        )
        assert patch_response.status_code == 200

        response = await async_client.get(
            "/api/v1/cashflow/report",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"from": "2024-01-09", "to": "2024-01-11"},
        )

        assert response.status_code == 200
        data = response.json()
        assert [row["transaction_id"] for row in data["rows"]] == [
            transaction_id,
            salary_response.json()["id"],
        ]
        assert [row["amount"] for row in data["rows"]] == ["-150.00", "1000.00"]
        assert [row["balance_after"] for row in data["rows"]] == ["-150.00", "850.00"]
