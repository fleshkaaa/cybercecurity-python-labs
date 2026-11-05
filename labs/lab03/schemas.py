"""Pydantic-моделі запитів і відповідей."""

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03.config import (
    CODE_MAX_LENGTH,
    CODE_MIN_LENGTH,
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    SQLITE_MAX_INT,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    VALUE_MIN,
    Status,
)


class StudentRead(BaseModel):
    """Дані студента."""

    student_name: str
    group_name: str
    variant_number: int


class CategoryCreate(BaseModel):
    """Тіло запиту для створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        min_length=NAME_MIN_LENGTH,
        max_length=NAME_MAX_LENGTH,
        description="Унікальна назва категорії.",
        examples=["phishing"],
    )


class CategoryRead(CategoryCreate):
    """Категорія у відповіді API."""

    id: int


class RecordCreate(BaseModel):
    """Тіло запиту для створення запису (id задає база даних)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(
        min_length=CODE_MIN_LENGTH,
        max_length=CODE_MAX_LENGTH,
        description="Унікальний код запису.",
        examples=["V06-09"],
    )
    title: str = Field(
        min_length=TITLE_MIN_LENGTH,
        max_length=TITLE_MAX_LENGTH,
        description="Назва запису.",
        examples=["Спостереження пошти 09"],
    )
    category_id: int = Field(
        gt=0,
        le=SQLITE_MAX_INT,
        description="Ідентифікатор наявної категорії.",
    )
    value: int = Field(
        ge=VALUE_MIN,
        le=SQLITE_MAX_INT,
        strict=True,
        description="Кількість виявлених подій (ціле число, одиниця: events).",
        examples=[12],
    )
    status: Status = Field(description="Стан опрацювання запису.")


class RecordReplace(RecordCreate):
    """Тіло запиту для повної заміни запису: усі змінювані поля обов’язкові."""


class RecordRead(RecordCreate):
    """Запис у відповіді API разом з назвою категорії."""

    id: int
    category_name: str
