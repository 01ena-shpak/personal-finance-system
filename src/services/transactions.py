from datetime import date
import logging
import sqlite3

from src.repositories.categories import CategoryRepository
from src.repositories.transactions import TransactionRepository
from src.services.errors import DataReadError, DataWriteError


LOGGER = logging.getLogger("personal_finance")


class TransactionValidationError(Exception):
    def __init__(self, message: str, field: str, rule: str) -> None:
        super().__init__(message)
        self.message = message
        self.field = field
        self.rule = rule


class TransactionNotFoundError(Exception):
    pass


class TransactionService:
    def __init__(
        self,
        repository: TransactionRepository,
        category_repository: CategoryRepository,
    ) -> None:
        self.repository = repository
        self.category_repository = category_repository

    @staticmethod
    def parse_local_date(value: str, field: str) -> date:
        try:
            parsed = date.fromisoformat(value)
        except (TypeError, ValueError) as exception:
            raise TransactionValidationError(
                f"Поле {field} повинно містити реальну дату YYYY-MM-DD.",
                field,
                "real_iso_date",
            ) from exception
        if parsed.isoformat() != value:
            raise TransactionValidationError(
                f"Поле {field} повинно містити реальну дату YYYY-MM-DD.",
                field,
                "real_iso_date",
            )
        return parsed

    def validate_state(
        self,
        *,
        transaction_type: str,
        transaction_date: str,
        category_id: int,
        client_local_date: str,
    ) -> None:
        local_date = self.parse_local_date(
            client_local_date,
            "X-Client-Local-Date",
        )
        parsed_transaction_date = self.parse_local_date(transaction_date, "date")
        if parsed_transaction_date > local_date:
            raise TransactionValidationError(
                "Дата Transaction не може бути пізнішою за поточну локальну дату пристрою User.",
                "date",
                "not_after_client_local_date",
            )

        try:
            category = self.category_repository.get_by_id(category_id)
        except sqlite3.Error as exception:
            raise DataReadError("Збережені дані неможливо прочитати.") from exception
        if category is None:
            raise TransactionNotFoundError("Ресурс з указаним ID не існує.")
        if category["type"] != transaction_type:
            raise TransactionValidationError(
                "Тип Category повинен відповідати типу Transaction.",
                "category_id",
                "category_type_matches_transaction_type",
            )

    def create(
        self,
        *,
        transaction_type: str,
        amount: str,
        transaction_date: str,
        category_id: int,
        description: str | None,
        client_local_date: str,
    ) -> dict[str, object]:
        self.validate_state(
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            category_id=category_id,
            client_local_date=client_local_date,
        )
        try:
            transaction = self.repository.create(
                transaction_type,
                amount,
                transaction_date,
                category_id,
                description,
            )
        except sqlite3.Error as exception:
            raise DataWriteError(
                "Результат зміни неможливо стійко й атомарно зберегти."
            ) from exception
        LOGGER.info(
            "transaction_created id=%s type=%s category_id=%s",
            transaction["id"],
            transaction["type"],
            transaction["category_id"],
        )
        return transaction

    def list_all(
        self,
        *,
        transaction_type: str | None,
        category_id: int | None,
        date_from: str | None,
        date_to: str | None,
    ) -> list[dict[str, object]]:
        if (date_from is None) != (date_to is None):
            raise TransactionValidationError(
                "Межі Date Range потрібно передавати разом.",
                "date_range",
                "paired_date_range_bounds",
            )
        if date_from is not None and date_to is not None:
            parsed_from = self.parse_local_date(date_from, "date_from")
            parsed_to = self.parse_local_date(date_to, "date_to")
            if parsed_from > parsed_to:
                raise TransactionValidationError(
                    "Початкова дата Date Range не може бути пізнішою за кінцеву.",
                    "date_range",
                    "date_from_not_after_date_to",
                )
        try:
            transactions = self.repository.list_all(
                transaction_type=transaction_type,
                category_id=category_id,
                date_from=date_from,
                date_to=date_to,
            )
        except sqlite3.Error as exception:
            raise DataReadError("Збережені дані неможливо прочитати.") from exception
        LOGGER.info("transactions_listed count=%s", len(transactions))
        return transactions

    @staticmethod
    def amount_to_cents(amount: str) -> int:
        whole, fraction = amount.split(".")
        if (
            not whole.isdigit()
            or len(fraction) != 2
            or not fraction.isdigit()
            or (len(whole) > 1 and whole.startswith("0"))
            or (whole == "0" and fraction == "00")
        ):
            raise ValueError("Invalid stored amount")
        return int(whole) * 100 + int(fraction)

    @staticmethod
    def cents_to_money(cents: int) -> str:
        sign = "-" if cents < 0 else ""
        whole, fraction = divmod(abs(cents), 100)
        return f"{sign}{whole}.{fraction:02d}"

    def financial_summary(self) -> dict[str, str]:
        try:
            amounts = self.repository.list_amounts_by_type()
            total_income = 0
            total_expenses = 0
            for item in amounts:
                cents = self.amount_to_cents(item["amount"])
                if item["type"] == "income":
                    total_income += cents
                elif item["type"] == "expense":
                    total_expenses += cents
                else:
                    raise ValueError("Invalid stored transaction type")
        except (sqlite3.Error, ValueError) as exception:
            raise DataReadError(
                "Збережені дані неможливо прочитати або коректно підсумувати."
            ) from exception

        LOGGER.info("financial_summary_calculated transaction_count=%s", len(amounts))
        return {
            "total_income": self.cents_to_money(total_income),
            "total_expenses": self.cents_to_money(total_expenses),
            "current_balance": self.cents_to_money(
                total_income - total_expenses
            ),
        }

    def update(
        self,
        transaction_id: int,
        patch: dict[str, object],
        client_local_date: str,
    ) -> dict[str, object]:
        try:
            current = self.repository.get_by_id(transaction_id)
        except sqlite3.Error as exception:
            raise DataReadError("Збережені дані неможливо прочитати.") from exception
        if current is None:
            raise TransactionNotFoundError("Ресурс з указаним ID не існує.")

        resulting = {
            "type": current["type"],
            "amount": current["amount"],
            "date": current["date"],
            "category_id": current["category_id"],
            "description": current["description"],
            **patch,
        }
        self.validate_state(
            transaction_type=str(resulting["type"]),
            transaction_date=str(resulting["date"]),
            category_id=int(resulting["category_id"]),
            client_local_date=client_local_date,
        )
        try:
            updated = self.repository.update(
                transaction_id,
                transaction_type=str(resulting["type"]),
                amount=str(resulting["amount"]),
                date=str(resulting["date"]),
                category_id=int(resulting["category_id"]),
                description=(
                    str(resulting["description"])
                    if resulting["description"] is not None
                    else None
                ),
            )
        except sqlite3.Error as exception:
            raise DataWriteError(
                "Результат зміни неможливо стійко й атомарно зберегти."
            ) from exception
        if updated is None:
            raise TransactionNotFoundError("Ресурс з указаним ID не існує.")
        LOGGER.info(
            "transaction_updated id=%s type=%s category_id=%s",
            updated["id"],
            updated["type"],
            updated["category_id"],
        )
        return updated

    def delete(self, transaction_id: int) -> None:
        try:
            deleted = self.repository.delete(transaction_id)
        except sqlite3.Error as exception:
            raise DataWriteError(
                "Результат зміни неможливо стійко й атомарно зберегти."
            ) from exception
        if not deleted:
            raise TransactionNotFoundError("Ресурс з указаним ID не існує.")
        LOGGER.info("transaction_deleted id=%s", transaction_id)
