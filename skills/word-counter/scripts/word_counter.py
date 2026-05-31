#!/usr/bin/env python3
"""Deterministic counting for Chinese, English, and mixed-language text."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from typing import Iterable


CJK_RANGES = (
    (0x3400, 0x4DBF),   # CJK Unified Ideographs Extension A
    (0x4E00, 0x9FFF),   # CJK Unified Ideographs
    (0xF900, 0xFAFF),   # CJK Compatibility Ideographs
    (0x20000, 0x2A6DF), # CJK Unified Ideographs Extension B
    (0x2A700, 0x2B73F), # CJK Unified Ideographs Extension C
    (0x2B740, 0x2B81F), # CJK Unified Ideographs Extension D
    (0x2B820, 0x2CEAF), # CJK Unified Ideographs Extension E/F
    (0x2CEB0, 0x2EBEF), # CJK Unified Ideographs Extension G/I
    (0x2F800, 0x2FA1F), # CJK Compatibility Ideographs Supplement
    (0x3040, 0x309F),   # Hiragana
    (0x30A0, 0x30FF),   # Katakana
    (0x31F0, 0x31FF),   # Katakana Phonetic Extensions
    (0x1100, 0x11FF),   # Hangul Jamo
    (0x3130, 0x318F),   # Hangul Compatibility Jamo
    (0xAC00, 0xD7AF),   # Hangul Syllables
)

WORD_JOINERS = {"'", "’", "-"}
NUMBER_JOINERS = {".", ",", ":", "/", "-"}
PROFILE_FORMULAS = {
    "zh": "zh_content_chars = cjk_chars + latin_letters + digit_chars + other_letter_chars",
    "en": "en_word_count = english_words + number_tokens + other_words",
    "mixed": "mixed_count = cjk_chars + english_words + number_tokens + other_words",
}
PROFILE_LABELS = {
    "zh": "Chinese content count",
    "en": "English word count",
    "mixed": "Mixed-language count",
}
PROFILE_LABELS_ZH = {
    "zh": "中文实际字数",
    "en": "英文词数",
    "mixed": "中英混排总数",
}
SUMMARY_LABELS = {
    "en": {
        "title": "Word Count Result",
        "profile": "Counting mode",
        "total": "Selected total",
        "formula": "Applied formula",
        "table_metric": "Metric",
        "table_value": "Value",
        "zh_total": "Chinese count",
        "en_total": "English words",
        "mixed_total": "Mixed total",
        "cjk_chars": "CJK characters",
        "english_words": "English words",
        "number_tokens": "Number tokens",
        "source_length": "Source length",
        "line_count": "Line count",
        "paragraph_count": "Paragraph count",
    },
    "zh": {
        "title": "字数统计结果",
        "profile": "统计方式",
        "total": "总数",
        "formula": "规则",
        "table_metric": "项目",
        "table_value": "数值",
        "zh_total": "中文字数",
        "en_total": "英文词数",
        "mixed_total": "混排总数",
        "cjk_chars": "CJK 字符",
        "english_words": "英文单词",
        "number_tokens": "数字 token",
        "source_length": "原文长度",
        "line_count": "行数",
        "paragraph_count": "段落数",
    },
}


@dataclass
class CountResult:
    profile: str
    selected_total: int
    selected_formula: str
    zh_content_chars: int
    en_word_count: int
    mixed_count: int
    cjk_chars: int
    latin_letters: int
    digit_chars: int
    other_letter_chars: int
    english_words: int
    number_tokens: int
    other_words: int
    whitespace_chars: int
    punctuation_chars: int
    symbol_chars: int
    source_length: int
    line_count: int
    paragraph_count: int

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


def detect_output_locale(text: str) -> str:
    for char in text:
        if is_cjk_char(char):
            return "zh"
    return "en"


def is_cjk_char(char: str) -> bool:
    codepoint = ord(char)
    return any(start <= codepoint <= end for start, end in CJK_RANGES)


def is_latin_letter(char: str) -> bool:
    if not char.isalpha():
        return False
    return "LATIN" in unicodedata.name(char, "")


def is_letter(char: str) -> bool:
    return unicodedata.category(char).startswith("L")


def consume_latin_word(text: str, start: int) -> int:
    index = start + 1
    while index < len(text):
        char = text[index]
        if is_latin_letter(char):
            index += 1
            continue
        if (
            char in WORD_JOINERS
            and index + 1 < len(text)
            and is_latin_letter(text[index - 1])
            and is_latin_letter(text[index + 1])
        ):
            index += 1
            continue
        break
    return index


def consume_number_token(text: str, start: int) -> int:
    index = start + 1
    while index < len(text):
        char = text[index]
        if char.isdigit():
            index += 1
            continue
        if char == "%" and text[index - 1].isdigit():
            index += 1
            break
        if (
            char in NUMBER_JOINERS
            and index + 1 < len(text)
            and text[index - 1].isdigit()
            and text[index + 1].isdigit()
        ):
            index += 1
            continue
        break
    return index


def consume_other_word(text: str, start: int) -> int:
    index = start + 1
    while index < len(text):
        char = text[index]
        if is_letter(char) and not is_cjk_char(char) and not is_latin_letter(char):
            index += 1
            continue
        break
    return index


def iter_tokens(text: str) -> Iterable[str]:
    normalized = unicodedata.normalize("NFKC", text)
    index = 0
    while index < len(normalized):
        char = normalized[index]
        if is_cjk_char(char):
            yield "cjk"
            index += 1
            continue
        if is_latin_letter(char):
            yield "english_word"
            index = consume_latin_word(normalized, index)
            continue
        if char.isdigit():
            yield "number_token"
            index = consume_number_token(normalized, index)
            continue
        if is_letter(char):
            yield "other_word"
            index = consume_other_word(normalized, index)
            continue
        index += 1


def count_paragraphs(text: str) -> int:
    if not text.strip():
        return 0
    return len([block for block in re.split(r"\n\s*\n", text.strip()) if block.strip()])


def analyze_text(text: str, profile: str = "mixed") -> CountResult:
    if profile not in PROFILE_FORMULAS:
        raise ValueError(f"Unsupported profile: {profile}")

    cjk_chars = 0
    latin_letters = 0
    digit_chars = 0
    other_letter_chars = 0
    whitespace_chars = 0
    punctuation_chars = 0
    symbol_chars = 0

    for char in text:
        category = unicodedata.category(char)
        if char.isspace():
            whitespace_chars += 1
        elif is_cjk_char(char):
            cjk_chars += 1
        elif is_latin_letter(char):
            latin_letters += 1
        elif char.isdigit():
            digit_chars += 1
        elif category.startswith("L"):
            other_letter_chars += 1
        elif category.startswith("P"):
            punctuation_chars += 1
        else:
            symbol_chars += 1

    english_words = 0
    number_tokens = 0
    other_words = 0

    for token_kind in iter_tokens(text):
        if token_kind == "english_word":
            english_words += 1
        elif token_kind == "number_token":
            number_tokens += 1
        elif token_kind == "other_word":
            other_words += 1

    zh_content_chars = cjk_chars + latin_letters + digit_chars + other_letter_chars
    en_word_count = english_words + number_tokens + other_words
    mixed_count = cjk_chars + en_word_count

    selected_total = {
        "zh": zh_content_chars,
        "en": en_word_count,
        "mixed": mixed_count,
    }[profile]

    line_count = 0 if not text else text.count("\n") + 1
    paragraph_count = count_paragraphs(text)

    return CountResult(
        profile=profile,
        selected_total=selected_total,
        selected_formula=PROFILE_FORMULAS[profile],
        zh_content_chars=zh_content_chars,
        en_word_count=en_word_count,
        mixed_count=mixed_count,
        cjk_chars=cjk_chars,
        latin_letters=latin_letters,
        digit_chars=digit_chars,
        other_letter_chars=other_letter_chars,
        english_words=english_words,
        number_tokens=number_tokens,
        other_words=other_words,
        whitespace_chars=whitespace_chars,
        punctuation_chars=punctuation_chars,
        symbol_chars=symbol_chars,
        source_length=len(text),
        line_count=line_count,
        paragraph_count=paragraph_count,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministically count Chinese, English, and mixed-language text."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Optional text file path. If omitted, read --text or stdin.",
    )
    parser.add_argument(
        "--text",
        help="Inline text to count. Prefer stdin for multi-line content.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_FORMULAS),
        default="mixed",
        help="Counting profile: zh, en, or mixed. Default: mixed.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "text", "json"),
        default="markdown",
        help="Output format. Default: markdown.",
    )
    parser.add_argument(
        "--locale",
        choices=("auto", "zh", "en"),
        default="auto",
        help="Output language for markdown/text. Default: auto.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Show detailed statistics in markdown/text output.",
    )
    return parser.parse_args(argv)


def read_input_text(args: argparse.Namespace) -> str:
    if args.text is not None and args.input_file:
        raise ValueError("Use either --text or input_file, not both.")
    if args.text is not None:
        return args.text
    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as handle:
            return handle.read()
    if sys.stdin.isatty():
        raise ValueError("No input provided. Pass --text, input_file, or stdin.")
    return sys.stdin.read()


def profile_label_for_locale(profile: str, locale: str) -> str:
    if locale == "zh":
        return PROFILE_LABELS_ZH[profile]
    return PROFILE_LABELS[profile]


def format_profile_display(profile: str, locale: str) -> str:
    label = profile_label_for_locale(profile, locale)
    if locale == "zh":
        return f"`{profile}`（{label}）"
    return f"`{profile}` ({label})"


def build_summary_rows(
    result: CountResult, locale: str, details: bool
) -> list[tuple[str, int]]:
    labels = SUMMARY_LABELS[locale]
    rows: list[tuple[str, int]] = []

    if result.profile == "mixed":
        rows.extend(
            [
                (labels["zh_total"], result.zh_content_chars),
                (labels["en_total"], result.en_word_count),
                (labels["mixed_total"], result.mixed_count),
            ]
        )
    elif result.profile == "zh":
        rows.append((labels["zh_total"], result.zh_content_chars))
    else:
        rows.append((labels["en_total"], result.en_word_count))

    if details:
        if result.cjk_chars > 0:
            rows.append((labels["cjk_chars"], result.cjk_chars))
        if result.english_words > 0:
            rows.append((labels["english_words"], result.english_words))
        rows.append((labels["number_tokens"], result.number_tokens))
        rows.append((labels["source_length"], result.source_length))

    if result.line_count > 1 or details:
        rows.append((labels["line_count"], result.line_count))
    if result.paragraph_count > 1 or details:
        rows.append((labels["paragraph_count"], result.paragraph_count))

    return rows


def render_text(result: CountResult, locale: str, details: bool) -> str:
    labels = SUMMARY_LABELS[locale]
    rows = build_summary_rows(result, locale, details)
    colon = ": " if locale == "en" else "："
    lines = [
        labels["title"],
        f"- {labels['profile']}{colon}{format_profile_display(result.profile, locale)}",
        f"- {labels['total']}{colon}`{result.selected_total}`",
        f"- {labels['formula']}{colon}`{result.selected_formula}`",
    ]
    for label, value in rows:
        lines.append(f"- {label}{colon} {value}")
    return "\n".join(lines)


def render_markdown(result: CountResult, locale: str, details: bool) -> str:
    labels = SUMMARY_LABELS[locale]
    rows = build_summary_rows(result, locale, details)
    colon = ": " if locale == "en" else "："
    lines = [
        f"# {labels['title']}",
        "",
        f"- {labels['profile']}{colon}{format_profile_display(result.profile, locale)}",
        f"- {labels['total']}{colon}`{result.selected_total}`",
        f"- {labels['formula']}{colon}`{result.selected_formula}`",
        "",
        f"| {labels['table_metric']} | {labels['table_value']} |",
        "| --- | ---: |",
    ]
    for label, value in rows:
        lines.append(f"| {label} | {value} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        text = read_input_text(args)
        result = analyze_text(text, args.profile)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    locale = detect_output_locale(text) if args.locale == "auto" else args.locale

    if args.format == "json":
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        print(render_markdown(result, locale, args.details))
    else:
        print(render_text(result, locale, args.details))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
