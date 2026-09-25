"""Завдання 3: Безпечне хешування, CSV-база та JSON-логування (Варіант 6)."""

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from functools import wraps


class ValidationError(Exception):
    """Виняток для помилок валідації пароля."""


def generate_hash(password: str, salt: str = "00000") -> str:
    """Генерує хеш пароля з сіллю за алгоритмом blake2s (Варіант 6)."""
    if not password or not salt:
        raise ValueError("Пароль або сіль не можуть бути порожніми.")

    min_length = 9  # Мінімальна довжина для варіанта 6
    if len(password) < min_length:
        raise ValidationError(f"Пароль занадто короткий. Мінімум: {min_length}")

    data = (password + salt).encode("utf-8")
    return hashlib.blake2s(data).hexdigest()


def log_event(func):
    """Декоратор для логування подій автентифікації у JSON."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        success = True
        username = args[0] if args else "unknown"
        try:
            result = func(*args, **kwargs)
            if not result:
                success = False
            return result
        except Exception:
            success = False
            raise
        finally:
            log_dir = "labs/lab01/data"
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "log.json")

            log_entry = {
                "event": "login",
                "user": username,
                "result": "success" if success else "failure",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "args": list(args[1:]),
                "kwargs": kwargs,
            }

            logs = []
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                except (json.JSONDecodeError, OSError):
                    logs = []

            logs.append(log_entry)
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)

    return wrapper


def create_user(username: str, password: str, salt: str) -> tuple[str, str]:
    """Створює пару (логін, хеш) для користувача."""
    pwd_hash = generate_hash(password, salt)
    return username, pwd_hash


def create_users_db(users_list: tuple, salt: str) -> None:
    """Створює CSV-базу даних користувачів."""
    data_dir = "labs/lab01/data"
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "users.csv")

    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password_hash"])
            for uname, pwd in users_list:
                try:
                    _, pwd_hash = create_user(uname, pwd, salt)
                    writer.writerow([uname, pwd_hash])
                except (ValueError, ValidationError) as e:
                    print(f"Попередження при реєстрації користувача {uname}: {e}")
    except (OSError, FileNotFoundError, PermissionError) as e:
        print(f"Помилка при роботі з файлом бази даних: {e}")


def read_users_db() -> list:
    """Зчитує базу даних із CSV-файлу."""
    data_dir = "labs/lab01/data"
    csv_path = os.path.join(data_dir, "users.csv")
    users_db = []

    try:
        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Пропускаємо заголовки
                for row in reader:
                    if row:
                        users_db.append(row)
    except (OSError, FileNotFoundError, PermissionError) as e:
        print(f"Помилка читання бази: {e}")
    return users_db


@log_event
def login(username: str, password: str, salt: str) -> bool:
    """Перевіряє автентифікацію користувача за базою даних."""
    if not username or not password:
        raise ValueError("Логін і пароль не можуть бути порожніми.")

    users_db = read_users_db()
    input_hash = generate_hash(password, salt)

    for uname, stored_hash in users_db:
        if uname == username and stored_hash == input_hash:
            return True
    return False


def run_task3() -> None:
    """Головна функція для демонстрації Завдання 3."""
    salt = "00006"  # Сіль для 6 варіанту
    users_to_register = (
        ("admin_v6", "SecurePass#6"),
        ("analyst_v6", "AnalystKey!9"),
        ("user_v6", "NormalPass$5"),
        ("test_v6", "Test123456!"),
        ("dev_v6", "Developer#88"),
        ("sec_v6", "Security*99"),
        ("guest_v6", "GuestKey#12"),
        ("root_v6", "RootAdmin!00"),
        ("audit_v6", "AuditPass#77"),
        ("temp_v6", "TempUser$123"),
    )

    create_users_db(users_to_register, salt)
    db = read_users_db()

    print("\nЗчитана база даних користувачів (CSV):")
    print(f"{'Логін':<15} | {'Хеш пароля':<40}")
    print("-" * 60)
    for row in db:
        print(f"{row[0]:<15} | {row[1]:<40}")

    try:
        res1 = login("admin_v6", "SecurePass#6", salt)
        print(f"\nВхід admin_v6: {'Успішно' if res1 else 'Помилка'}")

        res2 = login("admin_v6", "WrongPassword", salt)
        print(f"Вхід з невірним паролем: {'Успішно' if res2 else 'Помилка'}")
    except Exception as e:  # noqa: BLE001
        print(f"Виняток при вході: {e}")


if __name__ == "__main__":
    run_task3()