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

    def create(self, name: str, name_key: str, category_type: str) -> dict[str, object]:
        with closing(self.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name, name_key, type) VALUES (?, ?, ?)",
                    (name, name_key, category_type),
                )
                category_id = cursor.lastrowid
        return {"id": category_id, "name": name, "type": category_type}
