from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ApiErrorCode(str, Enum):
    MALFORMED_JSON = "MALFORMED_JSON"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CATEGORY_NAME_CONFLICT = "CATEGORY_NAME_CONFLICT"
    CATEGORY_IN_USE = "CATEGORY_IN_USE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DATA_READ_ERROR = "DATA_READ_ERROR"
    DATA_WRITE_ERROR = "DATA_WRITE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "field і rule обов’язкові разом для помилки конкретного поля. "
                "Залежність їх спільної присутності документована, але не може "
                "бути надійно виражена без ускладнення OpenAPI 3.0.3."
            ),
            "properties": {
                "code": {"$ref": "#/components/schemas/ApiErrorCode"},
                "message": {"type": "string", "minLength": 1},
                "field": {"type": "string", "minLength": 1},
                "rule": {"type": "string", "minLength": 1},
            },
        },
    )

    code: ApiErrorCode
    message: str = Field(min_length=1)
    field: str | None = Field(default=None, min_length=1)
    rule: str | None = Field(default=None, min_length=1)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


BAD_REQUEST = {
    "model": ErrorResponse,
    "description": "Request body не є коректним JSON",
}
NOT_FOUND = {
    "model": ErrorResponse,
    "description": "Потрібний ресурс не існує",
}
METHOD_NOT_ALLOWED = {
    "model": ErrorResponse,
    "description": "Метод не підтримується для URI",
}
UNSUPPORTED_MEDIA_TYPE = {
    "model": ErrorResponse,
    "description": "Request body не використовує application/json",
}
VALIDATION_ERROR = {
    "model": ErrorResponse,
    "description": "Параметр або body порушує контракт чи доменне правило",
}
INTERNAL_SERVER_ERROR = {
    "model": ErrorResponse,
    "description": "Дані неможливо прочитати або стійко змінити",
}

CATEGORY_CREATE_CONFLICT = {
    "model": ErrorResponse,
    "description": (
        "Назва Category конфліктує з наявною Category того самого типу"
    ),
}
CATEGORY_RENAME_CONFLICT = {
    "model": ErrorResponse,
    "description": (
        "Нова назва конфліктує з іншою Category того самого типу"
    ),
}
CATEGORY_IN_USE = {
    "model": ErrorResponse,
    "description": "Category використовується Transaction і не видалена",
}


TRANSACTION_FILTER_PARAMETERS = [
    {
        "name": "type",
        "in": "query",
        "required": False,
        "description": "Filter за Transaction Type",
        "schema": {"type": "string", "enum": ["income", "expense"]},
    },
    {
        "name": "category_id",
        "in": "query",
        "required": False,
        "description": (
            "Filter за Category; коректний неіснуючий ID дає порожній список"
        ),
        "schema": {"type": "integer", "format": "int64", "minimum": 1},
    },
    {
        "name": "date_from",
        "in": "query",
        "required": False,
        "description": (
            "Включна початкова межа Date Range; використовується разом із date_to"
        ),
        "schema": {
            "type": "string",
            "format": "date",
            "pattern": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
            "description": (
                "Реальна календарна дата YYYY-MM-DD. Існування дати "
                "перевіряється семантично."
            ),
        },
    },
    {
        "name": "date_to",
        "in": "query",
        "required": False,
        "description": (
            "Включна кінцева межа Date Range; використовується разом із date_from"
        ),
        "schema": {
            "type": "string",
            "format": "date",
            "pattern": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
            "description": (
                "Реальна календарна дата YYYY-MM-DD. Існування дати "
                "перевіряється семантично."
            ),
        },
    },
]
