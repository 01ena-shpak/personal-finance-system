import logging
import sqlite3

from src.repositories.categories import CategoryRepository


LOGGER = logging.getLogger("personal_finance")


class CategoryValidationError(Exception):
    def __init__(self, message: str, field: str, rule: str) -> None:
        super().__init__(message)
        self.message = message
        self.field = field
        self.rule = rule


class CategoryConflictError(Exception):
    pass


class DataWriteError(Exception):
    pass


class CategoryService:
    def __init__(self, repository: CategoryRepository) -> None:
        self.repository = repository

    def create(self, name: str, category_type: str) -> dict[str, object]:
        normalized_name = name.strip()
        if not 1 <= len(normalized_name) <= 50:
            raise CategoryValidationError(
                "Поле name після видалення крайніх пробілів повинно містити від 1 до 50 символів.",
                "name",
                "normalized_length_1_to_50",
            )

        name_key = normalized_name.casefold()
        if self.repository.exists_by_name_key(category_type, name_key):
            raise CategoryConflictError(
                "Category з такою назвою вже існує в межах цього типу."
            )

        try:
            category = self.repository.create(
                normalized_name,
                name_key,
                category_type,
            )
        except sqlite3.IntegrityError as exception:
            raise CategoryConflictError(
                "Category з такою назвою вже існує в межах цього типу."
            ) from exception
        except sqlite3.Error as exception:
            raise DataWriteError(
                "Результат зміни неможливо стійко й атомарно зберегти."
            ) from exception

        LOGGER.info(
            "category_created id=%s type=%s",
            category["id"],
            category["type"],
        )
        return category
