from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


CLIENT_HEADERS = {"X-Client-Local-Date": "2026-10-31"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    test_id = uuid4().hex
    database_path = Path.cwd() / f".category-test-summary-{test_id}.sqlite3"
    log_path = Path.cwd() / f".category-test-summary-{test_id}.log"
    try:
        with TestClient(create_app(database_path, log_path)) as test_client:
            yield test_client
    finally:
        database_path.unlink(missing_ok=True)
        log_path.unlink(missing_ok=True)


def create_category(client: TestClient, category_type: str) -> dict[str, object]:
    response = client.post(
        "/api/categories",
        json={
            "name": f"{category_type}-{uuid4().hex[:12]}",
            "type": category_type,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_transaction(
    client: TestClient,
    category: dict[str, object],
    amount: str,
) -> dict[str, object]:
    response = client.post(
        "/api/transactions",
        json={
            "type": category["type"],
            "amount": amount,
            "date": "2026-10-31",
            "category_id": category["id"],
            "description": None,
        },
        headers=CLIENT_HEADERS,
    )
    assert response.status_code == 201
    return response.json()


def assert_summary(
    response,
    *,
    total_income: str,
    total_expenses: str,
    current_balance: str,
) -> None:
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"total_income", "total_expenses", "current_balance"}
    assert body == {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "current_balance": current_balance,
    }
    assert all(isinstance(value, str) for value in body.values())


def test_financial_summary_returns_zero_values_for_empty_database(
    client: TestClient,
) -> None:
    """API-P-010; REQ-F-002, REQ-F-021..REQ-F-023; FinancialSummary schema."""
    response = client.get("/api/financial-summary")

    assert_summary(
        response,
        total_income="0.00",
        total_expenses="0.00",
        current_balance="0.00",
    )


def test_financial_summary_calculates_income_expenses_and_balance(
    client: TestClient,
) -> None:
    """API-P-010; REQ-F-021..REQ-F-023; AC-022..AC-024."""
    income = create_category(client, "income")
    expense = create_category(client, "expense")
    create_transaction(client, income, "25000.00")
    create_transaction(client, expense, "850.50")

    response = client.get("/api/financial-summary")

    assert_summary(
        response,
        total_income="25000.00",
        total_expenses="850.50",
        current_balance="24149.50",
    )


def test_financial_summary_can_be_negative_and_ignores_list_filters(
    client: TestClient,
) -> None:
    """API-P-010; BDD-012; REQ-F-023, REQ-F-024; AC-024, AC-025."""
    income = create_category(client, "income")
    expense = create_category(client, "expense")
    create_transaction(client, income, "10.00")
    create_transaction(client, expense, "25.25")

    filtered = client.get("/api/transactions", params={"type": "income"})
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    response = client.get("/api/financial-summary")

    assert_summary(
        response,
        total_income="10.00",
        total_expenses="25.25",
        current_balance="-15.25",
    )


def test_financial_summary_preserves_decimal_precision(client: TestClient) -> None:
    """REQ-F-002, REQ-F-021..REQ-F-023; AC-002, AC-022..AC-024."""
    income = create_category(client, "income")
    expense = create_category(client, "expense")
    create_transaction(client, income, "9999999999999999.99")
    create_transaction(client, income, "0.02")
    create_transaction(client, expense, "0.01")

    response = client.get("/api/financial-summary")

    assert_summary(
        response,
        total_income="10000000000000000.01",
        total_expenses="0.01",
        current_balance="10000000000000000.00",
    )


def test_financial_summary_recalculates_after_transaction_crud(
    client: TestClient,
) -> None:
    """API-P-010; REQ-F-009, REQ-F-021..REQ-F-024; AC-009, AC-022..AC-025."""
    income = create_category(client, "income")
    expense = create_category(client, "expense")
    income_transaction = create_transaction(client, income, "100.00")
    expense_transaction = create_transaction(client, expense, "30.50")

    assert_summary(
        client.get("/api/financial-summary"),
        total_income="100.00",
        total_expenses="30.50",
        current_balance="69.50",
    )

    updated = client.patch(
        f"/api/transactions/{income_transaction['id']}",
        json={"amount": "120.25"},
        headers=CLIENT_HEADERS,
    )
    assert updated.status_code == 200
    assert_summary(
        client.get("/api/financial-summary"),
        total_income="120.25",
        total_expenses="30.50",
        current_balance="89.75",
    )

    deleted = client.delete(f"/api/transactions/{expense_transaction['id']}")
    assert deleted.status_code == 204
    assert_summary(
        client.get("/api/financial-summary"),
        total_income="120.25",
        total_expenses="0.00",
        current_balance="120.25",
    )
