# Android Interview - Codex - Render Skill Artifacts

## Scenario

Render the standard local artifact set from structured `session.json` and `score.json` payloads that already exist, without asking the legacy runtime to conduct the interview again.

## Expected Behavior

- The renderer accepts structured outputs from a prior interview run.
- The renderer writes `report.html`, `transcript.md`, `screening-summary.md`, `resume-prep.md`, and `pass-summary.md`.
- The renderer preserves round deliberations, question-bank validation, and turn-event visibility in the rendered artifacts.
- The renderer does not recalculate the interview result or replace the original structured evidence.
