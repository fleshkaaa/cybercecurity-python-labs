"""Налаштування предметної області та обмеження варіанта 6."""

from typing import Literal, get_args

DOMAIN_NAME = "Облік подій поштової безпеки"
DOMAIN_DESCRIPTION = (
    "Сервіс обліку підсумків перевірки повідомлень. Категорія визначає тип події "
    "(phishing, malicious_attachment, spam), value містить кількість виявлених "
    "подій у спостереженні, status — стан опрацювання цього спостереження."
)

UNIT = "events"
THRESHOLD = 10
RECORD_TITLE = "Спостереження пошти"

Status = Literal["new", "in_progress", "done"]
ALLOWED_STATUSES: tuple[str, ...] = get_args(Status)

VALUE_MIN = 0
SQLITE_MAX_INT = 2**63 - 1

NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 40
CODE_MIN_LENGTH = 3
CODE_MAX_LENGTH = 40
TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 120

MAX_BATCH_SIZE = 100
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
