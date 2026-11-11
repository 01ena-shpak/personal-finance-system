from typing import Literal

from fastapi import APIRouter, Request, status
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


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(payload: CategoryCreate, request: Request) -> CategoryResponse:
    service: CategoryService = request.app.state.category_service
    category = service.create(payload.name, payload.type)
    return CategoryResponse(**category)
