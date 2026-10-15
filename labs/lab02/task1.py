"""Завдання 1: Модель користувача й облікового запису (ООП)."""

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

PBKDF2_ITERATIONS = 100_000
SESSION_TIMEOUT_SEC = 900

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_.-]{2,63}@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$"
)


class User:
    """Клас для представлення користувача системи."""

    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user",
        active: bool = True,
    ) -> None:
        """Ініціалізує об'єкт користувача."""
        if not username:
            raise ValueError("Ім'я користувача не може бути порожнім.")
        self.username: str = username
        self.email: str = email
        self.role: str = role
        self.active: bool = active
        self.__password_salt: bytes = b""
        self.__password_hash: bytes = b""
        self.set_password(password)

    @property
    def email(self) -> str:
        """Повертає електронну пошту користувача."""
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        """Встановлює електронну пошту після перевірки регулярним виразом."""
        if not isinstance(value, str) or not EMAIL_REGEX.match(value):
            raise ValueError(f"Некоректний формат email: {value}")
        self._email = value

    def set_password(self, password: str) -> None:
        """Встановлює пароль, зберігаючи лише випадкову сіль та PBKDF2-хеш."""
        if not isinstance(password, str) or len(password) < 6:
            raise ValueError("Пароль має містити щонайменше 6 символів.")
        self.__password_salt = os.urandom(16)
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        """Перевіряє пароль за допомогою захищеного порівняння дайджестів."""
        if not isinstance(password, str) or not self.__password_hash:
            return False
        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, candidate_hash)

    def deactivate(self) -> None:
        """Деактивує обліковий запис користувача."""
        self.active = False

    def __str__(self) -> str:
        """Повертає рядкове представлення користувача без чутливих даних."""
        status = "active" if self.active else "inactive"
        return (
            f"User(username='{self.username}', email='{self.email}', "
            f"role='{self.role}', status='{status}')"
        )


class Admin(User):
    """Клас адміністратора, що успадковує User та додає систему дозволів."""

    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        permissions: set[str] | list[str] | None = None,
        active: bool = True,
    ) -> None:
        """Ініціалізує адміністратора без змінюваних аргументів за замовчуванням."""
        super().__init__(
            username=username,
            email=email,
            password=password,
            role="admin",
            active=active,
        )
        self.permissions: set[str] = (
            set(permissions) if permissions is not None else set()
        )

    def grant_permission(self, permission: str) -> None:
        """Надає вказаний дозвіл адміністратору."""
        if not permission or not isinstance(permission, str):
            raise ValueError("Назва дозволу має бути непорожнім рядком.")
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        """Відкликає вказаний дозвіл у адміністратора."""
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """Перевіряє наявність дозволу."""
        return permission in self.permissions

    def __str__(self) -> str:
        """Повертає рядкове представлення адміністратора разом із правами."""
        status = "active" if self.active else "inactive"
        perms = ", ".join(sorted(self.permissions)) if self.permissions else "none"
        return (
            f"Admin(username='{self.username}', email='{self.email}', "
            f"status='{status}', permissions=[{perms}])"
        )


class Session:
    """Клас для управління сеансом користувача."""

    def __init__(self, ip: str) -> None:
        """Ініціалізує новий сеанс із поточним часом UTC."""
        if not ip or not isinstance(ip, str):
            raise ValueError("IP-адреса не може бути порожньою.")
        now = datetime.now(timezone.utc)
        self.ip: str = ip
        self.login_time: datetime = now
        self.last_activity: datetime = now

    def touch(self) -> None:
        """Оновлює час останньої активності до поточного моменту UTC."""
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int = SESSION_TIMEOUT_SEC) -> bool:
        """Перевіряє, чи не минув час дії сеансу."""
        if not isinstance(timeout_sec, int) or timeout_sec <= 0:
            raise ValueError("Таймаут сеансу має бути додатним цілим числом.")
        now = datetime.now(timezone.utc)
        return (now - self.last_activity) <= timedelta(seconds=timeout_sec)

    def __str__(self) -> str:
        """Рядкове представлення сеансу."""
        return (
            f"Session(ip='{self.ip}', "
            f"login='{self.login_time.strftime('%Y-%m-%d %H:%M:%S')} UTC', "
            f"last_activity='{self.last_activity.strftime('%Y-%m-%d %H:%M:%S')} UTC')"
        )


@dataclass(frozen=True)
class AuditEntry:
    """Клас даних для окремого запису в журналі аудиту."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Клас для збереження та відображення журналу подій безпеки."""

    def __init__(self) -> None:
        """Ініціалізує порожній список записів аудиту."""
        self._entries: list[AuditEntry] = []

    def add_log(self, username: str, action: str) -> None:
        """Додає новий запис із поточним часом UTC без збереження паролів."""
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
        )
        self._entries.append(entry)

    def show_all(self) -> None:
        """Виводить усі записи журналу аудиту на екран."""
        print("=== Audit Log Entries ===")
        if not self._entries:
            print("(Журнал порожній)")
            return
        for entry in self._entries:
            ts_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"[{ts_str}] user='{entry.username}' action='{entry.action}'")

    @property
    def entries(self) -> list[AuditEntry]:
        """Повертає копію списку записів."""
        return list(self._entries)


