from collections.abc import Iterator
from pathlib import Path
import sqlite3
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


CLIENT_DATE = "2026-10-31"
CLIENT_HEADERS = {"X-Client-Local-Date": CLIENT_DATE}


@pytest.fixture
def client() -> Iterator[TestClient]:
    test_id = uuid4().hex
    database_path = Path.cwd() / f".category-test-transaction-{test_id}.sqlite3"
    log_path = Path.cwd() / f".category-test-transaction-{test_id}.log"
    try:
        with TestClient(create_app(database_path, log_path)) as test_client:
            yield test_client
    finally:
        database_path.unlink(missing_ok=True)
        log_path.unlink(missing_ok=True)


def unique_name(prefix: str = "Категорія") -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def create_category(client: TestClient, category_type: str) -> dict[str, object]:
    name = unique_name("Дохід" if category_type == "income" else "Витрата")
    response = client.post(
        "/api/categories",
        json={"name": name, "type": category_type},
    )
    assert response.status_code == 201
    return response.json()


def transaction_body(
    category_id: int,
    **overrides: object,
) -> dict[str, object]:
    body: dict[str, object] = {
        "type": "income",
        "amount": "1500.00",
        "date": CLIENT_DATE,
        "category_id": category_id,
        "description": None,
    }
    body.update(overrides)
    return body


def create_transaction_record(
    client: TestClient,
    category: dict[str, object],
    *,
    transaction_type: str,
    date: str,
    description: str | None,
) -> dict[str, object]:
    response = client.post(
        "/api/transactions",
        json=transaction_body(
            int(category["id"]),
            type=transaction_type,
            date=date,
            description=description,
        ),
        headers=CLIENT_HEADERS,
    )
    assert response.status_code == 201
    return response.json()


def assert_transaction(
    response,
    *,
    expected: dict[str, object],
    expected_category_name: str,
    expected_status: int = 201,
) -> int:
    assert response.status_code == expected_status
    body = response.json()
    assert set(body) == {
        "id",
        "type",
        "amount",
        "date",
        "category_id",
        "category_name",
        "description",
    }
    assert isinstance(body["id"], int) and not isinstance(body["id"], bool)
    assert body["id"] >= 1
    for field in ("type", "amount", "date", "category_id", "description"):
        assert body[field] == expected.get(field)
    assert body["category_name"] == expected_category_name
    return body["id"]


def assert_error_response(
    response,
    *,
    expected_status: int,
    expected_code: str,
    expected_field: str | set[str] | None = None,
    expected_rule: str | None = None,
) -> None:
    assert response.status_code == expected_status
    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert set(error).issubset({"code", "message", "field", "rule"})
    assert error["code"] == expected_code
    assert isinstance(error["message"], str) and error["message"]
    if expected_field is None:
        assert "field" not in error
        assert "rule" not in error
    else:
        if isinstance(expected_field, set):
            assert error["field"] in expected_field
        else:
            assert error["field"] == expected_field
        assert isinstance(error["rule"], str) and error["rule"]
        if expected_rule is not None:
            assert error["rule"] == expected_rule


@pytest.mark.parametrize(
    ("category_type", "amount", "date", "description"),
    [
        ("income", "1500.00", CLIENT_DATE, None),
        ("expense", "0.01", "2026-01-01", "А"),
        ("expense", "10.00", "2026-10-30", ""),
        ("income", "999999999999.99", "2000-02-29", "О" * 255),
        ("expense", "850.50", "2026-10-30", None),
    ],
)
def test_create_transaction_returns_openapi_transaction(
    client: TestClient,
    category_type: str,
    amount: str,
    date: str,
    description: str | None,
) -> None:
    """API-P-005; BDD-005; REQ-F-002..REQ-F-007; AC-003..AC-007."""
    category = create_category(client, category_type)
    body = transaction_body(
        int(category["id"]),
        type=category_type,
        amount=amount,
        date=date,
        description=description,
    )

    response = client.post("/api/transactions", json=body, headers=CLIENT_HEADERS)

    assert_transaction(
        response,
        expected=body,
        expected_category_name=str(category["name"]),
    )


def test_create_transaction_without_description_returns_null(
    client: TestClient,
) -> None:
    """REQ-F-006; AC-006; TransactionCreate/Transaction response contract."""
    category = create_category(client, "income")
    body = transaction_body(int(category["id"]))
    del body["description"]

    response = client.post("/api/transactions", json=body, headers=CLIENT_HEADERS)

    expected = {**body, "description": None}
    assert_transaction(
        response,
        expected=expected,
        expected_category_name=str(category["name"]),
    )


