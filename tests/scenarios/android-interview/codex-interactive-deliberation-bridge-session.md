# Android Interview - Codex - Deliberation Bridge Probe Session

## Scenario

Run the Android interview skill in real turn-by-turn mode with round deliberation bridge probes enabled, so a later technical round can be held for one extra targeted probe before the interviewer advances.

## Expected Behavior

- The session still completes with normal structured interview artifacts.
- After the first `round2` review, the panel can hold the round instead of advancing immediately.
- The runner appends one generated technical probe and records the hold action in the turn event log.
- The final report keeps both the transition strategy and the bridge probe evidence together with the normal scoring output.
