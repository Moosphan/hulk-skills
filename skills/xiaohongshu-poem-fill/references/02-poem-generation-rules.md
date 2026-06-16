# Poem Generation Rules

## Blank Length

Support configurable blank length with `blank_chars`.

- default: `1`
- common values: `1`, `2`, `3`
- display form:
  - `（　）`
  - `（　　）`
  - `（　　　）`

The answer length must exactly match `blank_chars`.

## Preferred Blank Type

Default to blanking a verb or verb phrase.

- Single-character verbs: `收` `照` `入` `落` `过` `听` `染` `醒` `渡` `裁` `藏` `问` `敲` `卷` `吹` `湿` `摇` `映`
- Two-character verb phrases: `吹醒` `染透` `照破` `唤回` `听尽` `卷入` `裁开` `湿遍` `摇落` `渡过` `藏起` `敲开`

Do not blank weak function words.

## Style Source

Use classical Chinese aesthetics as inspiration, not as source text to rewrite:

- `诗经`
- `楚辞`
- `古诗十九首`
- 魏晋诗与陶渊明
- 唐诗
- 宋词
- 元曲小令

## Writing Process

1. pick the mood
2. pick the scene
3. draft the complete two-line version
4. choose the strongest blank location
5. generate one recommended answer and alternatives
6. verify originality and readability

## Quality Bar

- avoid direct borrowing from famous lines
- avoid near-paraphrases of well-known poems
- prefer common Chinese characters over obscure characters
- keep the image clear enough for social posting
- preserve room for multiple valid comment answers