def test_create_transactions_assigns_unique_positive_ids(client: TestClient) -> None:
    """API-P-005; REQ-F-003; AC-003."""
    category = create_category(client, "income")
    body = transaction_body(int(category["id"]))

    first = client.post("/api/transactions", json=body, headers=CLIENT_HEADERS)
    second = client.post("/api/transactions", json=body, headers=CLIENT_HEADERS)

    first_id = assert_transaction(
        first, expected=body, expected_category_name=str(category["name"])
    )
    second_id = assert_transaction(
        second, expected=body, expected_category_name=str(category["name"])
    )
    assert first_id != second_id


@pytest.mark.parametrize(
    ("mutation", "expected_field"),
    [
        (("remove", "type"), "type"),
        (("remove", "amount"), "amount"),
        (("remove", "date"), "date"),
        (("remove", "category_id"), "category_id"),
        (("set", "type", None), "type"),
        (("set", "type", "other"), "type"),
        (("set", "amount", None), "amount"),
        (("set", "amount", 1250.0), "amount"),
        (("set", "amount", "0.00"), "amount"),
        (("set", "amount", "-1.00"), "amount"),
        (("set", "amount", "1"), "amount"),
        (("set", "amount", "1.0"), "amount"),
        (("set", "amount", "01.00"), "amount"),
        (("set", "amount", "1.000"), "amount"),
        (("set", "date", None), "date"),
        (("set", "date", "2026-02-29"), "date"),
        (("set", "date", "31-10-2026"), "date"),
        (("set", "category_id", 0), "category_id"),
        (("set", "category_id", "1"), "category_id"),
        (("set", "description", "Д" * 256), "description"),
        (("set", "command", "noop"), "command"),
    ],
)
def test_create_transaction_rejects_invalid_body(
    client: TestClient,
    mutation: tuple[object, ...],
    expected_field: str,
) -> None:
    """API-N-011, API-N-012, API-N-017, API-N-018; REQ-NF-005."""
    category = create_category(client, "income")
    body = transaction_body(int(category["id"]))
    if mutation[0] == "remove":
        body.pop(str(mutation[1]))
    else:
        body[str(mutation[1])] = mutation[2]

    response = client.post("/api/transactions", json=body, headers=CLIENT_HEADERS)

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field=expected_field,
    )


def test_create_transaction_rejects_future_date(client: TestClient) -> None:
    """API-N-013; BDD-006; REQ-F-005; AC-005."""
    category = create_category(client, "income")
    body = transaction_body(int(category["id"]), date="2026-11-01")

    response = client.post("/api/transactions", json=body, headers=CLIENT_HEADERS)

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="date",
        expected_rule="not_after_client_local_date",
    )


@pytest.mark.parametrize("header_value", [None, "2026-02-29", "31-10-2026"])
def test_create_transaction_requires_valid_client_local_date(
    client: TestClient,
    header_value: str | None,
) -> None:
    """API-N-014; REQ-F-005, REQ-NF-005; ClientLocalDate contract."""
    category = create_category(client, "income")
    headers = {} if header_value is None else {"X-Client-Local-Date": header_value}

    response = client.post(
        "/api/transactions",
        json=transaction_body(int(category["id"])),
        headers=headers,
    )

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="X-Client-Local-Date",
    )


def test_create_transaction_rejects_category_type_mismatch(
    client: TestClient,
) -> None:
    """API-N-015; BDD-006; REQ-F-007; AC-007."""
    category = create_category(client, "expense")

    response = client.post(
        "/api/transactions",
        json=transaction_body(int(category["id"]), type="income"),
        headers=CLIENT_HEADERS,
    )

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="category_id",
        expected_rule="category_type_matches_transaction_type",
    )


def test_create_transaction_rejects_missing_category(client: TestClient) -> None:
    """API-N-016; REQ-F-007."""
    response = client.post(
        "/api/transactions",
        json=transaction_body(999),
        headers=CLIENT_HEADERS,
    )

    assert_error_response(
        response,
        expected_status=404,
        expected_code="RESOURCE_NOT_FOUND",
        expected_field="id",
        expected_rule="resource_exists",
    )


def test_create_transaction_rejects_malformed_json(client: TestClient) -> None:
    """API-N-001; REQ-NF-005."""
    response = client.post(
        "/api/transactions",
        content=b'{"type":"income"',
        headers={"Content-Type": "application/json", **CLIENT_HEADERS},
    )

    assert_error_response(
        response, expected_status=400, expected_code="MALFORMED_JSON"
    )


