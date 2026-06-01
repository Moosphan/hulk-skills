# Report Output

## Goal

Produce a report that explains the final decision through evidence.

## Minimum Deliverables

- screening summary
- round summaries
- question-level evidence
- final decision
- improvement suggestions

## Recommended Local Files

- `session.json`
- `score.json`
- `transcript.md`
- `report.html`
- `screening-summary.md`
- `resume-prep.md`
- `mail-reject.html` when rejected

## Report Structure

1. session metadata
2. screening snapshot
3. round-by-round summary
4. detailed question evidence
5. consistency summary
6. final verdict
7. improvement plan

## Writing Rules

- explain conclusions through concrete evidence
- separate strengths, risks, and missing evidence
- keep the report readable by a candidate
- avoid raw internal jargon unless it helps interpretation

## Artifact Mode

If the user wants files:

- generate structured content first
- optionally call `scripts/render_skill_artifacts.py` to render the standard local artifact set from structured `session.json` and `score.json`
- call helper scripts only for deterministic writing or rendering
- do not let the rendering tool decide interview conclusions

## Minimum Structured Bundle

When the interview is conducted directly in the conversation, the render helper should receive a structured bundle shaped like:

```json
{
  "session": {
    "session_id": "android-interview-session",
    "interactive_mode": true,
    "screening_summary": {},
    "resume_prep": {},
    "question_bank_validation": {},
    "round_summaries": [],
    "round_deliberations": [],
    "turn_events": [],
    "panel_memos": []
  },
  "score": {
    "score_scale": "1-5",
    "question_count": 0,
    "questions": [],
    "final_decision": "pass"
  }
}
```

The bundle may use `session_data` and `score_data` instead of `session` and `score`, but the meaning should stay the same.
