"""API tests for finance CRUD endpoints.

These tests verify:
- POST /api/v1/accounts - Create account
- GET /api/v1/accounts - List accounts
- GET /api/v1/accounts/{id} - Get account
- PUT /api/v1/accounts/{id} - Update account
- DELETE /api/v1/accounts/{id} - Delete account

- POST /api/v1/categories - Create category
- GET /api/v1/categories - List categories
- GET /api/v1/categories/{id} - Get category
- PUT /api/v1/categories/{id} - Update category
- DELETE /api/v1/categories/{id} - Delete category

- POST /api/v1/transactions - Create transaction
- GET /api/v1/transactions - List transactions
- GET /api/v1/transactions/{id} - Get transaction
- PUT /api/v1/transactions/{id} - Update transaction
- DELETE /api/v1/transactions/{id} - Delete transaction
"""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.api


async def _login_user(async_client: AsyncClient, email: str, password: str) -> str:
    """Register and login a user, return access token."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return login_response.json()["access_token"]


@pytest.mark.api
class TestAccountsEndpoints:
    """Tests for accounts CRUD endpoints."""

    async def test_create_account_success(self, async_client: AsyncClient) -> None:
        """Test successful account creation via API."""
        # Register and login user
        access_token = await _login_user(
            async_client, "accuser@example.com", "SecurePass123!"
        )

        # Create account via API
        response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Main Checking",
                "type": "checking",
                "description": "Primary checking account",
                "currency_code": "USD",
                "is_active": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Main Checking"
        assert data["type"] == "checking"
        assert data["description"] == "Primary checking account"
        assert data["currency_code"] == "USD"
        assert data["is_active"] is True
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data

    async def test_create_account_minimal(self, async_client: AsyncClient) -> None:
        """Test creating account with minimal required fields."""
        # Register and login user
        access_token = await _login_user(
            async_client, "minimalacc@example.com", "SecurePass123!"
        )

        # Create account with only required fields
        response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Cash Wallet",
                "type": "cash",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Cash Wallet"
        assert data["type"] == "cash"
        # Defaults should apply
        assert data["currency_code"] == "USD"
        assert data["is_active"] is True

    async def test_create_account_invalid_type(self, async_client: AsyncClient) -> None:
        """Test creating account with invalid type."""
        # Register and login user
        access_token = await _login_user(
            async_client, "invalidtype@example.com", "SecurePass123!"
        )

        response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Invalid",
                "type": "invalid_type",
            },
        )

        assert response.status_code == 422

    async def test_create_account_unauthorized(self, async_client: AsyncClient) -> None:
        """Test creating account without authentication."""
        response = await async_client.post(
            "/api/v1/accounts",
            json={"name": "Test", "type": "checking"},
        )

        assert response.status_code == 401

    async def test_list_accounts_empty(self, async_client: AsyncClient) -> None:
        """Test listing accounts when none exist."""
        # Register and login user
        access_token = await _login_user(
            async_client, "emptyaccuser@example.com", "SecurePass123!"
        )

        response = await async_client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_accounts(self, async_client: AsyncClient) -> None:
        """Test listing multiple accounts."""
        # Register and login user
        access_token = await _login_user(
            async_client, "listaccuser@example.com", "SecurePass123!"
        )

        # Create accounts
        await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Account 1", "type": "checking"},
        )
        await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Account 2", "type": "savings"},
        )

        # List accounts
        response = await async_client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_get_account_not_found(self, async_client: AsyncClient) -> None:
        """Test getting a non-existent account."""
        # Register and login user
        access_token = await _login_user(
            async_client, "getnotfound@example.com", "SecurePass123!"
        )

        fake_id = "12345678-1234-1234-1234-123456789012"
        response = await async_client.get(
            f"/api/v1/accounts/{fake_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404

    async def test_update_account(self, async_client: AsyncClient) -> None:
        """Test updating an account."""
        # Register and login user
        access_token = await _login_user(
            async_client, "updateaccuser@example.com", "SecurePass123!"
        )

        # Create account
        create_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Original Name", "type": "checking"},
        )
        account_id = create_response.json()["id"]

        # Update account
        response = await async_client.put(
            f"/api/v1/accounts/{account_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Updated Name",
                "type": "savings",
                "description": "Updated description",
                "current_balance": "100.50",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["type"] == "savings"
        assert data["description"] == "Updated description"
        assert data["current_balance"] == "100.50"

    async def test_delete_account(self, async_client: AsyncClient) -> None:
        """Test deleting an account."""
        # Register and login user
        access_token = await _login_user(
            async_client, "deleteaccuser@example.com", "SecurePass123!"
        )

        # Create account
        create_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "To Delete", "type": "checking"},
        )
        account_id = create_response.json()["id"]

        # Delete account
        response = await async_client.delete(
            f"/api/v1/accounts/{account_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await async_client.get(
            f"/api/v1/accounts/{account_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert get_response.status_code == 404


@pytest.mark.api
class TestCategoriesEndpoints:
    """Tests for categories CRUD endpoints."""

    async def test_create_category_success(self, async_client: AsyncClient) -> None:
        """Test successful category creation via API."""
        # Register and login user
        access_token = await _login_user(
            async_client, "catuser@example.com", "SecurePass123!"
        )

        response = await async_client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Housing",
                "type": "expense",
                "description": "Housing expenses",
                "is_active": True,
                "display_order": 1,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Housing"
        assert data["type"] == "expense"
        assert data["is_active"] is True
        assert data["display_order"] == 1
        assert "id" in data

    async def test_create_category_with_parent(self, async_client: AsyncClient) -> None:
        """Test creating a child category with parent."""
        # Register and login user
        access_token = await _login_user(
            async_client, "parentcatuser@example.com", "SecurePass123!"
        )

        # Create parent
        parent_response = await async_client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Food", "type": "expense"},
        )
        parent_id = parent_response.json()["id"]

        # Create child
        response = await async_client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Groceries",
                "type": "expense",
                "parent_id": parent_id,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == parent_id
        assert data["name"] == "Groceries"

    async def test_create_category_invalid_parent(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating category with non-existent parent."""
        # Register and login user
        access_token = await _login_user(
            async_client, "invalidparent@example.com", "SecurePass123!"
        )

        fake_id = "12345678-1234-1234-1234-123456789012"
        response = await async_client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Invalid",
                "type": "expense",
                "parent_id": fake_id,
            },
        )

        assert response.status_code == 404

    async def test_create_category_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating category without authentication."""
        response = await async_client.post(
            "/api/v1/categories",
            json={"name": "Test", "type": "expense"},
        )

        assert response.status_code == 401

    async def test_list_categories(self, async_client: AsyncClient) -> None:
        """Test listing categories."""
        # Register and login user
        access_token = await _login_user(
            async_client, "listcatuser@example.com", "SecurePass123!"
        )

        # Create categories
        await async_client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Income", "type": "income"},
        )
        await async_client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Food", "type": "expense"},
        )

        # List categories
        response = await async_client.get(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_get_category_not_found(self, async_client: AsyncClient) -> None:
        """Test getting a non-existent category."""
        # Register and login user
        access_token = await _login_user(
            async_client, "getcatnotfound@example.com", "SecurePass123!"
        )

        fake_id = "12345678-1234-1234-1234-123456789012"
        response = await async_client.get(
            f"/api/v1/categories/{fake_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404

    async def test_update_category(self, async_client: AsyncClient) -> None:
        """Test updating a category."""
        # Register and login user
        access_token = await _login_user(
            async_client, "updatecatuser@example.com", "SecurePass123!"
        )

        # Create category
        create_response = await async_client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Original", "type": "expense"},
        )
        category_id = create_response.json()["id"]

        # Update category
        response = await async_client.put(
            f"/api/v1/categories/{category_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Updated",
                "type": "income",
                "is_active": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["type"] == "income"
        assert data["is_active"] is False

    async def test_delete_category(self, async_client: AsyncClient) -> None:
        """Test deleting a category."""
        # Register and login user
        access_token = await _login_user(
            async_client, "deletecatuser@example.com", "SecurePass123!"
        )

        # Create category
        create_response = await async_client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "To Delete", "type": "expense"},
        )
        category_id = create_response.json()["id"]

        # Delete category
        response = await async_client.delete(
            f"/api/v1/categories/{category_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await async_client.get(
            f"/api/v1/categories/{category_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert get_response.status_code == 404


@pytest.mark.api
class TestTransactionsEndpoints:
    """Tests for transactions CRUD endpoints."""

    async def test_create_transaction_success(self, async_client: AsyncClient) -> None:
        """Test successful transaction creation via API."""
        # Register and login user
        access_token = await _login_user(
            async_client, "transuser@example.com", "SecurePass123!"
        )

        # Create account first
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Checking", "type": "checking"},
        )
        account_id = account_response.json()["id"]

        # Create transaction
        response = await async_client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "150.00",
                "type": "payment",
                "date_accrual": "2024-01-15T10:00:00Z",
                "date_cash": "2024-01-16T10:00:00Z",
                "description": "Grocery shopping",
                "is_reconciled": False,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == "150.00"
        assert data["type"] == "payment"
        assert data["description"] == "Grocery shopping"
        assert data["is_reconciled"] is False
        assert data["account_id"] == account_id
        assert "id" in data

    async def test_create_transaction_with_category(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating transaction with category reference."""
        # Register and login user
        access_token = await _login_user(
            async_client, "transcatuser@example.com", "SecurePass123!"
        )

        # Create account and category
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Checking", "type": "checking"},
        )
        account_id = account_response.json()["id"]

        category_response = await async_client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Food", "type": "expense"},
        )
        category_id = category_response.json()["id"]

        # Create transaction with category
        response = await async_client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "75.50",
                "type": "payment",
                "date_accrual": "2024-01-15T10:00:00Z",
                "date_cash": "2024-01-15T10:00:00Z",
                "category_id": category_id,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] == category_id

    async def test_create_transaction_dates(self, async_client: AsyncClient) -> None:
        """Test transaction with different date_accrual and date_cash.

        This validates accrual vs cash basis accounting support.
        """
        # Register and login user
        access_token = await _login_user(
            async_client, "datesuser@example.com", "SecurePass123!"
        )

        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Checking", "type": "checking"},
        )
        account_id = account_response.json()["id"]

        # Create transaction where dates differ
        response = await async_client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "200.00",
                "type": "income",
                "date_accrual": "2024-01-31T23:59:59Z",
                "date_cash": "2024-02-05T10:00:00Z",  # Cash moves later
                "description": "Invoice payment received",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify dates are stored correctly (parse ISO 8601 for comparison)
        date_accrual = datetime.fromisoformat(data["date_accrual"])
        date_cash = datetime.fromisoformat(data["date_cash"])
        assert date_accrual == datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
        assert date_cash == datetime(2024, 2, 5, 10, 0, 0, tzinfo=timezone.utc)
        assert date_accrual != date_cash

    async def test_create_transaction_invalid_account(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating transaction with non-existent account."""
        # Register and login user
        access_token = await _login_user(
            async_client, "invalidacc@example.com", "SecurePass123!"
        )

        fake_id = "12345678-1234-1234-1234-123456789012"
        response = await async_client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": fake_id,
                "amount": "100.00",
                "type": "payment",
                "date_accrual": "2024-01-15T10:00:00Z",
                "date_cash": "2024-01-16T10:00:00Z",
            },
        )

        assert response.status_code == 404

    async def test_create_transaction_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating transaction without authentication."""
        response = await async_client.post(
            "/api/v1/transactions",
            json={
                "account_id": "12345678-1234-1234-1234-123456789012",
                "amount": "100.00",
                "type": "payment",
                "date_accrual": "2024-01-15T10:00:00Z",
                "date_cash": "2024-01-16T10:00:00Z",
            },
        )

        assert response.status_code == 401

    async def test_list_transactions(self, async_client: AsyncClient) -> None:
        """Test listing transactions."""
        # Register and login user
        access_token = await _login_user(
            async_client, "listtransuser@example.com", "SecurePass123!"
        )

        # Create account
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Checking", "type": "checking"},
        )
        account_id = account_response.json()["id"]

        # Create transactions
        await async_client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "100.00",
                "type": "payment",
                "date_accrual": "2024-01-15T10:00:00Z",
                "date_cash": "2024-01-16T10:00:00Z",
            },
        )
        await async_client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "50.00",
                "type": "income",
                "date_accrual": "2024-01-16T10:00:00Z",
                "date_cash": "2024-01-17T10:00:00Z",
            },
        )

        # List transactions
        response = await async_client.get(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_get_transaction_not_found(self, async_client: AsyncClient) -> None:
        """Test getting a non-existent transaction."""
        # Register and login user
        access_token = await _login_user(
            async_client, "gettransnotfound@example.com", "SecurePass123!"
        )

        fake_id = "12345678-1234-1234-1234-123456789012"
        response = await async_client.get(
            f"/api/v1/transactions/{fake_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404

    async def test_update_transaction(self, async_client: AsyncClient) -> None:
        """Test updating a transaction."""
        # Register and login user
        access_token = await _login_user(
            async_client, "updatetransuser@example.com", "SecurePass123!"
        )

        # Create account
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Checking", "type": "checking"},
        )
        account_id = account_response.json()["id"]

        # Create transaction
        create_response = await async_client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "100.00",
                "type": "payment",
                "date_accrual": "2024-01-15T10:00:00Z",
                "date_cash": "2024-01-16T10:00:00Z",
            },
        )
        transaction_id = create_response.json()["id"]

        # Update transaction
        response = await async_client.put(
            f"/api/v1/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "150.00",
                "type": "income",
                "description": "Updated description",
                "date_accrual": "2024-01-20T10:00:00Z",
                "date_cash": "2024-01-21T10:00:00Z",
                "is_reconciled": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "150.00"
        assert data["type"] == "income"
        assert data["description"] == "Updated description"
        assert data["is_reconciled"] is True

    async def test_delete_transaction(self, async_client: AsyncClient) -> None:
        """Test deleting a transaction."""
        # Register and login user
        access_token = await _login_user(
            async_client, "deletetransuser@example.com", "SecurePass123!"
        )

        # Create account
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Checking", "type": "checking"},
        )
        account_id = account_response.json()["id"]

        # Create transaction
        create_response = await async_client.post(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "100.00",
                "type": "payment",
                "date_accrual": "2024-01-15T10:00:00Z",
                "date_cash": "2024-01-16T10:00:00Z",
            },
        )
        transaction_id = create_response.json()["id"]

        # Delete transaction
        response = await async_client.delete(
            f"/api/v1/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await async_client.get(
            f"/api/v1/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert get_response.status_code == 404