def test_create_transaction_rejects_non_json_content_type(client: TestClient) -> None:
    """API-N-006; REQ-NF-005."""
    response = client.post(
        "/api/transactions",
        content='{"type":"income"}',
        headers={"Content-Type": "text/plain", **CLIENT_HEADERS},
    )

    assert_error_response(
        response,
        expected_status=415,
        expected_code="UNSUPPORTED_MEDIA_TYPE",
        expected_field="Content-Type",
        expected_rule="application_json_media_type",
    )


def test_transaction_description_with_code_syntax_is_plain_text(
    client: TestClient,
) -> None:
    """API-N-030; REQ-NF-004; AC-029."""
    category = create_category(client, "expense")
    body = transaction_body(
        int(category["id"]),
        type="expense",
        description="$(whoami); DROP TABLE transactions;",
    )

    response = client.post("/api/transactions", json=body, headers=CLIENT_HEADERS)

    assert_transaction(
        response, expected=body, expected_category_name=str(category["name"])
    )


def test_rejected_create_transaction_does_not_change_state(
    client: TestClient,
) -> None:
    """BDD-006; REQ-F-004, REQ-NF-002; AC-004, AC-027."""
    category = create_category(client, "income")
    response = client.post(
        "/api/transactions",
        json=transaction_body(int(category["id"]), amount="-1.00"),
        headers=CLIENT_HEADERS,
    )
    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="amount",
    )

    listed = client.get("/api/transactions")

    assert listed.status_code == 200
    assert listed.json() == []


def test_list_transactions_returns_empty_array(client: TestClient) -> None:
    """API-P-006; BDD-011; REQ-F-019; AC-020."""
    response = client.get("/api/transactions")

    assert response.status_code == 200
    assert response.json() == []


def test_list_transactions_returns_empty_for_valid_missing_category_filter(
    client: TestClient,
) -> None:
    """API-P-007; CategoryIdFilter contract; REQ-F-017, REQ-F-020."""
    response = client.get("/api/transactions", params={"category_id": "999"})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    ("query", "expected_field", "expected_rule"),
    [
        ({"type": "other"}, "type", None),
        ({"category_id": "0"}, "category_id", None),
        ({"category_id": "not-an-integer"}, "category_id", None),
        ({"date_from": "2026-10-01"}, "date_range", None),
        ({"date_to": "2026-10-31"}, "date_range", None),
        (
            {"date_from": "2026-11-01", "date_to": "2026-10-31"},
            "date_range",
            "date_from_not_after_date_to",
        ),
        (
            {"date_from": "2026-02-29", "date_to": "2026-10-31"},
            "date_from",
            None,
        ),
        (
            {"date_from": "2026-10-01", "date_to": "31-10-2026"},
            "date_to",
            None,
        ),
    ],
)
def test_list_transactions_rejects_invalid_filters(
    client: TestClient,
    query: dict[str, str],
    expected_field: str,
    expected_rule: str | None,
) -> None:
    """API-N-019..API-N-021; BDD-010; REQ-F-018, REQ-NF-005; AC-019."""
    response = client.get("/api/transactions", params=query)

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field=expected_field,
        expected_rule=expected_rule,
    )


@pytest.mark.parametrize(
    ("query_string", "expected_field"),
    [
        ("sort=date", "sort"),
        ("type=income&type=expense", "type"),
    ],
)
def test_list_transactions_rejects_unknown_or_repeated_query_parameter(
    client: TestClient,
    query_string: str,
    expected_field: str,
) -> None:
    """REQ-F-017, REQ-NF-005; TransactionFilterQuery contract."""
    response = client.get(f"/api/transactions?{query_string}")

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field=expected_field,
    )


def test_list_transactions_returns_full_records_sorted_by_date(
    client: TestClient,
) -> None:
    """API-P-006; BDD-009; REQ-F-015, REQ-F-016; AC-016, AC-017."""
    income = create_category(client, "income")
    expense = create_category(client, "expense")
    created = []
    for category, transaction_type, amount, date, description in (
        (expense, "expense", "30.00", "2026-10-15", None),
        (income, "income", "100.00", "2026-10-31", None),
        (expense, "expense", "20.00", "2026-10-20", None),
        (income, "income", "40.00", "2026-10-20", "Опис"),
    ):
        created.append(
            client.post(
                "/api/transactions",
                json=transaction_body(
                    int(category["id"]),
                    type=transaction_type,
                    amount=amount,
                    date=date,
                    description=description,
                ),
                headers=CLIENT_HEADERS,
            ).json()
        )

    response = client.get("/api/transactions")

    assert response.status_code == 200
    body = response.json()
    assert [item["date"] for item in body] == sorted(
        (item["date"] for item in body), reverse=True
    )
    assert {item["id"]: item for item in body} == {
        item["id"]: item for item in created
    }


