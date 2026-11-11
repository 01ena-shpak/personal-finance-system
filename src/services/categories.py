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


class CategoryNotFoundError(Exception):
    pass


class DataWriteError(Exception):
    pass


class DataReadError(Exception):
    pass


class CategoryService:
    def __init__(self, repository: CategoryRepository) -> None:
        self.repository = repository

    def create(self, name: str, category_type: str) -> dict[str, object]:
        normalized_name = self.normalize_name(name)

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

    @staticmethod
    def normalize_name(name: str) -> str:
        normalized_name = name.strip()
        if not 1 <= len(normalized_name) <= 50:
            raise CategoryValidationError(
                "Поле name після видалення крайніх пробілів повинно містити від 1 до 50 символів.",
                "name",
                "normalized_length_1_to_50",
            )
        return normalized_name

    def list_all(self) -> list[dict[str, object]]:
        try:
            categories = self.repository.list_all()
        except sqlite3.Error as exception:
            raise DataReadError(
                "Збережені дані неможливо прочитати."
            ) from exception
        LOGGER.info("categories_listed count=%s", len(categories))
        return categories

    def rename(self, category_id: int, name: str) -> dict[str, object]:
        normalized_name = self.normalize_name(name)
        try:
            category = self.repository.get_by_id(category_id)
            if category is None:
                raise CategoryNotFoundError("Ресурс з указаним ID не існує.")

            name_key = normalized_name.casefold()
            if self.repository.name_key_exists_for_other_category(
                category_id,
                str(category["type"]),
                name_key,
            ):
                raise CategoryConflictError(
                    "Category з такою назвою вже існує в межах цього типу."
                )

            renamed = self.repository.rename(category_id, normalized_name, name_key)
            if renamed is None:
                raise CategoryNotFoundError("Ресурс з указаним ID не існує.")
        except (CategoryNotFoundError, CategoryConflictError):
            raise
        except sqlite3.IntegrityError as exception:
            raise CategoryConflictError(
                "Category з такою назвою вже існує в межах цього типу."
            ) from exception
        except sqlite3.Error as exception:
            raise DataWriteError(
                "Результат зміни неможливо стійко й атомарно зберегти."
            ) from exception

        LOGGER.info("category_renamed id=%s type=%s", renamed["id"], renamed["type"])
        return renamed

    def delete(self, category_id: int) -> None:
        try:
            deleted = self.repository.delete(category_id)
        except sqlite3.Error as exception:
            raise DataWriteError(
                "Результат зміни неможливо стійко й атомарно зберегти."
            ) from exception
        if not deleted:
            raise CategoryNotFoundError("Ресурс з указаним ID не існує.")
        LOGGER.info("category_deleted id=%s", category_id)
