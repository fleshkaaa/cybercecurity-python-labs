"""Завдання 2 (Варіант 6): Аудитор надійності та масок словників паролів."""

import json
import logging
import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

logger = logging.getLogger("password_auditor")

RE_ALL_LOWER = re.compile(r"^[a-z]+$")
RE_ALL_UPPER = re.compile(r"^[A-Z]+$")
RE_ALL_DIGITS = re.compile(r"^\d+$")
RE_ALL_SPECIAL = re.compile(r"^[^a-zA-Z0-9]+$")
RE_LOWER_DIGIT = re.compile(r"^(?=.*[a-z])(?=.*\d)[a-z\d]+$")
RE_UPPER_DIGIT = re.compile(r"^(?=.*[A-Z])(?=.*\d)[A-Z\d]+$")
RE_UPPER_LOWER = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])[a-zA-Z]+$")
RE_UPPER_LOWER_DIGIT = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)[a-zA-Z\d]+$")
RE_COMPLEX = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^a-zA-Z0-9]).+$")


def setup_logging(level: int = logging.INFO) -> None:
    """Налаштовує формат виведення логів у консоль."""
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        force=True,
    )


def read_wordlist_generator(filepath: Path) -> Iterator[str]:
    """Порядково читає словник паролів за допомогою генератора для економії пам'яті."""
    with filepath.open("r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            pwd = line.rstrip("\r\n")
            if pwd:
                yield pwd


def char_to_mask_symbol(char: str) -> str:
    """Перетворює окремий символ на символ маски (U, l, d, s)."""
    if re.match(r"[A-Z]", char):
        return "U"
    if re.match(r"[a-z]", char):
        return "l"
    if re.match(r"\d", char):
        return "d"
    return "s"


def get_structural_pattern(password: str, max_len: int = 4) -> str:
    """Формує короткий структурний код маски (наприклад, Ulld)."""
    raw_mask = "".join(char_to_mask_symbol(ch) for ch in password)
    return raw_mask[:max_len]


def classify_password_mask(password: str) -> str:
    """Визначає категорію маски пароля за допомогою регулярних виразів."""
    if RE_LOWER_DIGIT.match(password):
        return "Lowercase-Digit (ldld)"
    if RE_ALL_LOWER.match(password):
        return "All-Lowercase (llll)"
    if RE_UPPER_LOWER_DIGIT.match(password):
        return "Upper-Lower-Digit (Ulld)"
    if RE_ALL_DIGITS.match(password):
        return "All-Digits (dddd)"
    if RE_COMPLEX.match(password):
        return "Complex (Upper-Lower-Digit-Special)"
    if RE_UPPER_LOWER.match(password):
        return "Upper-Lower (Ulll)"
    if RE_ALL_UPPER.match(password):
        return "All-Uppercase (UUUU)"
    if RE_UPPER_DIGIT.match(password):
        return "Upper-Digit (Uddd)"
    if RE_ALL_SPECIAL.match(password):
        return "All-Special (ssss)"
    return f"Mixed-Other ({get_structural_pattern(password)})"


def audit_wordlist(
    wordlist_path: Path,
    min_length: int = 8,
    top_masks: int = 5,
    output_stats_path: Path | None = None,
) -> dict[str, Any]:
    """Виконує повний аудит словника паролів та зберігає статистику у JSON."""
    setup_logging()

    if min_length <= 0:
        raise ValueError("Мінімальна довжина пароля має бути більшою за 0.")
    if top_masks <= 0:
        raise ValueError("Кількість топових масок має бути більшою за 0.")
    if not wordlist_path.exists() or not wordlist_path.is_file():
        raise FileNotFoundError(f"Файл словника не знайдено: {wordlist_path}")

    logger.info("Processing dictionary file %s using generators...", wordlist_path)

    total_passwords = 0
    weak_passwords = 0
    total_length = 0
    mask_counter: Counter[str] = Counter()
    mask_examples: dict[str, str] = {}

    for pwd in read_wordlist_generator(wordlist_path):
        total_passwords += 1
        pwd_len = len(pwd)
        total_length += pwd_len

        if pwd_len < min_length:
            weak_passwords += 1

        mask_category = classify_password_mask(pwd)
        mask_counter[mask_category] += 1
        if mask_category not in mask_examples:
            mask_examples[mask_category] = pwd

    logger.info("Analyzed %s passwords.", f"{total_passwords:,}")

    avg_length = (total_length / total_passwords) if total_passwords > 0 else 0.0
    weak_pct = (
        (weak_passwords / total_passwords * 100.0) if total_passwords > 0 else 0.0
    )

    print("\n=== Password Dictionary Audit Summary ===")
    print(f"{'Total Passwords':<19} : {total_passwords:,}")
    print(
        f"{f'Weak Passwords (<{min_length})':<19} : "
        f"{weak_passwords:,} ({weak_pct:.1f}%)"
    )
    print(f"{'Average Length':<19} : {avg_length:.1f} characters")

    print(f"\n=== Top-{top_masks} Password Masks ===")
    top_items = mask_counter.most_common(top_masks)
    top_masks_report = []

    for idx, (mask_name, count) in enumerate(top_items, start=1):
        pct = (count / total_passwords * 100.0) if total_passwords > 0 else 0.0
        example = mask_examples.get(mask_name, "")
        print(f"{idx}. {mask_name:<35} : {count:,} ({pct:.1f}%) [e.g. {example}]")
        top_masks_report.append(
            {
                "rank": idx,
                "mask": mask_name,
                "count": count,
                "percentage": round(pct, 2),
                "example": example,
            }
        )

    report_data: dict[str, Any] = {
        "wordlist_file": str(wordlist_path),
        "total_passwords": total_passwords,
        "min_length_threshold": min_length,
        "weak_passwords_count": weak_passwords,
        "weak_passwords_percentage": round(weak_pct, 2),
        "average_length": round(avg_length, 2),
        "top_masks": top_masks_report,
    }

    if output_stats_path is not None:
        output_stats_path.parent.mkdir(parents=True, exist_ok=True)
        with output_stats_path.open("w", encoding="utf-8") as out_file:
            json.dump(report_data, out_file, indent=4, ensure_ascii=False)
        print()
        logger.info("Dictionary statistics saved to %s", output_stats_path)

    return report_data
