"""Маршрути для роботи з категоріями."""

from fastapi import APIRouter, Path, status

from labs.lab03 import repository
from labs.lab03.config import SQLITE_MAX_INT
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Список категорій",
    description="Повертає всі категорії за зростанням id.",
)
def list_categories() -> list[CategoryRead]:
    """Повернути список категорій."""
    return repository.list_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити категорію",
    responses={409: {"description": "Категорія з такою назвою вже існує."}},
)
def create_category(payload: CategoryCreate) -> CategoryRead:
    """Створити категорію."""
    return repository.create_category(payload.name)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити порожню категорію",
    responses={
        404: {"description": "Категорію не знайдено."},
        409: {"description": "Категорія містить записи."},
    },
)
def delete_category(
    category_id: int = Path(
        gt=0, le=SQLITE_MAX_INT, description="Ідентифікатор категорії."
    ),
) -> None:
    """Видалити порожню категорію."""
    repository.delete_category(category_id)
