# Scoring Rubric

## Required Fields

Every scored answer must include:

- `score`
- `confidence`
- `strength_evidence`
- `risk_evidence`
- `missing_evidence`

## Score Meaning

- `1`
  - clearly below bar, wrong, unverifiable, or seriously misleading
- `2`
  - partial understanding, shallow execution, weak evidence
- `3`
  - meets the basic expectation for the topic
- `4`
  - strong answer with concrete evidence and transferability
- `5`
  - exemplar answer with depth, judgment, and strong proof

## Confidence Meaning

- high confidence means the answer contains concrete, attributable evidence
- low confidence means the answer may sound plausible but remains weakly supported

## Scoring Principles

- do not give high score without evidence
- do not hide uncertainty; low confidence must be explicit
- polished wording does not equal strong evidence
- ownership, metrics, tradeoffs, diagnosis path, and failure handling matter more than buzzwords

## Output Shape

```json
{
  "score": 4,
  "confidence": 0.78,
  "strength_evidence": [],
  "risk_evidence": [],
  "missing_evidence": [],
  "recommended_next_action": "follow_up_same_topic"
}
```

## Hard Fail Signals

Treat these as potential hard fails:

- ownership appears fabricated
- repeated contradiction under direct challenge
- target-level architecture depth is clearly absent
- complete inability to answer in the required interview language

## Next Action Guidance

Use one of:

- `advance_same_round`
- `follow_up_same_topic`
- `switch_topic`
- `increase_difficulty`
- `decrease_difficulty`
- `mark_risk`
- `terminate_round_fail`
- `complete_round_pass`
