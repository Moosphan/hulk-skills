# Android Interview - Codex - Adaptive Routing Session

## Scenario

Run the Android interview skill in real turn-by-turn mode with adaptive runtime routing enabled so the next question in a round can be reordered based on the previous answer quality.

## Expected Behavior

- The session starts from the same structured interview flow as the normal interactive session.
- When a strong answer is detected in a technical round, the runner can promote a harder remaining question before an easier one.
- The turn event log records `adaptive_route` so the route change is auditable.
- The final report and score output keep the adaptive routing evidence together with normal scoring artifacts.
