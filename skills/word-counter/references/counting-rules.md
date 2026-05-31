# Counting Rules

This skill keeps the counting logic deterministic by separating character-style counting and word-style counting.

## Profiles

### `zh`

Use for Chinese稿件的实际字数。

Formula:

```text
zh_content_chars = cjk_chars + latin_letters + digit_chars + other_letter_chars
```

Meaning:

- Count every CJK character as `1`.
- Count every Latin letter as `1`.
- Count every digit as `1`.
- Count letters from other scripts as `1`.
- Ignore whitespace and punctuation.

### `en`

Use for English稿件的实际 word count。

Formula:

```text
en_word_count = english_words + number_tokens + other_words
```

Meaning:

- Count English word tokens as `1`.
- Count numeric tokens such as `2026`, `3.14`, `10/10`, `25%` as `1`.
- Count other non-CJK word tokens from other scripts as `1`.

Token rules:

- `don't` counts as `1`.
- `state-of-the-art` counts as `1`.
- `OpenAI` counts as `1`.

### `mixed`

Use when the user wants one total for中英混排文本。

Formula:

```text
mixed_count = cjk_chars + english_words + number_tokens + other_words
```

Meaning:

- CJK characters keep Chinese-style counting.
- English and other non-CJK segments keep word-style counting.

## Examples

### Example 1

Input:

```text
你好 OpenAI 2026
```

Result:

- `zh_content_chars = 12`
- `en_word_count = 2`
- `mixed_count = 4`

### Example 2

Input:

```text
OpenAI builds safe AI in 2026.
```

Result:

- `zh_content_chars = 24`
- `en_word_count = 6`
- `mixed_count = 6`

### Example 3

Input:

```text
ＡＩ测试１２３
```

Result:

- Fullwidth Latin letters and digits are normalized for tokenization.
- `zh_content_chars = 7`
- `en_word_count = 2`
- `mixed_count = 4`

