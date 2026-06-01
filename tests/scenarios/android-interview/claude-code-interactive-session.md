# Android Interview - Claude Code - Interactive Session

## Scenario

Run the Android interview skill in real turn-by-turn mode with scripted answers, stage transitions, round summaries, and local artifacts.

## Expected Behavior

- The session starts with a self-introduction round before technical rounds.
- The same round can contain multiple questions before the round summary is emitted.
- The runner writes `session.json`, `score.json`, `turn-events.json`, `transcript.md`, and `report.html`.
- The turn event log includes round lifecycle stages such as `intro`, `questioning`, `follow_up`, `summary`, `deliberation`, and `advance` or `reject`.
- Each round writes an explicit internal deliberation step before the final round decision is emitted.
- The output keeps evidence-based scoring, round-level decision summaries, `round3`, and generated fallback questions when bank coverage is insufficient.
