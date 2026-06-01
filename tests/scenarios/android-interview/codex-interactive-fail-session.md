# Android Interview - Codex - Interactive Failure Session

## Scenario

Run the Android interview skill in interactive mode with weak scripted answers so that the session terminates early and writes failure artifacts.

## Expected Behavior

- The session stops early on a clear failure path instead of continuing all rounds.
- The runner writes `mail-reject.html`, `fail-summary.md`, and `interview-plan.json`.
- The session output marks `session_terminated` and records a concrete termination reason.
