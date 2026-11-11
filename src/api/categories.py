from typing import Annotated, Literal

from fastapi import APIRouter, Path, Request, Response, status
from pydantic import BaseModel, ConfigDict

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
)
def create_category(payload: CategoryCreate, request: Request) -> CategoryResponse:
    service: CategoryService = request.app.state.category_service
    category = service.create(payload.name, payload.type)
    return CategoryResponse(**category)


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(request: Request) -> list[CategoryResponse]:
    service: CategoryService = request.app.state.category_service
    return [CategoryResponse(**category) for category in service.list_all()]


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
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
)
def delete_category(
    request: Request,
    category_id: Annotated[int, Path(ge=1)],
) -> Response:
    service: CategoryService = request.app.state.category_service
    service.delete(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
