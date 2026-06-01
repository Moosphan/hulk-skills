# Consistency Check

## Goal

Check whether the candidate's answers remain internally consistent across the interview.

## What To Check

- ownership consistency
- metric consistency
- timeline consistency
- architecture / tradeoff consistency
- leadership / influence consistency
- scope consistency

## Trigger Conditions

Run a stronger consistency check when:

- later answers downgrade earlier ownership claims
- numbers or baselines drift unexpectedly
- timeline details no longer align
- previously claimed decision authority disappears under pressure
- the candidate sounds much stronger in one place than another without explanation

## Challenge Policy

When challenging a contradiction:

- quote the earlier position fairly
- state the new conflicting signal
- ask for reconciliation instead of immediate accusation
- if the contradiction remains unresolved, record it as risk evidence

## Output Shape

```json
{
  "category": "ownership_consistency",
  "status": "resolved_or_unresolved",
  "evidence": [],
  "risk_level": "low|medium|high",
  "recommended_challenge": ""
}
```
