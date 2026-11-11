from contextlib import closing
from pathlib import Path
import sqlite3


class CategoryRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        name_key TEXT NOT NULL,
                        type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                        UNIQUE (type, name_key)
                    )
                    """
                )

    def exists_by_name_key(self, category_type: str, name_key: str) -> bool:
        with closing(self.connect()) as connection:
            row = connection.execute(
                "SELECT 1 FROM categories WHERE type = ? AND name_key = ?",
                (category_type, name_key),
            ).fetchone()
        return row is not None

    def list_all(self) -> list[dict[str, object]]:
        with closing(self.connect()) as connection:
            rows = connection.execute(
                "SELECT id, name, type FROM categories ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, category_id: int) -> dict[str, object] | None:
        with closing(self.connect()) as connection:
            row = connection.execute(
                "SELECT id, name, type FROM categories WHERE id = ?",
                (category_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def name_key_exists_for_other_category(
        self,
        category_id: int,
        category_type: str,
        name_key: str,
    ) -> bool:
        with closing(self.connect()) as connection:
            row = connection.execute(
                """
                SELECT 1 FROM categories
                WHERE type = ? AND name_key = ? AND id <> ?
                """,
                (category_type, name_key, category_id),
            ).fetchone()
        return row is not None

    def rename(
        self,
        category_id: int,
        name: str,
        name_key: str,
    ) -> dict[str, object] | None:
        with closing(self.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "UPDATE categories SET name = ?, name_key = ? WHERE id = ?",
                    (name, name_key, category_id),
                )
                if cursor.rowcount == 0:
                    return None
                row = connection.execute(
                    "SELECT id, name, type FROM categories WHERE id = ?",
                    (category_id,),
                ).fetchone()
        return dict(row) if row is not None else None

    def delete(self, category_id: int) -> bool:
        with closing(self.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM categories WHERE id = ?",
                    (category_id,),
                )
        return cursor.rowcount > 0

    def create(self, name: str, name_key: str, category_type: str) -> dict[str, object]:
        with closing(self.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name, name_key, type) VALUES (?, ?, ?)",
                    (name, name_key, category_type),
                )
                category_id = cursor.lastrowid
        return {"id": category_id, "name": name, "type": category_type}
