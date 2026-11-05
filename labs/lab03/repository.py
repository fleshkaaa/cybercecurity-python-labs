"""Параметризовані SQL-запити до таблиць categories і records."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager

from labs.lab03.database import get_connection
from labs.lab03.schemas import CategoryRead, RecordCreate, RecordRead

RECORD_SELECT = """
    SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name,
           r.value, r.status
    FROM records AS r
    JOIN categories AS c ON c.id = r.category_id
"""


class RepositoryError(Exception):
    """Базовий клас помилок шару доступу до даних."""


class NotFoundError(RepositoryError):
    """Потрібний запис або категорія не існує."""


class ConflictError(RepositoryError):
    """Порушення унікальності або спроба видалити непорожню категорію."""


@contextmanager
def _transaction(*, write: bool = False) -> Iterator[sqlite3.Connection]:
    """Відкрити з’єднання, виконати зміни в одній транзакції та закрити його.

    Контекстний менеджер з’єднання підтверджує зміни за успіху або скасовує
    їх за винятку; саме з’єднання закриває ``closing``.
    """
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        with connection:
            if write:
                connection.execute("BEGIN IMMEDIATE")
            yield connection


def _conflict_from(error: sqlite3.IntegrityError) -> RepositoryError | None:
    """Перетворити помилку цілісності на помилку предметного рівня."""
    message = str(error)
    if "UNIQUE" in message:
        return ConflictError("Значення, яке має бути унікальним, уже існує.")
    if "FOREIGN KEY" in message:
        return NotFoundError("Категорію не знайдено.")
    return None


def _category_exists(connection: sqlite3.Connection, category_id: int) -> bool:
    """Перевірити існування категорії."""
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return row is not None


def _require_category(connection: sqlite3.Connection, category_id: int) -> None:
    """Викликати NotFoundError, якщо категорії немає."""
    if not _category_exists(connection, category_id):
        raise NotFoundError("Категорію не знайдено.")


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> RecordRead:
    """Прочитати запис разом з назвою категорії."""
    row = connection.execute(RECORD_SELECT + " WHERE r.id = ?", (record_id,)).fetchone()
    if row is None:
        raise NotFoundError("Запис не знайдено.")
    return RecordRead(**dict(row))


def create_category(name: str) -> CategoryRead:
    """Створити категорію."""
    try:
        with _transaction(write=True) as connection:
            cursor = connection.execute(
                "INSERT INTO categories (name) VALUES (?)", (name,)
            )
            return CategoryRead(id=int(cursor.lastrowid or 0), name=name)
    except sqlite3.IntegrityError as error:
        converted = _conflict_from(error)
        if converted is None:
            raise
        raise converted from error


def list_categories() -> list[CategoryRead]:
    """Повернути категорії за зростанням id."""
    with _transaction() as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
    return [CategoryRead(**dict(row)) for row in rows]


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію."""
    with _transaction(write=True) as connection:
        _require_category(connection, category_id)
        used = connection.execute(
            "SELECT COUNT(*) FROM records WHERE category_id = ?", (category_id,)
        ).fetchone()[0]
        if used:
            raise ConflictError("Категорія містить записи й не може бути видалена.")
        connection.execute("DELETE FROM categories WHERE id = ?", (category_id,))


def _insert_record(connection: sqlite3.Connection, record: RecordCreate) -> int:
    """Додати запис у межах наявної транзакції та повернути його id."""
    cursor = connection.execute(
        "INSERT INTO records (code, title, category_id, value, status) "
        "VALUES (?, ?, ?, ?, ?)",
        (record.code, record.title, record.category_id, record.value, record.status),
    )
    return int(cursor.lastrowid or 0)


def create_record(record: RecordCreate) -> RecordRead:
    """Додати один запис."""
    try:
        with _transaction(write=True) as connection:
            _require_category(connection, record.category_id)
            record_id = _insert_record(connection, record)
            return _fetch_record(connection, record_id)
    except sqlite3.IntegrityError as error:
        converted = _conflict_from(error)
        if converted is None:
            raise
        raise converted from error


def create_records_bulk(records: list[RecordCreate]) -> list[RecordRead]:
    """Атомарно додати пакет записів: або всі, або жодного."""
    try:
        with _transaction(write=True) as connection:
            for category_id in sorted({record.category_id for record in records}):
                _require_category(connection, category_id)
            codes = [record.code for record in records]
            if len(set(codes)) != len(codes):
                raise ConflictError("Пакет містить повторювані коди.")
            ids = [_insert_record(connection, record) for record in records]
            return [_fetch_record(connection, record_id) for record_id in ids]
    except sqlite3.IntegrityError as error:
        converted = _conflict_from(error)
        if converted is None:
            raise
        raise converted from error


def get_record(record_id: int) -> RecordRead:
    """Повернути запис за id."""
    with _transaction() as connection:
        return _fetch_record(connection, record_id)


def list_records(
    *,
    category_id: int | None,
    status: str | None,
    min_value: int | None,
    q: str | None,
    limit: int,
    offset: int,
) -> list[RecordRead]:
    """Повернути записи за фільтрами (умови об’єднано через AND) зі сторінками."""
    with _transaction() as connection:
        rows = connection.execute(
            RECORD_SELECT
            + """
            WHERE (? IS NULL OR r.category_id = ?)
              AND (? IS NULL OR r.status = ?)
              AND (? IS NULL OR r.value >= ?)
              AND (? IS NULL OR instr(r.title, ?) > 0)
            ORDER BY r.id
            LIMIT ? OFFSET ?
            """,
            (
                category_id,
                category_id,
                status,
                status,
                min_value,
                min_value,
                q,
                q,
                limit,
                offset,
            ),
        ).fetchall()
    return [RecordRead(**dict(row)) for row in rows]


def replace_record(record_id: int, record: RecordCreate) -> RecordRead:
    """Повністю замінити змінювані поля запису; id не змінюється."""
    try:
        with _transaction(write=True) as connection:
            _require_category(connection, record.category_id)
            cursor = connection.execute(
                "UPDATE records SET code = ?, title = ?, category_id = ?, "
                "value = ?, status = ? WHERE id = ?",
                (
                    record.code,
                    record.title,
                    record.category_id,
                    record.value,
                    record.status,
                    record_id,
                ),
            )
            if cursor.rowcount == 0:
                raise NotFoundError("Запис не знайдено.")
            return _fetch_record(connection, record_id)
    except sqlite3.IntegrityError as error:
        converted = _conflict_from(error)
        if converted is None:
            raise
        raise converted from error


def delete_record(record_id: int) -> None:
    """Видалити запис за id."""
    with _transaction(write=True) as connection:
        cursor = connection.execute("DELETE FROM records WHERE id = ?", (record_id,))
        if cursor.rowcount == 0:
            raise NotFoundError("Запис не знайдено.")


def seed_database(
    categories: list[tuple[int, str]], records: list[RecordCreate]
) -> bool:
    """Заповнити порожню базу в одній транзакції.

    Повертає ``False`` без змін, якщо в базі вже є дані.
    """
    with _transaction(write=True) as connection:
        total = connection.execute(
            "SELECT (SELECT COUNT(*) FROM categories) + (SELECT COUNT(*) FROM records)"
        ).fetchone()[0]
        if total:
            return False
        connection.executemany(
            "INSERT INTO categories (id, name) VALUES (?, ?)", categories
        )
        for record in records:
            _insert_record(connection, record)
    return True
