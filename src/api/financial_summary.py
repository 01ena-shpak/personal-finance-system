from typing import Annotated

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from src.services.transactions import TransactionService


router = APIRouter(tags=["Financial Summary"])

NonNegativeMoney = Annotated[
    str,
    Field(pattern=r"^(?:0|[1-9][0-9]*)\.[0-9]{2}$"),
]
POSITIVE_MONEY_PATTERN = (
    r"(?:0\.(?:0[1-9]|[1-9][0-9])|[1-9][0-9]*\.[0-9]{2})"
)
SIGNED_MONEY_PATTERN = (
    rf"^(?:0\.00|{POSITIVE_MONEY_PATTERN}|-{POSITIVE_MONEY_PATTERN})$"
)
SignedMoney = Annotated[
    str,
    Field(pattern=SIGNED_MONEY_PATTERN),
]


class FinancialSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    total_income: NonNegativeMoney
    total_expenses: NonNegativeMoney
    current_balance: SignedMoney


@router.get("/financial-summary", response_model=FinancialSummaryResponse)
def get_financial_summary(request: Request) -> FinancialSummaryResponse:
    service: TransactionService = request.app.state.transaction_service
    return FinancialSummaryResponse(**service.financial_summary())
