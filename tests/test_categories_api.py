from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    test_id = uuid4().hex
    database_path = Path.cwd() / f".category-test-{test_id}.sqlite3"
    log_path = Path.cwd() / f".category-test-{test_id}.log"
    try:
        with TestClient(create_app(database_path, log_path)) as test_client:
            yield test_client
    finally:
        database_path.unlink(missing_ok=True)
        log_path.unlink(missing_ok=True)


def unique_name(prefix: str = "Категорія") -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def unique_name_of_length(length: int) -> str:
    seed = uuid4().hex
    return (seed * ((length // len(seed)) + 1))[:length]


NAME_50 = unique_name_of_length(50)
TRIMMED_NAME = unique_name("Відсотки")
NAME_1 = chr(0x4E00 + (uuid4().int % 20_992))


def assert_category(
    response,
    *,
    expected_name: str,
    expected_type: str,
    expected_status: int = 201,
) -> int:
    assert response.status_code == expected_status
    body = response.json()
    assert set(body) == {"id", "name", "type"}
    assert isinstance(body["id"], int) and not isinstance(body["id"], bool)
    assert body["id"] >= 1
    assert body["name"] == expected_name
    assert body["type"] == expected_type
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


def test_create_category_returns_openapi_category(client: TestClient) -> None:
    """API-P-001; REQ-F-001, REQ-F-010, REQ-F-011, REQ-NF-001."""
    name = unique_name("Премія")
    response = client.post(
        "/api/categories",
        json={"name": name, "type": "income"},
    )

    assert_category(response, expected_name=name, expected_type="income")


@pytest.mark.parametrize(
    ("raw_name", "expected_name", "category_type"),
    [
        (NAME_1, NAME_1, "income"),
        (NAME_50, NAME_50, "expense"),
        (f"  {TRIMMED_NAME}  ", TRIMMED_NAME, "income"),
    ],
)
def test_create_category_accepts_name_boundaries_and_normalizes_whitespace(
    client: TestClient,
    raw_name: str,
    expected_name: str,
    category_type: str,
) -> None:
    """REQ-F-010, REQ-F-011; AC-010, AC-011."""
    response = client.post(
        "/api/categories",
        json={"name": raw_name, "type": category_type},
    )

    assert_category(
        response,
        expected_name=expected_name,
        expected_type=category_type,
    )


def test_create_categories_assigns_unique_positive_ids(client: TestClient) -> None:
    """API-P-001; REQ-F-010; AC-010."""
    first_name = unique_name("Перша")
    second_name = unique_name("Друга")

    first_id = assert_category(
        client.post(
            "/api/categories",
            json={"name": first_name, "type": "income"},
        ),
        expected_name=first_name,
        expected_type="income",
    )
    second_id = assert_category(
        client.post(
            "/api/categories",
            json={"name": second_name, "type": "expense"},
        ),
        expected_name=second_name,
        expected_type="expense",
    )

    assert first_id != second_id


def test_same_normalized_name_is_allowed_for_different_types(
    client: TestClient,
) -> None:
    """BDD-002; REQ-F-011; AC-012."""
    name = unique_name("Спільна")

    assert_category(
        client.post(
            "/api/categories",
            json={"name": name, "type": "expense"},
        ),
        expected_name=name,
        expected_type="expense",
    )
    assert_category(
        client.post(
            "/api/categories",
            json={"name": f"  {name}  ", "type": "income"},
        ),
        expected_name=name,
        expected_type="income",
    )


def test_duplicate_name_within_type_is_case_insensitive_after_trim(
    client: TestClient,
) -> None:
    """API-N-005; BDD-002; REQ-F-011; AC-012."""
    name = unique_name("Дублікат")
    assert_category(
        client.post(
            "/api/categories",
            json={"name": name, "type": "income"},
        ),
        expected_name=name,
        expected_type="income",
    )

    response = client.post(
        "/api/categories",
        json={"name": f"  {name.swapcase()}  ", "type": "income"},
    )

    assert_error_response(
        response,
        expected_status=409,
        expected_code="CATEGORY_NAME_CONFLICT",
        expected_field="name",
        expected_rule="unique_case_insensitive_within_type",
    )


@pytest.mark.parametrize(
    ("body", "expected_field"),
    [
        ({"type": "income"}, "name"),
        ({"name": "Без типу"}, "type"),
        ({"name": None, "type": "income"}, "name"),
        ({"name": "Неправильний тип", "type": None}, "type"),
        ({"name": "", "type": "income"}, "name"),
        ({"name": "   ", "type": "income"}, "name"),
        ({"name": "Г" * 51, "type": "expense"}, "name"),
        ({"name": "Інше", "type": "other"}, "type"),
        ({"name": "Зайве поле", "type": "income", "command": "noop"}, "command"),
    ],
)
def test_invalid_category_body_returns_validation_error(
    client: TestClient,
    body: dict[str, object],
    expected_field: str,
) -> None:
    """API-N-002, API-N-003, API-N-004; REQ-F-010, REQ-F-011, REQ-NF-005."""
    response = client.post("/api/categories", json=body)

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field=expected_field,
    )


def test_malformed_json_returns_contract_error(client: TestClient) -> None:
    """API-N-001; REQ-NF-005."""
    response = client.post(
        "/api/categories",
        content=b'{"name":"\xd0\x87\xd0\xb6\xd0\xb0"',
        headers={"Content-Type": "application/json"},
    )

    assert_error_response(
        response,
        expected_status=400,
        expected_code="MALFORMED_JSON",
    )


def test_non_json_content_type_returns_contract_error(client: TestClient) -> None:
    """API-N-006; REQ-NF-005."""
    response = client.post(
        "/api/categories",
        content='{"name":"Їжа","type":"expense"}',
        headers={"Content-Type": "text/plain"},
    )

    assert_error_response(
        response,
        expected_status=415,
        expected_code="UNSUPPORTED_MEDIA_TYPE",
        expected_field="Content-Type",
        expected_rule="application_json_media_type",
    )


def test_category_name_with_code_syntax_is_plain_text(client: TestClient) -> None:
    """API-N-030; REQ-NF-004."""
    name = unique_name("$(whoami)")
    response = client.post(
        "/api/categories",
        json={"name": name, "type": "expense"},
    )

    assert_category(response, expected_name=name, expected_type="expense")


def test_list_categories_returns_empty_array(client: TestClient) -> None:
    """API-P-002; REQ-F-012, REQ-NF-003, REQ-NF-006."""
    response = client.get("/api/categories")

    assert response.status_code == 200
    assert response.json() == []


def test_list_categories_returns_all_created_categories(client: TestClient) -> None:
    """API-P-002; BDD-001; REQ-F-012; AC-013."""
    income_name = unique_name("Дохід")
    expense_name = unique_name("Витрата")
    income = client.post(
        "/api/categories",
        json={"name": income_name, "type": "income"},
    ).json()
    expense = client.post(
        "/api/categories",
        json={"name": expense_name, "type": "expense"},
    ).json()

    response = client.get("/api/categories")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert {category["id"]: category for category in body} == {
        income["id"]: income,
        expense["id"]: expense,
    }


def test_rename_category_returns_full_category_without_changing_id_or_type(
    client: TestClient,
) -> None:
    """API-P-003; BDD-003; REQ-F-001, REQ-F-011, REQ-F-013; AC-014."""
    original_name = unique_name("Продукти")
    created = client.post(
        "/api/categories",
        json={"name": original_name, "type": "expense"},
    ).json()
    new_name = unique_name("Харчування")

    response = client.patch(
        f"/api/categories/{created['id']}",
        json={"name": f"  {new_name}  "},
    )

    assert_category(
        response,
        expected_name=new_name,
        expected_type="expense",
        expected_status=200,
    )
    assert response.json()["id"] == created["id"]


@pytest.mark.parametrize("category_id", ["0", "-1", "not-an-integer"])
def test_rename_category_rejects_invalid_id(
    client: TestClient,
    category_id: str,
) -> None:
    """REQ-F-013, REQ-NF-005; CategoryId contract."""
    response = client.patch(
        f"/api/categories/{category_id}",
        json={"name": "Нова назва"},
    )

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="category_id",
    )


def test_rename_missing_category_returns_not_found(client: TestClient) -> None:
    """API-N-007; REQ-F-013."""
    response = client.patch(
        "/api/categories/999",
        json={"name": "Нова назва"},
    )

    assert_error_response(
        response,
        expected_status=404,
        expected_code="RESOURCE_NOT_FOUND",
        expected_field="id",
        expected_rule="resource_exists",
    )


@pytest.mark.parametrize(
    ("body", "expected_field"),
    [
        ({}, "name"),
        ({"name": None}, "name"),
        ({"name": ""}, "name"),
        ({"name": "   "}, "name"),
        ({"name": "Д" * 51}, "name"),
        ({"type": "income"}, {"name", "type"}),
        ({"name": "Назва", "type": "expense"}, "type"),
    ],
)
def test_rename_category_rejects_invalid_body(
    client: TestClient,
    body: dict[str, object],
    expected_field: str | set[str],
) -> None:
    """API-N-008; REQ-F-011, REQ-F-013, REQ-NF-005; AC-014."""
    created = client.post(
        "/api/categories",
        json={"name": unique_name("Для редагування"), "type": "income"},
    ).json()

    response = client.patch(f"/api/categories/{created['id']}", json=body)

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field=expected_field,
    )


