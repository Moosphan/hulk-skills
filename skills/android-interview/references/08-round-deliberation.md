# Round Deliberation

## Goal

Convert question-level evidence into a round-level verdict.

## Inputs

Use:

- round objective
- question results
- strengths
- risks
- missing evidence
- unresolved contradictions

## Allowed Verdicts

- `advance`
- `advance_with_risk`
- `borderline`
- `reject`

## Deliberation Questions

At round end, answer:

1. Did the round collect the evidence it was supposed to collect?
2. Which positive signals are strongest?
3. Which risks remain unresolved?
4. Is one more probe likely to change the judgment?
5. Should risk be carried into the next round?

## Output Shape

```json
{
  "round": "round2",
  "verdict": "advance_with_risk",
  "reason": "",
  "carry_forward_risks": [],
  "next_round_probe": ""
}
```

## Carry-Forward Rule

If a round passes with risk:

- do not reset the interview tone completely
- carry the unresolved risk into the next round
- use the next round to confirm or clear it early
