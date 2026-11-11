from contextlib import asynccontextmanager
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.categories import router as categories_router
from src.repositories.categories import CategoryRepository
from src.services.categories import (
    CategoryConflictError,
    CategoryService,
    CategoryValidationError,
    DataWriteError,
)


LOGGER = logging.getLogger("personal_finance")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def is_valid_json_content_type(content_type: str) -> bool:
    parts = [part.strip() for part in content_type.split(";")]
    if not parts or parts[0].lower() != "application/json":
        return False
    for parameter in parts[1:]:
        if "=" not in parameter:
            return False
        key, value = parameter.split("=", 1)
        if not key.strip() or not value.strip():
            return False
    return True


def error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    field: str | None = None,
    rule: str | None = None,
) -> JSONResponse:
    detail: dict[str, str] = {"code": code, "message": message}
    if field is not None and rule is not None:
        detail.update(field=field, rule=rule)
    return JSONResponse(status_code=status_code, content={"error": detail})


def validation_rule(error_type: str) -> str:
    return {
        "missing": "required",
        "extra_forbidden": "known_field_only",
        "literal_error": "allowed_value",
        "string_type": "string_type",
    }.get(error_type, "valid_value")


def create_app(
    database_path: str | Path = "data/personal_finance.sqlite3",
    log_path: str | Path = "logs/app.log",
) -> FastAPI:
    repository = CategoryRepository(Path(database_path))
    service = CategoryService(repository)
    application_log_path = Path(log_path)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        application_log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            application_log_path,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        LOGGER.addHandler(file_handler)
        try:
            repository.initialize()
            LOGGER.info("database_initialized")
            yield
        finally:
            LOGGER.removeHandler(file_handler)
            file_handler.close()

    application = FastAPI(
        title="Personal Finance System REST API",
        lifespan=lifespan,
    )
    application.state.category_service = service

    @application.middleware("http")
    async def request_logging_and_content_type(request: Request, call_next):
        LOGGER.info("request_started method=%s path=%s", request.method, request.url.path)
        if request.method in {"POST", "PATCH"} and request.url.path.startswith(
            "/api/categories"
        ):
            content_type = request.headers.get("content-type", "")
            if not is_valid_json_content_type(content_type):
                LOGGER.warning(
                    "request_rejected method=%s path=%s reason=unsupported_media_type",
                    request.method,
                    request.url.path,
                )
                LOGGER.info(
                    "request_finished method=%s path=%s status=415",
                    request.method,
                    request.url.path,
                )
                return error_response(
                    415,
                    "UNSUPPORTED_MEDIA_TYPE",
                    "Request body повинен використовувати медіатип application/json.",
                    field="Content-Type",
                    rule="application_json_media_type",
                )

        response = await call_next(request)
        LOGGER.info(
            "request_finished method=%s path=%s status=%s",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response

    @application.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request,
        exception: RequestValidationError,
    ) -> JSONResponse:
        error = exception.errors()[0]
        if error["type"] == "json_invalid":
            LOGGER.warning("request_invalid_json path=%s", request.url.path)
            return error_response(
                400,
                "MALFORMED_JSON",
                "Request body не є синтаксично коректним JSON.",
            )

        location = error.get("loc", ())
        field = str(location[-1]) if location else "body"
        LOGGER.warning(
            "request_validation_failed path=%s field=%s type=%s",
            request.url.path,
            field,
            error["type"],
        )
        return error_response(
            422,
            "VALIDATION_ERROR",
            f"Поле {field} порушує правило перевірки.",
            field=field,
            rule=validation_rule(error["type"]),
        )

    @application.exception_handler(CategoryValidationError)
    async def category_validation_handler(
        request: Request,
        exception: CategoryValidationError,
    ) -> JSONResponse:
        LOGGER.warning(
            "category_validation_failed path=%s field=%s rule=%s",
            request.url.path,
            exception.field,
            exception.rule,
        )
        return error_response(
            422,
            "VALIDATION_ERROR",
            exception.message,
            field=exception.field,
            rule=exception.rule,
        )

    @application.exception_handler(CategoryConflictError)
    async def category_conflict_handler(
        request: Request,
        exception: CategoryConflictError,
    ) -> JSONResponse:
        LOGGER.warning("category_name_conflict path=%s", request.url.path)
        return error_response(
            409,
            "CATEGORY_NAME_CONFLICT",
            str(exception),
            field="name",
            rule="unique_case_insensitive_within_type",
        )

    @application.exception_handler(DataWriteError)
    async def data_write_handler(
        request: Request,
        exception: DataWriteError,
    ) -> JSONResponse:
        LOGGER.exception("category_write_failed path=%s", request.url.path)
        return error_response(500, "DATA_WRITE_ERROR", str(exception))

    application.include_router(categories_router, prefix="/api")
    return application


app = create_app()
