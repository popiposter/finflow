"""API tests for workbook-based transaction import."""

from datetime import datetime, timezone
from io import BytesIO

import pytest
from httpx import AsyncClient
from openpyxl import Workbook

pytestmark = pytest.mark.api


async def _login_user(async_client: AsyncClient, email: str, password: str) -> str:
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return login_response.json()["access_token"]


async def _create_account(async_client: AsyncClient, access_token: str, name: str) -> str:
    response = await async_client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": name, "type": "checking"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _build_workbook_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append([46038, "Самокат", -907])
    sheet.append([46039, "Зарплата", 120000])
    sheet.append([None, None, None])
    sheet.append([46040, "Такси", -335.50])

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


class TestTransactionImportEndpoint:
    async def test_import_transactions_from_xlsx(
        self,
        async_client: AsyncClient,
    ) -> None:
        access_token = await _login_user(
            async_client,
            "xlsximport@example.com",
            "SecurePass123!",
        )
        account_id = await _create_account(async_client, access_token, "Import account")

        response = await async_client.post(
            "/api/v1/transactions/import",
            headers={"Authorization": f"Bearer {access_token}"},
            files={
                "file": (
                    "transactions.xlsx",
                    _build_workbook_bytes(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            },
            data={"account_id": account_id},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["imported_count"] == 3
        assert data["skipped_count"] == 0
        assert len(data["imported_transaction_ids"]) == 3

        list_response = await async_client.get(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert list_response.status_code == 200
        transactions = sorted(
            list_response.json(),
            key=lambda item: item["description"] or "",
        )
        assert len(transactions) == 3
        assert [item["description"] for item in transactions] == [
            "Зарплата",
            "Самокат",
            "Такси",
        ]
        assert [item["type"] for item in transactions] == [
            "income",
            "expense",
            "expense",
        ]
        assert [item["amount"] for item in transactions] == [
            "120000.00",
            "907.00",
            "335.50",
        ]

        samokat_transaction = next(
            item for item in transactions if item["description"] == "Самокат"
        )
        first_date = datetime.fromisoformat(samokat_transaction["date_cash"])
        assert first_date == datetime(2026, 1, 16, 0, 0, tzinfo=timezone.utc)

    async def test_import_transactions_rejects_foreign_account(
        self,
        async_client: AsyncClient,
    ) -> None:
        owner_token = await _login_user(
            async_client,
            "xlsxowner@example.com",
            "SecurePass123!",
        )
        other_token = await _login_user(
            async_client,
            "xlsxother@example.com",
            "SecurePass123!",
        )
        account_id = await _create_account(async_client, owner_token, "Owner account")

        response = await async_client.post(
            "/api/v1/transactions/import",
            headers={"Authorization": f"Bearer {other_token}"},
            files={
                "file": (
                    "transactions.xlsx",
                    _build_workbook_bytes(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            },
            data={"account_id": account_id},
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "account_not_found"

    async def test_import_transactions_rejects_non_xlsx_file(
        self,
        async_client: AsyncClient,
    ) -> None:
        access_token = await _login_user(
            async_client,
            "xlsxinvalid@example.com",
            "SecurePass123!",
        )
        account_id = await _create_account(async_client, access_token, "Import account")

        response = await async_client.post(
            "/api/v1/transactions/import",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("transactions.csv", b"date,description,amount", "text/csv")},
            data={"account_id": account_id},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "import_invalid_file"
        assert data["error"]["message"] == "Only .xlsx files are supported"
