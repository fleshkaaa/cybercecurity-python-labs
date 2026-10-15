"""Головний модуль Лабораторної роботи №2 (Варіант 6)."""

import argparse
import sys
from pathlib import Path

# Додаємо корінь репозиторію до sys.path для надійного імпорту
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from labs.lab02.task1 import run_oop_demo
from labs.lab02.task2 import audit_wordlist
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def build_parser() -> argparse.ArgumentParser:
    """Створює парсер аргументів командного рядка для утиліти."""
    parser = argparse.ArgumentParser(
        prog="python -m labs.lab02.main",
        description=(
            f"Лабораторна робота №2 | Студент: {STUDENT_NAME} "
            f"({GROUP_NAME}) | Варіант {VARIANT_NUMBER}"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Підкоманда demo (Завдання 1)
    subparsers.add_parser(
        "demo",
        help="Запустити демонстрацію ООП моделі користувачів та сесій (Завдання 1)",
    )

    # Підкоманда analyze (Завдання 2 - Варіант 6)
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Запустити аудитор надійності та масок словників паролів (Завдання 2)",
    )
    analyze_parser.add_argument(
        "--wordlist",
        type=Path,
        required=True,
        help="Шлях до вхідного текстового файлу словника паролів",
    )
    analyze_parser.add_argument(
        "--min-length",
        type=int,
        default=8,
        help="Мінімальна довжина надійного пароля (за замовчуванням: 8)",
    )
    analyze_parser.add_argument(
        "--top-masks",
        type=int,
        default=5,
        help="Кількість найпопулярніших масок для виводу (за замовчуванням: 5)",
    )
    analyze_parser.add_argument(
        "--output-stats",
        type=Path,
        default=Path("labs/lab02/data/mask_audit_report.json"),
        help="Шлях до файлу JSON зі статистикою аудиту",
    )

    return parser


def main() -> None:
    """Точка входу консольної програми."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "demo":
            run_oop_demo()
        elif args.command == "analyze":
            audit_wordlist(
                wordlist_path=args.wordlist,
                min_length=args.min_length,
                top_masks=args.top_masks,
                output_stats_path=args.output_stats,
            )
    except (FileNotFoundError, PermissionError, ValueError, OSError) as err:
        print(f"[ERROR] Помилка виконання: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