def test_rename_category_rejects_name_conflict(client: TestClient) -> None:
    """REQ-F-011, REQ-F-013, REQ-NF-005; AC-012, AC-014."""
    existing_name = unique_name("Наявна")
    existing = client.post(
        "/api/categories",
        json={"name": existing_name, "type": "income"},
    ).json()
    target = client.post(
        "/api/categories",
        json={"name": unique_name("Цільова"), "type": "income"},
    ).json()
    assert existing["id"] != target["id"]

    response = client.patch(
        f"/api/categories/{target['id']}",
        json={"name": f"  {existing_name.swapcase()}  "},
    )

    assert_error_response(
        response,
        expected_status=409,
        expected_code="CATEGORY_NAME_CONFLICT",
        expected_field="name",
        expected_rule="unique_case_insensitive_within_type",
    )


@pytest.mark.parametrize("category_id", ["0", "-1", "not-an-integer"])
def test_delete_category_rejects_invalid_id(
    client: TestClient,
    category_id: str,
) -> None:
    """API-N-026; REQ-F-014, REQ-NF-005."""
    response = client.delete(f"/api/categories/{category_id}")

    assert_error_response(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
        expected_field="category_id",
    )


def test_delete_unused_category_returns_no_content(client: TestClient) -> None:
    """API-P-004; BDD-004; REQ-F-001, REQ-F-014, REQ-NF-001; AC-015."""
    created = client.post(
        "/api/categories",
        json={"name": unique_name("Подорожі"), "type": "expense"},
    ).json()

    response = client.delete(f"/api/categories/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_category_returns_not_found(client: TestClient) -> None:
    """API-N-010; REQ-F-014."""
    response = client.delete("/api/categories/999")

    assert_error_response(
        response,
        expected_status=404,
        expected_code="RESOURCE_NOT_FOUND",
        expected_field="id",
        expected_rule="resource_exists",
    )


@pytest.mark.skip(reason="Blocked: requires POST Transaction and isolated SQLite")
def test_delete_used_category_returns_conflict(client: TestClient) -> None:
    """API-N-009; BDD-004; REQ-F-014; AC-015."""
    response = client.delete("/api/categories/2")

    assert_error_response(
        response,
        expected_status=409,
        expected_code="CATEGORY_IN_USE",
    )


def test_repeated_delete_returns_not_found(client: TestClient) -> None:
    """REQ-F-014; DELETE operation contract."""
    created = client.post(
        "/api/categories",
        json={"name": unique_name("Одноразова"), "type": "expense"},
    ).json()
    first_response = client.delete(f"/api/categories/{created['id']}")
    assert first_response.status_code == 204

    second_response = client.delete(f"/api/categories/{created['id']}")

    assert_error_response(
        second_response,
        expected_status=404,
        expected_code="RESOURCE_NOT_FOUND",
        expected_field="id",
        expected_rule="resource_exists",
    )
