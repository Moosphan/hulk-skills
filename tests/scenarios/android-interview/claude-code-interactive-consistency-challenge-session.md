# Android Interview - Claude Code - Interactive Consistency Challenge Session

## Scenario

Run the Android interview skill in real turn-by-turn mode with a scripted answer set that creates a cross-question ownership contradiction, so the interviewer should challenge it immediately instead of waiting until the final report.

## Expected Behavior

- The session still completes with normal structured interview artifacts.
- The turn event log records a `consistency_challenge` event when the later answer conflicts with earlier ownership evidence.
- The final report surfaces the runtime consistency challenge separately from the final consistency summary.
