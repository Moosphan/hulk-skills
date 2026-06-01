# Question Generation Strategy

## Priority Order

Choose questions in this order:

1. high-confidence question-bank hits
2. resume-anchor deep dives
3. JD gap-filling questions
4. fallback questions to cover missing competencies

## Selection Principles

- prefer questions that validate a specific candidate claim
- prefer questions that expose real project depth
- do not default to generic Android trivia when stronger JD or resume anchors exist
- avoid repeating the same topic unless evidence is incomplete or contradictory

## What A Good Question Should Do

A good question should:

- target one clear competency
- be anchored in the candidate's likely experience or JD pressure
- create room for evidence, not just concepts
- support focused follow-up

## Output Shape

When selecting or generating a question, internally keep:

```json
{
  "question": "",
  "round": "",
  "target_competency": "",
  "why_this_question": "",
  "expected_signal": "",
  "follow_up_strategy": ""
}
```

## Repeat Policy

Do not repeat a topic unless:

- the candidate contradicted themself
- the previous answer was too vague to verify
- the round needs one harder probe on the same topic

## Question Bank Usage

If a question bank exists:

- prefer it for stable quality and reproducibility
- do not let it override better JD/resume evidence targeting
- validate format first when the bank is external or untrusted