@pytest.mark.parametrize("filter_kind", ["type", "category", "date", "combined"])
def test_list_transactions_applies_each_filter_and_combines_with_and(
    client: TestClient,
    filter_kind: str,
) -> None:
    """API-P-007; BDD-010; REQ-F-017; AC-018."""
    income = create_category(client, "income")
    expense = create_category(client, "expense")
    records = []
    for category, transaction_type, date in (
        (income, "income", "2026-10-10"),
        (expense, "expense", "2026-10-01"),
        (expense, "expense", "2026-09-30"),
    ):
        response = client.post(
            "/api/transactions",
            json=transaction_body(
                int(category["id"]), type=transaction_type, date=date
            ),
            headers=CLIENT_HEADERS,
        )
        assert response.status_code == 201
        records.append(response.json())
    queries = {
        "type": ({"type": "expense"}, [records[1], records[2]]),
        "category": ({"category_id": str(expense["id"])}, [records[1], records[2]]),
        "date": (
            {"date_from": "2026-10-01", "date_to": "2026-10-10"},
            [records[0], records[1]],
        ),
        "combined": (
            {
                "type": "expense",
                "category_id": str(expense["id"]),
                "date_from": "2026-10-01",
                "date_to": "2026-10-10",
            },
            [records[1]],
        ),
    }

    query, expected = queries[filter_kind]
    response = client.get("/api/transactions", params=query)

    assert response.status_code == 200
    assert response.json() == expected


def test_list_transactions_returns_empty_array_when_filters_do_not_match(
    client: TestClient,
) -> None:
    """API-P-007; REQ-F-020; AC-021."""
    category = create_category(client, "income")
    created = client.post(
        "/api/transactions",
        json=transaction_body(int(category["id"])),
        headers=CLIENT_HEADERS,
    )
    assert created.status_code == 201

    response = client.get("/api/transactions", params={"type": "expense"})

    assert response.status_code == 200
    assert response.json() == []


def test_search_transactions_uses_trimmed_unicode_casefold_substring(
    client: TestClient,
) -> None:
    """ADD-L5-P-001; ADD-L5-F-001; ADD-L5-AC-001, ADD-L5-AC-003."""
    category = create_category(client, "income")
    matching = create_transaction_record(
        client,
        category,
        transaction_type="income",
        date="2026-10-30",
        description="Нараховано щомісячну премію за жовтень",
    )
    create_transaction_record(
        client,
        category,
        transaction_type="income",
        date="2026-10-29",
        description="Основна заробітна плата",
    )

    response = client.get(
        "/api/transactions",
        params={"search": "  ПРЕМІЯ  "},
    )

    assert response.status_code == 200
    assert response.json() == [matching]


@pytest.mark.parametrize(
    ("search", "matching_description", "nonmatching_description"),
    [
        ("%", "Знижка 10%", "Знижка без відсотка"),
        ("_", "Позначка_витрати", "Позначка витрати"),
        ("$(whoami)", "Текст $(whoami) без виконання", "Звичайний текст"),
    ],
)
def test_search_transactions_treats_special_syntax_as_literal_text(
    client: TestClient,
    search: str,
    matching_description: str,
    nonmatching_description: str,
) -> None:
    """ADD-L5-B-003; ADD-L5-F-001; ADD-L5-AC-001."""
    category = create_category(client, "expense")
    matching = create_transaction_record(
        client,
        category,
        transaction_type="expense",
        date="2026-10-30",
        description=matching_description,
    )
    create_transaction_record(
        client,
        category,
        transaction_type="expense",
        date="2026-10-29",
        description=nonmatching_description,
    )

    response = client.get("/api/transactions", params={"search": search})

    assert response.status_code == 200
    assert response.json() == [matching]


@pytest.mark.parametrize("length", [1, 255])
def test_search_transactions_accepts_normalized_length_boundaries(
    client: TestClient,
    length: int,
) -> None:
    """ADD-L5-B-001; ADD-L5-F-001; ADD-L5-AC-004."""
    category = create_category(client, "income")
    search = "я" * length
    matching = create_transaction_record(
        client,
        category,
        transaction_type="income",
        date="2026-10-30",
        description=search,
    )

    response = client.get(
        "/api/transactions",
        params={"search": f"  {search}  "},
    )

    assert response.status_code == 200
    assert response.json() == [matching]


