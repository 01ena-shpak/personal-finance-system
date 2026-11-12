from typing import Annotated, Literal

from fastapi import APIRouter, Path, Request, Response, status
from pydantic import BaseModel, ConfigDict

from src.api.contract import (
    BAD_REQUEST,
    CATEGORY_CREATE_CONFLICT,
    CATEGORY_IN_USE,
    CATEGORY_RENAME_CONFLICT,
    INTERNAL_SERVER_ERROR,
    METHOD_NOT_ALLOWED,
    NOT_FOUND,
    UNSUPPORTED_MEDIA_TYPE,
    VALIDATION_ERROR,
)
from src.services.categories import CategoryService


router = APIRouter(tags=["Categories"])


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: Literal["income", "expense"]


class CategoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    type: Literal["income", "expense"]


class CategoryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createCategory",
    responses={
        400: BAD_REQUEST,
        405: METHOD_NOT_ALLOWED,
        409: CATEGORY_CREATE_CONFLICT,
        415: UNSUPPORTED_MEDIA_TYPE,
        422: VALIDATION_ERROR,
        500: INTERNAL_SERVER_ERROR,
    },
)
def create_category(payload: CategoryCreate, request: Request) -> CategoryResponse:
    service: CategoryService = request.app.state.category_service
    category = service.create(payload.name, payload.type)
    return CategoryResponse(**category)


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    operation_id="listCategories",
    responses={
        405: METHOD_NOT_ALLOWED,
        500: INTERNAL_SERVER_ERROR,
    },
)
def list_categories(request: Request) -> list[CategoryResponse]:
    service: CategoryService = request.app.state.category_service
    return [CategoryResponse(**category) for category in service.list_all()]


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    operation_id="renameCategory",
    responses={
        400: BAD_REQUEST,
        404: NOT_FOUND,
        405: METHOD_NOT_ALLOWED,
        409: CATEGORY_RENAME_CONFLICT,
        415: UNSUPPORTED_MEDIA_TYPE,
        422: VALIDATION_ERROR,
        500: INTERNAL_SERVER_ERROR,
    },
)
def rename_category(
    payload: CategoryPatch,
    request: Request,
    category_id: Annotated[int, Path(ge=1)],
) -> CategoryResponse:
    service: CategoryService = request.app.state.category_service
    category = service.rename(category_id, payload.name)
    return CategoryResponse(**category)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteCategory",
    responses={
        404: NOT_FOUND,
        405: METHOD_NOT_ALLOWED,
        409: CATEGORY_IN_USE,
        422: VALIDATION_ERROR,
        500: INTERNAL_SERVER_ERROR,
    },
)
def delete_category(
    request: Request,
    category_id: Annotated[int, Path(ge=1)],
) -> Response:
    service: CategoryService = request.app.state.category_service
    service.delete(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
