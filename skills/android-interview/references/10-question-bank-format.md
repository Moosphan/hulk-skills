# Question Bank Format

## Purpose

Markdown question banks are optional structured input, not the primary source of interviewer intelligence.

## Expected Format

Each question file may contain:

- YAML frontmatter
- question body
- intent
- follow-ups
- scoring notes
- red flags
- good signals

## Recommended Fields

- `id`
- `title`
- `direction`
- `round`
- `level`
- `difficulty`
- `language`
- `tags`
- `competencies`
- `expected_signal`
- `follow_up_limit`

## How Claude Code Should Use The Bank

- prefer well-matched bank questions when they target the right evidence
- do not ask a bank question just because it exists
- bank hits should support the round objective and candidate profile

## Validation Policy

If the user provides an external question bank and wants reliability:

- call `scripts/validate_question_bank.py`
- surface errors or warnings clearly
- only use invalid banks if the user accepts the risk

## Parsing Policy

If you need structured bank metadata for selection:

- use `scripts/question_bank.py`
- keep the reasoning in the conversation
- do not let the parser decide interview conclusions