@pytest.mark.parametrize("search", ["", "   "])
def test_search_transactions_rejects_blank_normalized_value(
    client: TestClient,
    search: str,
) -> None:
    """ADD-L5-N-002; ADD-L5-F-001; ADD-L5-AC-003."""
    response = client.get("/api/transactions", params={"search": search})

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="search",
        expected_rule="non_blank",
    )


def test_search_transactions_rejects_value_longer_than_255_after_trim(
    client: TestClient,
) -> None:
    """ADD-L5-B-002; ADD-L5-F-001; ADD-L5-AC-004."""
    response = client.get(
        "/api/transactions",
        params={"search": f"  {'я' * 256}  "},
    )

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="search",
        expected_rule="max_length_255",
    )


def test_search_transactions_rejects_repeated_parameter(client: TestClient) -> None:
    """ADD-L5-N-003; ADD-L5-F-001; ADD-L5-AC-004."""
    response = client.get("/api/transactions?search=премія&search=бонус")

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="search",
        expected_rule="single_value",
    )


def test_search_transactions_returns_empty_for_no_match_and_null_description(
    client: TestClient,
) -> None:
    """ADD-L5-N-001; ADD-L5-F-001; ADD-L5-AC-001, ADD-L5-AC-003."""
    category = create_category(client, "income")
    create_transaction_record(
        client,
        category,
        transaction_type="income",
        date="2026-10-30",
        description=None,
    )
    create_transaction_record(
        client,
        category,
        transaction_type="income",
        date="2026-10-29",
        description="Заробітна плата",
    )

    response = client.get(
        "/api/transactions",
        params={"search": "відсутній підрядок"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_search_transactions_combines_with_existing_filters_using_and(
    client: TestClient,
) -> None:
    """ADD-L5-P-002; ADD-L5-F-001; ADD-L5-AC-002."""
    target_category = create_category(client, "expense")
    other_category = create_category(client, "expense")
    target = create_transaction_record(
        client,
        target_category,
        transaction_type="expense",
        date="2026-10-15",
        description="Щорічна премія",
    )
    create_transaction_record(
        client,
        target_category,
        transaction_type="expense",
        date="2026-09-30",
        description="Щорічна премія",
    )
    create_transaction_record(
        client,
        other_category,
        transaction_type="expense",
        date="2026-10-15",
        description="Щорічна премія",
    )
    create_transaction_record(
        client,
        target_category,
        transaction_type="expense",
        date="2026-10-15",
        description="Комунальні послуги",
    )

    response = client.get(
        "/api/transactions",
        params={
            "search": "ПРЕМІЯ",
            "type": "expense",
            "category_id": str(target_category["id"]),
            "date_from": "2026-10-01",
            "date_to": "2026-10-31",
        },
    )

    assert response.status_code == 200
    assert response.json() == [target]


def test_search_transactions_preserves_date_descending_sort(
    client: TestClient,
) -> None:
    """ADD-L5-F-001; ADD-L5-AC-002; REQ-F-016, AC-017."""
    category = create_category(client, "income")
    matching = [
        create_transaction_record(
            client,
            category,
            transaction_type="income",
            date=date,
            description=description,
        )
        for date, description in (
            ("2026-10-01", "Премія за вересень"),
            ("2026-10-30", "Премія за жовтень"),
            ("2026-10-15", "Додаткова премія"),
        )
    ]
    create_transaction_record(
        client,
        category,
        transaction_type="income",
        date="2026-10-31",
        description="Основна зарплата",
    )

    response = client.get(
        "/api/transactions",
        params={"search": "премія"},
    )

    assert response.status_code == 200
    assert response.json() == sorted(
        matching,
        key=lambda transaction: str(transaction["date"]),
        reverse=True,
    )


@pytest.mark.parametrize("transaction_id", ["0", "-1", "not-an-integer"])
def test_patch_transaction_rejects_invalid_id(
    client: TestClient,
    transaction_id: str,
) -> None:
    """API-N-026; REQ-F-008, REQ-NF-005; TransactionId contract."""
    response = client.patch(
        f"/api/transactions/{transaction_id}",
        json={"amount": "10.00"},
        headers=CLIENT_HEADERS,
    )

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="transaction_id",
    )


def test_patch_missing_transaction_returns_not_found(client: TestClient) -> None:
    """API-N-024; REQ-F-008."""
    response = client.patch(
        "/api/transactions/999",
        json={"amount": "10.00"},
        headers=CLIENT_HEADERS,
    )

    assert_error_response(
        response,
        expected_status=404,
        expected_code="RESOURCE_NOT_FOUND",
        expected_field="id",
        expected_rule="resource_exists",
    )


@pytest.mark.parametrize(
    "patch",
    [
        {"amount": "27500.00"},
        {"description": "Оновлений опис"},
        {"description": None},
        {"date": "2026-10-30"},
    ],
)
def test_patch_transaction_updates_only_supplied_fields_and_preserves_id(
    client: TestClient,
    patch: dict[str, object],
) -> None:
    """API-P-008; BDD-007; REQ-F-008; AC-008."""
    category = create_category(client, "income")
    original_body = transaction_body(
        int(category["id"]), description="Початковий опис"
    )
    created_response = client.post(
        "/api/transactions", json=original_body, headers=CLIENT_HEADERS
    )
    assert created_response.status_code == 201
    created = created_response.json()

    response = client.patch(
        f"/api/transactions/{created['id']}", json=patch, headers=CLIENT_HEADERS
    )

    expected = {**original_body, **patch}
    assert_transaction(
        response,
        expected=expected,
        expected_category_name=str(category["name"]),
        expected_status=200,
    )
    assert response.json()["id"] == created["id"]


def test_patch_transaction_can_change_type_with_matching_category(
    client: TestClient,
) -> None:
    """API-P-008; REQ-F-007, REQ-F-008; AC-007, AC-008."""
    income = create_category(client, "income")
    expense = create_category(client, "expense")
    original = transaction_body(int(income["id"]))
    created_response = client.post(
        "/api/transactions", json=original, headers=CLIENT_HEADERS
    )
    assert created_response.status_code == 201
    created = created_response.json()
    patch = {"type": "expense", "category_id": expense["id"]}

    response = client.patch(
        f"/api/transactions/{created['id']}", json=patch, headers=CLIENT_HEADERS
    )

    assert_transaction(
        response,
        expected={**original, **patch},
        expected_category_name=str(expense["name"]),
        expected_status=200,
    )
    assert response.json()["id"] == created["id"]


@pytest.mark.parametrize(
    ("patch", "expected_field"),
    [
        ({}, "body"),
        ({"type": None}, "type"),
        ({"type": "other"}, "type"),
        ({"amount": None}, "amount"),
        ({"amount": 10.0}, "amount"),
        ({"amount": "0.00"}, "amount"),
        ({"amount": "1.0"}, "amount"),
        ({"date": None}, "date"),
        ({"date": "2026-02-29"}, "date"),
        ({"category_id": None}, "category_id"),
        ({"category_id": 0}, "category_id"),
        ({"description": "О" * 256}, "description"),
        ({"id": 99}, "id"),
        ({"category_name": "Інша"}, "category_name"),
        ({"command": "noop"}, "command"),
    ],
)
def test_patch_transaction_rejects_invalid_body_without_changing_state(
    client: TestClient,
    patch: dict[str, object],
    expected_field: str,
) -> None:
    """API-N-022, API-N-023; BDD-007; REQ-F-008, REQ-NF-002, REQ-NF-005."""
    category = create_category(client, "income")
    original = transaction_body(int(category["id"]))
    created_response = client.post(
        "/api/transactions", json=original, headers=CLIENT_HEADERS
    )
    assert created_response.status_code == 201
    created = created_response.json()

    response = client.patch(
        f"/api/transactions/{created['id']}", json=patch, headers=CLIENT_HEADERS
    )

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field=expected_field,
    )
    listed = client.get("/api/transactions")
    assert listed.status_code == 200
    assert listed.json() == [created]


