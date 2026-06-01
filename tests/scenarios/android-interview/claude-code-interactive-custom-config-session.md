# Android Interview - Claude Code - Interactive Custom Config Session

## Scenario

Run the Android interview skill with a custom global interviewer persona, per-round persona overrides, per-round language overrides, and reduced question targets for later rounds.

## Expected Behavior

- The session still completes with structured turn-by-turn artifacts.
- `session.json` records the effective persona configuration in `input_config`.
- `session.json` also records the round language override map in `input_config`.
- `interview-plan.json` reflects the overridden per-round `question_target` values.
- The report shows the configured round languages in the interview plan section.
- The resulting session uses fewer total scored questions than the default interactive path.
