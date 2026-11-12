from typing import Annotated, Literal

from fastapi import APIRouter, Header, Path, Request, Response, status
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)

from src.api.contract import (
    BAD_REQUEST,
    INTERNAL_SERVER_ERROR,
    METHOD_NOT_ALLOWED,
    NOT_FOUND,
    TRANSACTION_FILTER_PARAMETERS,
    TRANSACTION_FILTER_VALIDATION_ERROR,
    UNSUPPORTED_MEDIA_TYPE,
    VALIDATION_ERROR,
)
from src.services.transactions import TransactionService, TransactionValidationError


router = APIRouter(tags=["Transactions"])

Amount = Annotated[
    str,
    Field(pattern=r"^(?:0\.(?:0[1-9]|[1-9][0-9])|[1-9][0-9]*\.[0-9]{2})$"),
]
Description = Annotated[str, Field(max_length=255)]
PositiveId = Annotated[StrictInt, Field(ge=1)]


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["income", "expense"]
    amount: Amount
    date: str
    category_id: PositiveId
    description: Description | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: int
    type: Literal["income", "expense"]
    amount: str
    date: str
    category_id: int
    category_name: str
    description: str | None


class TransactionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["income", "expense"] | None = None
    amount: Amount | None = None
    date: str | None = None
    category_id: PositiveId | None = None
    description: Description | None = None

    @model_validator(mode="before")
    @classmethod
    def require_property(cls, value: object) -> object:
        if isinstance(value, dict) and not value:
            raise ValueError("Patch повинен містити принаймні одне поле")
        return value

    @field_validator("type", "amount", "date", "category_id", mode="before")
    @classmethod
    def reject_null_except_description(cls, value: object) -> object:
        if value is None:
            raise ValueError("null дозволений лише для description")
        return value


def transaction_filters(
    request: Request,
) -> tuple[str | None, int | None, str | None, str | None, str | None]:
    allowed = {"type", "category_id", "date_from", "date_to", "search"}
    for key in request.query_params:
        if key not in allowed:
            raise TransactionValidationError(
                "Невідомий query parameter.", key, "known_query_parameter_only"
            )
        if len(request.query_params.getlist(key)) != 1:
            raise TransactionValidationError(
                "Query parameter не можна повторювати.", key, "single_value"
            )

    transaction_type = request.query_params.get("type")
    if transaction_type not in {None, "income", "expense"}:
        raise TransactionValidationError(
            "Поле type має недозволене значення.", "type", "allowed_value"
        )

    raw_category_id = request.query_params.get("category_id")
    category_id: int | None = None
    if raw_category_id is not None:
        try:
            category_id = int(raw_category_id)
        except ValueError as exception:
            raise TransactionValidationError(
                "Поле category_id повинно бути додатним цілим числом.",
                "category_id",
                "positive_integer",
            ) from exception
        if category_id < 1 or str(category_id) != raw_category_id:
            raise TransactionValidationError(
                "Поле category_id повинно бути додатним цілим числом.",
                "category_id",
                "positive_integer",
            )

    raw_search = request.query_params.get("search")
    search: str | None = None
    if raw_search is not None:
        search = raw_search.strip()
        if not search:
            raise TransactionValidationError(
                "Параметр search після видалення крайніх пробілів не може бути порожнім.",
                "search",
                "non_blank",
            )
        if len(search) > 255:
            raise TransactionValidationError(
                "Параметр search після видалення крайніх пробілів не може містити понад 255 символів.",
                "search",
                "max_length_255",
            )
    return (
        transaction_type,
        category_id,
        request.query_params.get("date_from"),
        request.query_params.get("date_to"),
        search,
    )


@router.post(
    "/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createTransaction",
    responses={
        400: BAD_REQUEST,
        404: NOT_FOUND,
        405: METHOD_NOT_ALLOWED,
        415: UNSUPPORTED_MEDIA_TYPE,
        422: VALIDATION_ERROR,
        500: INTERNAL_SERVER_ERROR,
    },
)
def create_transaction(
    payload: TransactionCreate,
    request: Request,
    client_local_date: Annotated[
        str,
        Header(alias="X-Client-Local-Date"),
    ],
) -> TransactionResponse:
    service: TransactionService = request.app.state.transaction_service
    transaction = service.create(
        transaction_type=payload.type,
        amount=payload.amount,
        transaction_date=payload.date,
        category_id=payload.category_id,
        description=payload.description,
        client_local_date=client_local_date,
    )
    return TransactionResponse(**transaction)


@router.get(
    "/transactions",
    response_model=list[TransactionResponse],
    operation_id="listTransactions",
    responses={
        405: METHOD_NOT_ALLOWED,
        422: TRANSACTION_FILTER_VALIDATION_ERROR,
        500: INTERNAL_SERVER_ERROR,
    },
    openapi_extra={
        "parameters": TRANSACTION_FILTER_PARAMETERS,
        "x-req-ids": [
            "REQ-F-002",
            "REQ-F-015",
            "REQ-F-016",
            "REQ-F-017",
            "REQ-F-018",
            "REQ-F-019",
            "REQ-F-020",
            "REQ-NF-003",
            "REQ-NF-006",
            "ADD-L5-F-001",
        ],
    },
)
def list_transactions(request: Request) -> list[TransactionResponse]:
    service: TransactionService = request.app.state.transaction_service
    transaction_type, category_id, date_from, date_to, search = transaction_filters(
        request
    )
    return [
        TransactionResponse(**transaction)
        for transaction in service.list_all(
            transaction_type=transaction_type,
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
        )
    ]


@router.patch(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
    operation_id="updateTransaction",
    responses={
        400: BAD_REQUEST,
        404: NOT_FOUND,
        405: METHOD_NOT_ALLOWED,
        415: UNSUPPORTED_MEDIA_TYPE,
        422: VALIDATION_ERROR,
        500: INTERNAL_SERVER_ERROR,
    },
)
def update_transaction(
    payload: TransactionPatch,
    request: Request,
    transaction_id: Annotated[int, Path(ge=1)],
    client_local_date: Annotated[
        str,
        Header(alias="X-Client-Local-Date"),
    ],
) -> TransactionResponse:
    service: TransactionService = request.app.state.transaction_service
    transaction = service.update(
        transaction_id,
        payload.model_dump(exclude_unset=True),
        client_local_date,
    )
    return TransactionResponse(**transaction)


@router.delete(
    "/transactions/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteTransaction",
    responses={
        404: NOT_FOUND,
        405: METHOD_NOT_ALLOWED,
        422: VALIDATION_ERROR,
        500: INTERNAL_SERVER_ERROR,
    },
)
def delete_transaction(
    request: Request,
    transaction_id: Annotated[int, Path(ge=1)],
) -> Response:
    service: TransactionService = request.app.state.transaction_service
    service.delete(transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