def test_patch_transaction_rejects_future_date_without_changing_state(
    client: TestClient,
) -> None:
    """REQ-F-005, REQ-F-008; AC-005, AC-008."""
    category = create_category(client, "income")
    original = transaction_body(int(category["id"]))
    created_response = client.post(
        "/api/transactions", json=original, headers=CLIENT_HEADERS
    )
    assert created_response.status_code == 201
    created = created_response.json()

    response = client.patch(
        f"/api/transactions/{created['id']}",
        json={"date": "2026-11-01"},
        headers=CLIENT_HEADERS,
    )

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="date",
        expected_rule="not_after_client_local_date",
    )
    assert client.get("/api/transactions").json() == [created]


def test_patch_transaction_rejects_category_type_mismatch(
    client: TestClient,
) -> None:
    """REQ-F-007, REQ-F-008; AC-007, AC-008."""
    income = create_category(client, "income")
    expense = create_category(client, "expense")
    original = transaction_body(int(income["id"]))
    created_response = client.post(
        "/api/transactions", json=original, headers=CLIENT_HEADERS
    )
    assert created_response.status_code == 201
    created = created_response.json()

    response = client.patch(
        f"/api/transactions/{created['id']}",
        json={"category_id": expense["id"]},
        headers=CLIENT_HEADERS,
    )

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="category_id",
        expected_rule="category_type_matches_transaction_type",
    )
    assert client.get("/api/transactions").json() == [created]


