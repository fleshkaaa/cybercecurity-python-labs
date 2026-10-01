"""Головний файл для демонстрації виконання Лабораторної роботи №1 (Варіант 6)."""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from task1 import analyze_passwords
from task2 import check_access
from task3 import run_secure_hashing_and_logging

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def main() -> None:
    """Головна функція запуску всіх завдань лаби."""
    print("=" * 60)
    print(" ЛАБОРАТОРНА РОБОТА №1")
    print(f" Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}")
    print("=" * 60)

    try:
        print("\n[ЗАВДАННЯ 1] Аналіз надійності паролів:")
        analyze_passwords()

        print("\n[ЗАВДАННЯ 2] Система контролю доступу:")
        check_access()

        print("\n[ЗАВДАННЯ 3] Безпечне хешування та логування:")
        run_secure_hashing_and_logging()

        print("\n" + "=" * 60)
        print(" Всі завдання для Варіанту 6 успішно виконано!")
        print("=" * 60)
    except Exception as e:  # noqa: BLE001
        print(f"\n[КРИТИЧНА ПОМИЛКА]: Виник непередбачений виняток: {e}")


if __name__ == "__main__":
    main()