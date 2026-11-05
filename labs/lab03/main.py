"""FastAPI-застосунок: облік подій поштової безпеки."""

import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from labs.lab03.config import DOMAIN_DESCRIPTION, DOMAIN_NAME, THRESHOLD, UNIT
from labs.lab03.database import initialize_database
from labs.lab03.repository import ConflictError, NotFoundError
from labs.lab03.routers import categories, records
from labs.lab03.schemas import StudentRead
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску, не змінюючи наявних даних."""
    initialize_database()
    yield


app = FastAPI(
    title=DOMAIN_NAME,
    description=(
        f"{DOMAIN_DESCRIPTION}\n\nОдиниця вимірювання: `{UNIT}`. Поріг: `{THRESHOLD}`."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(categories.router)
app.include_router(records.router)


@app.exception_handler(NotFoundError)
def handle_not_found(_: Request, error: NotFoundError) -> JSONResponse:
    """Перетворити NotFoundError на 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(error)}
    )


@app.exception_handler(ConflictError)
def handle_conflict(_: Request, error: ConflictError) -> JSONResponse:
    """Перетворити ConflictError на 409."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, content={"detail": str(error)}
    )


@app.exception_handler(sqlite3.Error)
def handle_database_error(_: Request, error: sqlite3.Error) -> JSONResponse:
    """Записати технічну помилку в журнал і повернути клієнту нейтральне 500."""
    logger.error("Помилка бази даних", exc_info=error)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутрішня помилка сервера."},
    )


@app.get("/ping", tags=["service"], summary="Перевірка доступності API")
def ping() -> dict[str, str]:
    """Повернути стан сервісу."""
    return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentRead,
    tags=["service"],
    summary="Дані студента",
)
def student() -> StudentRead:
    """Повернути ПІБ, групу та номер варіанта."""
    return StudentRead(
        student_name=STUDENT_NAME,
        group_name=GROUP_NAME,
        variant_number=VARIANT_NUMBER,
    )