def test_patch_transaction_requires_client_local_date(client: TestClient) -> None:
    """REQ-F-005, REQ-F-008, REQ-NF-005; ClientLocalDate contract."""
    category = create_category(client, "income")
    original = transaction_body(int(category["id"]))
    created_response = client.post(
        "/api/transactions", json=original, headers=CLIENT_HEADERS
    )
    assert created_response.status_code == 201
    created = created_response.json()

    response = client.patch(
        f"/api/transactions/{created['id']}", json={"amount": "10.00"}
    )

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="X-Client-Local-Date",
    )
    assert client.get("/api/transactions").json() == [created]


def test_patch_transaction_rejects_missing_category(client: TestClient) -> None:
    """REQ-F-007, REQ-F-008; PATCH 404 contract."""
    category = create_category(client, "income")
    original = transaction_body(int(category["id"]))
    created_response = client.post(
        "/api/transactions", json=original, headers=CLIENT_HEADERS
    )
    assert created_response.status_code == 201
    created = created_response.json()

    response = client.patch(
        f"/api/transactions/{created['id']}",
        json={"category_id": 999},
        headers=CLIENT_HEADERS,
    )

    assert_error_response(
        response,
        expected_status=404,
        expected_code="RESOURCE_NOT_FOUND",
        expected_field="id",
        expected_rule="resource_exists",
    )
    assert client.get("/api/transactions").json() == [created]


def test_patch_transaction_description_with_code_syntax_is_plain_text(
    client: TestClient,
) -> None:
    """API-N-030; REQ-NF-004; AC-029."""
    category = create_category(client, "income")
    original = transaction_body(int(category["id"]))
    created_response = client.post(
        "/api/transactions", json=original, headers=CLIENT_HEADERS
    )
    assert created_response.status_code == 201
    created = created_response.json()
    description = "$(whoami); DROP TABLE transactions;"

    response = client.patch(
        f"/api/transactions/{created['id']}",
        json={"description": description},
        headers=CLIENT_HEADERS,
    )

    assert_transaction(
        response,
        expected={**original, "description": description},
        expected_category_name=str(category["name"]),
        expected_status=200,
    )


@pytest.mark.parametrize("transaction_id", ["0", "-1", "not-an-integer"])
def test_delete_transaction_rejects_invalid_id(
    client: TestClient,
    transaction_id: str,
) -> None:
    """API-N-026; REQ-F-009, REQ-NF-005."""
    response = client.delete(f"/api/transactions/{transaction_id}")

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="transaction_id",
    )


def test_delete_missing_transaction_returns_not_found(client: TestClient) -> None:
    """API-N-025; REQ-F-009."""
    response = client.delete("/api/transactions/999")

    assert_error_response(
        response,
        expected_status=404,
        expected_code="RESOURCE_NOT_FOUND",
        expected_field="id",
        expected_rule="resource_exists",
    )


def test_transaction_resource_rejects_unsupported_method(client: TestClient) -> None:
    """API-N-027; operation contract."""
    response = client.put("/api/transactions/1", json={"amount": "10.00"})

    assert_error_response(
        response,
        expected_status=405,
        expected_code="METHOD_NOT_ALLOWED",
    )


