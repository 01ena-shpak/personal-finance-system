from contextlib import closing
from collections.abc import Callable
from pathlib import Path
import sqlite3


TRANSACTION_SELECT = """
    SELECT t.id, t.type, t.amount, t.date, t.category_id,
           c.name AS category_name, t.description
    FROM transactions AS t
    JOIN categories AS c ON c.id = t.category_id
"""


class TransactionRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.before_commit: Callable[[], None] = lambda: None

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with closing(self.connect()) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                        amount TEXT NOT NULL,
                        date TEXT NOT NULL,
                        category_id INTEGER NOT NULL,
                        description TEXT,
                        FOREIGN KEY (category_id)
                            REFERENCES categories(id) ON DELETE RESTRICT
                    )
                    """
                )

    @staticmethod
    def row_to_transaction(row: sqlite3.Row) -> dict[str, object]:
        return dict(row)

    def get_by_id(self, transaction_id: int) -> dict[str, object] | None:
        with closing(self.connect()) as connection:
            row = connection.execute(
                f"{TRANSACTION_SELECT} WHERE t.id = ?",
                (transaction_id,),
            ).fetchone()
        return self.row_to_transaction(row) if row is not None else None

    def create(
        self,
        transaction_type: str,
        amount: str,
        date: str,
        category_id: int,
        description: str | None,
    ) -> dict[str, object]:
        with closing(self.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO transactions (
                        type, amount, date, category_id, description
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (transaction_type, amount, date, category_id, description),
                )
                transaction_id = int(cursor.lastrowid)
                row = connection.execute(
                    f"{TRANSACTION_SELECT} WHERE t.id = ?",
                    (transaction_id,),
                ).fetchone()
                self.before_commit()
        if row is None:
            raise sqlite3.DatabaseError("Created transaction cannot be read")
        return self.row_to_transaction(row)

    def list_all(
        self,
        *,
        transaction_type: str | None = None,
        category_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, object]]:
        conditions: list[str] = []
        values: list[object] = []
        if transaction_type is not None:
            conditions.append("t.type = ?")
            values.append(transaction_type)
        if category_id is not None:
            conditions.append("t.category_id = ?")
            values.append(category_id)
        if date_from is not None and date_to is not None:
            conditions.append("t.date BETWEEN ? AND ?")
            values.extend((date_from, date_to))
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = (
            f"{TRANSACTION_SELECT} {where_clause} "
            "ORDER BY t.date DESC, t.id ASC"
        )
        with closing(self.connect()) as connection:
            rows = connection.execute(query, values).fetchall()
        return [self.row_to_transaction(row) for row in rows]

    def update(
        self,
        transaction_id: int,
        *,
        transaction_type: str,
        amount: str,
        date: str,
        category_id: int,
        description: str | None,
    ) -> dict[str, object] | None:
        with closing(self.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE transactions
                    SET type = ?, amount = ?, date = ?, category_id = ?,
                        description = ?
                    WHERE id = ?
                    """,
                    (
                        transaction_type,
                        amount,
                        date,
                        category_id,
                        description,
                        transaction_id,
                    ),
                )
                if cursor.rowcount == 0:
                    return None
                row = connection.execute(
                    f"{TRANSACTION_SELECT} WHERE t.id = ?",
                    (transaction_id,),
                ).fetchone()
                self.before_commit()
        return self.row_to_transaction(row) if row is not None else None

    def delete(self, transaction_id: int) -> bool:
        with closing(self.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM transactions WHERE id = ?",
                    (transaction_id,),
                )
                self.before_commit()
        return cursor.rowcount > 0