class UserAccount:
    """Клас облікового запису (композиція User, Session та AuditLog)."""

    def __init__(
        self,
        user: User,
        audit_log: AuditLog | None = None,
        session: Session | None = None,
    ) -> None:
        """Об'єднує об'єкти User, Session та AuditLog."""
        if not isinstance(user, User):
            raise TypeError("Поле user має бути екземпляром класу User.")
        if audit_log is not None and not isinstance(audit_log, AuditLog):
            raise TypeError("Поле audit_log має бути екземпляром класу AuditLog.")
        if session is not None and not isinstance(session, Session):
            raise TypeError("Поле session має бути екземпляром класу Session.")

        self.user: User = user
        self.audit_log: AuditLog = audit_log if audit_log is not None else AuditLog()
        self.session: Session | None = session

    def login(self, username: str, password: str, ip: str) -> bool:
        """Перевіряє дані користувача та створює сеанс при успішній автентифікації."""
        if (
            self.user.username != username
            or not self.user.active
            or not self.user.check_password(password)
        ):
            self.audit_log.add_log(username, "login_failure")
            return False

        self.session = Session(ip=ip)
        self.session.touch()
        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        """Перевіряє наявність активного сеансу."""
        if self.session is None:
            return False
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        """Завершує сеанс і фіксує подію виходу в журналі аудиту."""
        if self.session is not None:
            self.session = None
            self.audit_log.add_log(self.user.username, "logout")

    def __getitem__(self, key: str) -> Any:
        """Надає словниковий доступ до дозволених атрибутів облікового запису."""
        allowed_keys = {"user", "session", "audit_log", "authenticated"}
        if key not in allowed_keys:
            raise KeyError(
                f"Невідомий або заборонений ключ: '{key}'. Доступ до хешу/солі закритий."
            )
        if key == "authenticated":
            return self.is_authenticated()
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Дозволяє безпечно змінювати дозволені атрибути з перевіркою типів."""
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("Значення для 'user' має бути екземпляром User.")
            self.user = value
        elif key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError("Значення для 'session' має бути Session або None.")
            self.session = value
        elif key == "audit_log":
            if not isinstance(value, AuditLog):
                raise TypeError(
                    "Значення для 'audit_log' має бути екземпляром AuditLog."
                )
            self.audit_log = value
        else:
            raise KeyError(f"Невідомий або заборонений для запису ключ: '{key}'.")


def run_oop_demo() -> None:
    """Демонстраційний сценарій роботи класів Завдання 1."""
    print("=" * 60)
    print(" ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1 (ООП та Безпека облікових записів)")
    print("=" * 60)

    shared_audit = AuditLog()

    user = User(
        username="sec_analyst",
        email="analyst@cyber.edu.ua",
        password="StrongPassword#2026",
    )
    account = UserAccount(user=user, audit_log=shared_audit)
    print(f"\n[1] Створено користувача: {account['user']}")

    print("\n[2] Тестування входу в систему:")
    fail_res = account.login("sec_analyst", "WrongPass123", "192.168.1.55")
    print(f" -> Спроба з невірним паролем: {'Успіх' if fail_res else 'Відмова'}")
    print(f" -> Автентифікований зараз? {account.is_authenticated()}")

    ok_res = account.login("sec_analyst", "StrongPassword#2026", "192.168.1.55")
    print(f" -> Спроба з вірним паролем: {'Успіх' if ok_res else 'Відмова'}")
    print(f" -> Автентифікований зараз? {account.is_authenticated()}")
    print(f" -> Поточна сесія: {account['session']}")

    print("\n[3] Перевірка валідації email (@property):")
    try:
        user.email = "new.analyst_06@sec-lab.org"
        print(f" -> Email успішно змінено на: {user.email}")
        user.email = "123invalid@domain"
    except ValueError as err:
        print(f" -> Перехоплено очікувану помилку валідації: {err}")

    print("\n[4] Робота з класом Admin (наслідування):")
    admin = Admin(
        username="red_team_admin",
        email="admin@cyber.edu.ua",
        password="AdminSecret!99",
        permissions=["read_logs", "manage_users"],
    )
    admin.grant_permission("run_audits")
    admin.revoke_permission("manage_users")
    print(f" -> Об'єкт Admin: {admin}")
    print(f" -> Чи має право 'run_audits'? {admin.has_permission('run_audits')}")
    print(f" -> Чи має право 'manage_users'? {admin.has_permission('manage_users')}")

    print("\n[5] Симуляція завершення сеансу за таймаутом (>900 сек):")
    if account.session is not None:
        account.session.last_activity -= timedelta(seconds=SESSION_TIMEOUT_SEC + 60)
    print(f" -> Автентифікований після простою? {account.is_authenticated()}")

    print("\n[6] Повторний вхід та вихід із системи (logout):")
    account.login("sec_analyst", "StrongPassword#2026", "10.0.0.12")
    account.logout()
    print(f" -> Автентифікований після logout()? {account.is_authenticated()}")

    print("\n[7] Журнал аудиту подій:")
    shared_audit.show_all()
