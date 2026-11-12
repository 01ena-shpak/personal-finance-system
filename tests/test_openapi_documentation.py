import json
from pathlib import Path
from urllib.parse import urlparse

from src.main import app


APPROVED_SPEC_PATH = Path(__file__).parents[1] / "spec" / "openapi.json"
HTTP_METHODS = {"get", "post", "patch", "delete"}


def load_approved_spec() -> dict[str, object]:
    with APPROVED_SPEC_PATH.open(encoding="utf-8") as spec_file:
        return json.load(spec_file)


def resolve_local_ref(document: dict[str, object], value: dict[str, object]) -> dict[str, object]:
    if "$ref" not in value:
        return value

    resolved: object = document
    for part in value["$ref"].removeprefix("#/").split("/"):
        resolved = resolved[part]  # type: ignore[index]
    return resolved  # type: ignore[return-value]


def approved_operations() -> list[tuple[str, str, dict[str, object]]]:
    approved = load_approved_spec()
    server_path = urlparse(approved["servers"][0]["url"]).path.rstrip("/")
    operations = []
    for path, path_item in approved["paths"].items():
        for method, operation in path_item.items():
            if method in HTTP_METHODS:
                operations.append((server_path + path, method, operation))
    return operations


def test_generated_openapi_documents_approved_response_statuses() -> None:
    generated = app.openapi()

    for path, method, approved_operation in approved_operations():
        actual_responses = generated["paths"][path][method]["responses"]
        assert set(actual_responses) == set(approved_operation["responses"]), (
            f"{method.upper()} {path} response statuses differ"
        )


def test_generated_openapi_uses_error_response_for_all_errors() -> None:
    approved = load_approved_spec()
    generated = app.openapi()

    for path, method, approved_operation in approved_operations():
        for status_code, approved_response_ref in approved_operation["responses"].items():
            if int(status_code) < 400:
                continue
            approved_response = resolve_local_ref(approved, approved_response_ref)
            actual_response = generated["paths"][path][method]["responses"][status_code]
            schema = actual_response["content"]["application/json"]["schema"]
            assert schema == {"$ref": "#/components/schemas/ErrorResponse"}, (
                f"{method.upper()} {path} {status_code} must use ErrorResponse"
            )
            assert actual_response["description"] == approved_response["description"]

    for schema_name in ("ApiErrorCode", "ErrorDetail", "ErrorResponse"):
        approved_schema = approved["components"]["schemas"][schema_name]
        actual_schema = generated["components"]["schemas"][schema_name]
        for key, value in approved_schema.items():
            assert actual_schema[key] == value, f"{schema_name}.{key} differs"


def test_generated_openapi_documents_transaction_query_parameters() -> None:
    approved = load_approved_spec()
    generated = app.openapi()
    approved_parameters = approved["paths"]["/transactions"]["get"]["parameters"]
    actual_parameters = generated["paths"]["/api/transactions"]["get"]["parameters"]

    expected = {}
    for parameter_ref in approved_parameters:
        parameter = resolve_local_ref(approved, parameter_ref)
        expected[parameter["name"]] = {
            "in": parameter["in"],
            "required": parameter["required"],
            "description": parameter["description"],
            "schema": resolve_local_ref(approved, parameter["schema"]),
        }

    actual = {
        parameter["name"]: {
            "in": parameter["in"],
            "required": parameter.get("required", False),
            "description": parameter["description"],
            "schema": parameter["schema"],
        }
        for parameter in actual_parameters
        if parameter["in"] == "query"
    }
    assert actual == expected


def test_generated_openapi_documents_search_validation_rules() -> None:
    approved = load_approved_spec()
    generated = app.openapi()
    approved_response_ref = approved["paths"]["/transactions"]["get"]["responses"][
        "422"
    ]
    approved_response = resolve_local_ref(approved, approved_response_ref)
    approved_examples = approved_response["content"]["application/json"]["examples"]
    expected_rules = {
        example["value"]["error"]["rule"]
        for name, example in approved_examples.items()
        if name in {"blankSearch", "searchTooLong", "repeatedSearch"}
    }
    actual_response = generated["paths"]["/api/transactions"]["get"]["responses"][
        "422"
    ]
    actual_examples = actual_response["content"]["application/json"].get(
        "examples", {}
    )
    actual_rules = {
        example["value"]["error"]["rule"] for example in actual_examples.values()
    }

    assert expected_rules == {"non_blank", "max_length_255", "single_value"}
    assert expected_rules <= actual_rules
