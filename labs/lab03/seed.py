"""Початкове заповнення бази з data/seed.json."""

import json
import logging
import sqlite3
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from labs.lab03.config import SQLITE_MAX_INT
from labs.lab03.database import BASE_DIR, initialize_database
from labs.lab03.repository import seed_database
from labs.lab03.schemas import CategoryCreate, RecordCreate

SEED_PATH = BASE_DIR / "data" / "seed.json"
EXPECTED_CATEGORIES = 3
EXPECTED_RECORDS = 8

logger = logging.getLogger(__name__)


class SeedCategory(CategoryCreate):
    """Категорія з явним id для початкових даних."""

    id: int = Field(gt=0, le=SQLITE_MAX_INT)


class SeedData(BaseModel):
    """Структура seed.json."""

    model_config = ConfigDict(extra="forbid")

    categories: list[SeedCategory]
    records: list[RecordCreate]


def load_seed(path: Path = SEED_PATH) -> SeedData:
    """Прочитати та перевірити файл початкових даних."""
    data = json.loads(path.read_text(encoding="utf-8"))
    seed = SeedData.model_validate(data)
    if len(seed.categories) != EXPECTED_CATEGORIES:
        raise ValueError(f"Очікується {EXPECTED_CATEGORIES} категорії.")
    if len(seed.records) != EXPECTED_RECORDS:
        raise ValueError(f"Очікується {EXPECTED_RECORDS} записів.")
    return seed


def run() -> int:
    """Заповнити базу та повернути код завершення процесу."""
    try:
        seed = load_seed()
    except (OSError, ValueError, ValidationError) as error:
        logger.error("Некоректні початкові дані: %s", error)
        print("Помилка: файл seed.json відсутній або містить некоректні дані.")
        return 1

    initialize_database()
    try:
        inserted = seed_database(
            [(category.id, category.name) for category in seed.categories],
            seed.records,
        )
    except sqlite3.Error:
        logger.exception("Не вдалося заповнити базу")
        print("Помилка: початкові дані порушують обмеження, зміни скасовано.")
        return 1

    if inserted:
        print(
            f"Базу заповнено: {len(seed.categories)} категорії, "
            f"{len(seed.records)} записів."
        )
    else:
        print("База вже містить дані: повторне заповнення пропущено.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
