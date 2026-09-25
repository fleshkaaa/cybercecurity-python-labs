"""Завдання 1: Комплексний аналізатор надійності паролів (Варіант 6)."""

import os
import random
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import VARIANT_NUMBER


def analyze_passwords() -> None:
    """Аналізує стійкість паролів згідно з Варіантом 6."""
    passwords = [
        "InfoS3c@2023",
        "simple123",
        "Def3ns3@Key",
        "public",
        "Encrypt3d#Pass",
        "basic123",
        "Secur3@Analysis",
        "temp123",
        "Prot3ct@Data",
        "default",
    ]
    criteria = {
        "min_length": 8,
        "require_digits": True,
        "require_upper": True,
        "require_special": True,
    }
    forbidden_passwords = {
        "simple123",
        "public",
        "basic123",
        "temp123",
        "default",
        "guest",
    }

    # Генерація 3 випадкових індексів та додавання їхніх дублікатів у кінець
    random.seed(VARIANT_NUMBER)
    indices = [random.randint(0, len(passwords) - 1) for _ in range(3)]
    for idx in indices:
        passwords.append(passwords[idx])

    print(f"{'Пароль':<25} | {'Статус':<15}")
    print("-" * 45)

    for pwd in passwords:
        status = "Сильний"

        has_digit = any(char.isdigit() for char in pwd)
        has_upper = any(char.isupper() for char in pwd)
        has_special = any(not char.isalnum() for char in pwd)
        has_lower = any(char.islower() for char in pwd)

        if pwd in forbidden_passwords or len(pwd) < criteria["min_length"]:
            status = "Заборонений"
        elif (
            len(pwd) >= criteria["min_length"]
            and has_digit
            and has_upper
            and has_special
            and has_lower
            and len(pwd) >= criteria["min_length"] + 4
            and passwords.count(pwd) == 1
        ):
            status = "Дуже сильний"
        elif (
            len(pwd) >= criteria["min_length"]
            and has_digit
            and has_upper
            and has_special
            and has_lower
        ):
            status = "Сильний"
        elif has_digit or has_upper or has_special or has_lower:
            status = "Слабкий"
        else:
            status = "Заборонений"

        print(f"{pwd:<25} | {status:<15}")


if __name__ == "__main__":
    analyze_passwords()