"""Завдання 2: Багаторівнева система контролю доступу (Варіант 6)."""


def check_access() -> None:
    """Головна функція для демонстрації системи контролю доступу."""
    # Вхідні дані для Варіанта 6
    users = {
        "red_team_lead": {
            "role": "red_team",
            "clearance": 4,
            "department": "Red Team",
            "active": True,
        },
        "blue_team_analyst": {
            "role": "blue_team",
            "clearance": 3,
            "department": "Blue Team",
            "active": True,
        },
        "purple_team_coord": {
            "role": "purple_team",
            "clearance": 3,
            "department": "Purple Team",
            "active": True,
        },
        "student_intern": {
            "role": "student",
            "clearance": 1,
            "department": "Academia",
            "active": True,
        },
        "retired_expert": {
            "role": "retired",
            "clearance": 2,
            "department": "Emeritus",
            "active": False,
        },
    }

    resources = [
        ("attack_scenarios", 4),
        ("defense_playbooks", 3),
        ("exercise_plans", 3),
        ("research_papers", 1),
        ("exploit_tools", 4),
        ("student_resources", 1),
        ("simulation_results", 3),
        ("red_team_tools", 4),
        ("blue_team_reports", 3),
        ("public_research", 1),
    ]

    security_levels = ("Academic", "Operational", "Tactical", "Strategic")
    blocked_users = {"retired_expert", "academic_violator", "leaked_account"}

    print("=== СПИСОК РЕСУРСІВ СИСТЕМИ (з текстовими рівнями безпеки) ===")
    for resource_name, level_num in resources:
        # Отримуємо текстову назву рівня безпеки за індексом (level_num - 1)
        level_text = security_levels[level_num - 1]
        print(f"Ресурс: {resource_name:<22} | Рівень: {level_text} ({level_num})")

    print("\n=== РЕЗУЛЬТАТИ ПЕРЕВІРКИ ДОСТУПУ ===")

    # Перевірка доступу кожного користувача до кожного ресурсу
    for username, user_info in users.items():
        for resource_name, resource_level in resources:
            # 1. Якщо користувача немає в системі
            if username not in users:
                print(f"user={username} resource={resource_name} -> DENY (User not found)")
                continue

            # 2. Якщо користувач у списку заблокованих
            if username in blocked_users:
                print(f"user={username} resource={resource_name} -> DENY (User is blocked)")
                continue

            # 3. Якщо обліковий запис неактивний
            if not user_info.get("active", False):
                print(f"user={username} resource={resource_name} -> DENY (Account inactive)")
                continue

            # 4. Перевірка рівнів допуску (clearance >= resource_level)
            user_clearance = user_info.get("clearance", 0)
            if user_clearance >= resource_level:
                print(f"user={username} resource={resource_name} -> ALLOW")
            else:
                print(f"user={username} resource={resource_name} -> DENY (Insufficient clearance)")


if __name__ == "__main__":
    check_access()