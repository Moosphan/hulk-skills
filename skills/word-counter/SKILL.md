---
name: word-counter
description: Deterministic counting for Chinese, English, and mixed-language text such as articles, essays, novels, chapters, outlines, transcripts, and pasted paragraphs. Use when the user asks for word count, character count, manuscript length, bilingual text count, chapter length, or wants a stable count instead of a model estimate.
---

# Word Counter

Use the bundled script to produce a reproducible count. Prefer this skill whenever "roughly how many words" is not good enough.

If the user asks in Chinese, run the script with `--locale zh` so the report is returned in Chinese. If the user asks in English, use `--locale en`. Only use `--details` when the user explicitly asks for detailed statistics.

## Pick A Profile

- Use `zh` for Chinese-style content counting. This treats CJK characters, Latin letters, digits, and other letters as countable content characters, while ignoring whitespace and punctuation.
- Use `en` for English-style word counting. This counts English words, numeric tokens, and other non-CJK word tokens.
- Use `mixed` when the text contains both Chinese and English and the user wants one total. This counts each CJK character as `1`, then adds English words, number tokens, and other non-CJK word tokens.

If the user does not specify a profile, run `mixed` and report the alternative `zh` and `en` totals as context.

## Run The Script

For short single-line text:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/word-counter/scripts/word_counter.py" --profile mixed --locale en --format markdown --text "Hello world from OpenAI"
```

For multi-line text, prefer stdin:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/word-counter/scripts/word_counter.py" --profile zh --locale zh --format markdown <<'EOF'
第一段……
EOF
```

For file input:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/word-counter/scripts/word_counter.py" --profile en --locale en --format markdown ./chapter-01.txt
```

## Report The Result

Return the result in this compact Markdown format. Default to the English example below:

```markdown
# Word Count Result

- Selected profile: `mixed` (Mixed-language count)
- Selected total: `1234`
- Applied formula: `mixed_count = cjk_chars + english_words + number_tokens + other_words`

| Metric | Value |
| --- | ---: |
| Chinese count | 1300 |
| English words | 45 |
| Mixed total | 1234 |
| Line count | 12 |
| Paragraph count | 4 |
```

When the user asks in Chinese, return the same compact structure with Chinese labels. Do not show `CJK characters`, `English words`, or `Number tokens` unless the user explicitly asks for detailed statistics, in which case run with `--details`.

Prefer using the script's Markdown output directly, then optionally add a very short interpretation sentence below it.

## Counting Rules

Read [references/counting-rules.md](references/counting-rules.md) when you need the exact formulas, edge-case handling, or ready-to-use examples.