def test_delete_transaction_returns_no_content_and_removes_it_from_list(
    client: TestClient,
) -> None:
    """API-P-009; BDD-008; REQ-F-009; AC-009."""
    category = create_category(client, "expense")
    created_response = client.post(
        "/api/transactions",
        json=transaction_body(int(category["id"]), type="expense"),
        headers=CLIENT_HEADERS,
    )
    assert created_response.status_code == 201
    created = created_response.json()

    response = client.delete(f"/api/transactions/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    listed = client.get("/api/transactions")
    assert listed.status_code == 200
    assert listed.json() == []


def test_repeated_delete_transaction_returns_not_found(client: TestClient) -> None:
    """API-N-025; DELETE operation contract."""
    category = create_category(client, "income")
    created_response = client.post(
        "/api/transactions",
        json=transaction_body(int(category["id"])),
        headers=CLIENT_HEADERS,
    )
    assert created_response.status_code == 201
    transaction_id = created_response.json()["id"]
    first = client.delete(f"/api/transactions/{transaction_id}")
    assert first.status_code == 204

    response = client.delete(f"/api/transactions/{transaction_id}")

    assert_error_response(
        response,
        expected_status=404,
        expected_code="RESOURCE_NOT_FOUND",
        expected_field="id",
        expected_rule="resource_exists",
    )


def remove_sqlite_artifacts(database_path: Path, log_path: Path) -> None:
    for path in (
        database_path,
        database_path.with_name(f"{database_path.name}-wal"),
        database_path.with_name(f"{database_path.name}-shm"),
        log_path,
    ):
        path.unlink(missing_ok=True)


def test_transaction_mutations_persist_after_app_restart() -> None:
    """API-P-011; REQ-F-001, REQ-NF-001; AC-001, AC-026."""
    test_id = uuid4().hex
    database_path = Path.cwd() / f".category-test-restart-{test_id}.sqlite3"
    log_path = Path.cwd() / f".category-test-restart-{test_id}.log"
    try:
        with TestClient(create_app(database_path, log_path)) as first_client:
            category = create_category(first_client, "income")
            first = first_client.post(
                "/api/transactions",
                json=transaction_body(int(category["id"]), amount="100.00"),
                headers=CLIENT_HEADERS,
            )
            second = first_client.post(
                "/api/transactions",
                json=transaction_body(int(category["id"]), amount="200.00"),
                headers=CLIENT_HEADERS,
            )
            assert first.status_code == 201
            assert second.status_code == 201
            updated = first_client.patch(
                f"/api/transactions/{first.json()['id']}",
                json={"amount": "125.00"},
                headers=CLIENT_HEADERS,
            )
            deleted = first_client.delete(
                f"/api/transactions/{second.json()['id']}"
            )
            assert updated.status_code == 200
            assert deleted.status_code == 204
            expected = [updated.json()]

        with TestClient(create_app(database_path, log_path)) as restarted_client:
            response = restarted_client.get("/api/transactions")

        assert response.status_code == 200
        assert response.json() == expected
    finally:
        remove_sqlite_artifacts(database_path, log_path)


def test_unreadable_transaction_database_returns_data_read_error() -> None:
    """API-N-028; REQ-NF-003; AC-028."""
    test_id = uuid4().hex
    database_path = Path.cwd() / f".category-test-corrupt-{test_id}.sqlite3"
    log_path = Path.cwd() / f".category-test-corrupt-{test_id}.log"
    try:
        with TestClient(create_app(database_path, log_path)) as test_client:
            database_path.write_bytes(b"not a sqlite database")
            corrupted = database_path.read_bytes()

            response = test_client.get("/api/transactions")

            assert_error_response(
                response,
                expected_status=500,
                expected_code="DATA_READ_ERROR",
            )
            assert database_path.read_bytes() == corrupted
    finally:
        remove_sqlite_artifacts(database_path, log_path)


@pytest.mark.parametrize("operation", ["post", "patch", "delete"])
def test_transaction_write_failure_rolls_back_entire_operation(
    client: TestClient,
    operation: str,
) -> None:
    """API-N-029; REQ-NF-002; AC-027."""
    category = create_category(client, "income")
    created = client.post(
        "/api/transactions",
        json=transaction_body(int(category["id"]), amount="100.00"),
        headers=CLIENT_HEADERS,
    )
    assert created.status_code == 201
    before = client.get("/api/transactions").json()

    def fail_before_commit() -> None:
        raise sqlite3.OperationalError("controlled pre-commit failure")

    repository = client.app.state.transaction_repository
    repository.before_commit = fail_before_commit
    try:
        if operation == "post":
            response = client.post(
                "/api/transactions",
                json=transaction_body(int(category["id"]), amount="200.00"),
                headers=CLIENT_HEADERS,
            )
        elif operation == "patch":
            response = client.patch(
                f"/api/transactions/{created.json()['id']}",
                json={"amount": "200.00"},
                headers=CLIENT_HEADERS,
            )
        else:
            response = client.delete(
                f"/api/transactions/{created.json()['id']}"
            )
    finally:
        repository.before_commit = lambda: None

    assert_error_response(
        response,
        expected_status=500,
        expected_code="DATA_WRITE_ERROR",
    )
    after = client.get("/api/transactions")
    assert after.status_code == 200
    assert after.json() == before
