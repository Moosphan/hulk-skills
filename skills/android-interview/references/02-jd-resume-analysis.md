# JD And Resume Analysis

## Goal

Transform raw JD and resume inputs into two structured profiles:

- `job_profile`
- `candidate_profile`

These profiles become the foundation for round planning, question generation, follow-up choice, scoring, and final judgment.

## JD Analysis

Extract:

- target level
- core Android stack expectations
- must-have requirements
- nice-to-have requirements
- business context
- leadership expectation
- English requirement
- evidence that should be verified during interview

## Resume Analysis

Extract:

- strongest project anchors
- claimed ownership
- claimed metrics
- architecture / performance claims
- leadership / influence claims
- vague or unverifiable statements
- likely deep-dive entry points
- likely risk points

## Analysis Principles

- prefer concrete evidence over keyword counting
- distinguish claims from verified evidence
- mark ambiguity explicitly
- identify where the interview should validate真实性, depth, metrics, tradeoffs, and scope

## Output Shape

```json
{
  "job_profile": {
    "target_level": "senior",
    "must_have": [],
    "nice_to_have": [],
    "business_context": "",
    "english_requirement": "",
    "evidence_to_verify": []
  },
  "candidate_profile": {
    "project_anchors": [],
    "claimed_ownership": [],
    "claimed_metrics": [],
    "claimed_architecture_depth": [],
    "claimed_leadership": [],
    "vague_claims": [],
    "risk_points": []
  }
}
```

## Intake-To-Interview Bridge

After analysis, Claude Code should be able to answer:

1. Is this candidate plausibly aligned with the JD?
2. Which claims deserve the deepest validation?
3. Which round should carry the most pressure?
4. What evidence gaps are likely to create follow-up chains?
