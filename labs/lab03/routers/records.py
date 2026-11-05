"""Маршрути для роботи із записами."""

from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, status

from labs.lab03 import repository
from labs.lab03.config import (
    DEFAULT_LIMIT,
    MAX_BATCH_SIZE,
    MAX_LIMIT,
    SQLITE_MAX_INT,
    TITLE_MAX_LENGTH,
    VALUE_MIN,
    Status,
)
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter(prefix="/records", tags=["records"])

RecordId = Annotated[
    int, Path(gt=0, le=SQLITE_MAX_INT, description="Ідентифікатор запису.")
]


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Список записів із фільтрами",
    description="Фільтри поєднуються через AND; результат відсортовано за id.",
)
def list_records(
    category_id: Annotated[
        int | None,
        Query(gt=0, le=SQLITE_MAX_INT, description="Лише записи цієї категорії."),
    ] = None,
    status: Annotated[
        Status | None, Query(description="Лише записи з цим статусом.")
    ] = None,
    min_value: Annotated[
        int | None,
        Query(
            ge=VALUE_MIN,
            le=SQLITE_MAX_INT,
            description="Мінімальна кількість подій (value >= min_value).",
        ),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=TITLE_MAX_LENGTH,
            description="Буквальний підрядок у title з урахуванням регістру.",
        ),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=MAX_LIMIT, description="Максимальна кількість записів.")
    ] = DEFAULT_LIMIT,
    offset: Annotated[
        int, Query(ge=0, le=SQLITE_MAX_INT, description="Скільки записів пропустити.")
    ] = 0,
) -> list[RecordRead]:
    """Повернути записи за фільтрами."""
    return repository.list_records(
        category_id=category_id,
        status=status,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Пакетне створення записів",
    description="Усі записи зберігаються в одній транзакції: або всі, або жоден.",
    responses={
        404: {"description": "Одна з категорій не існує; нічого не збережено."},
        409: {"description": "Дублікат code; нічого не збережено."},
    },
)
def create_records_bulk(
    payload: Annotated[
        list[RecordCreate], Body(min_length=1, max_length=MAX_BATCH_SIZE)
    ],
) -> list[RecordRead]:
    """Атомарно створити пакет записів."""
    return repository.create_records_bulk(payload)


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запис",
    responses={
        404: {"description": "Категорію не знайдено."},
        409: {"description": "Запис із таким code вже існує."},
    },
)
def create_record(payload: RecordCreate) -> RecordRead:
    """Створити запис."""
    return repository.create_record(payload)


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис",
    responses={404: {"description": "Запис не знайдено."}},
)
def get_record(record_id: RecordId) -> RecordRead:
    """Повернути один запис."""
    return repository.get_record(record_id)


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити запис",
    description="Усі змінювані поля обов’язкові; id не змінюється.",
    responses={
        404: {"description": "Запис або категорію не знайдено."},
        409: {"description": "Запис із таким code вже існує."},
    },
)
def replace_record(record_id: RecordId, payload: RecordReplace) -> RecordRead:
    """Замінити запис."""
    return repository.replace_record(record_id, payload)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    responses={404: {"description": "Запис не знайдено."}},
)
def delete_record(record_id: RecordId) -> None:
    """Видалити запис."""
    repository.delete_record(record_id)
