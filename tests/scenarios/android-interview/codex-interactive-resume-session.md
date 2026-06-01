# Android Interview - Codex - Interactive Resume Session

## Scenario

Run the Android interview skill in interactive mode, pause after a few completed questions, then resume from the saved checkpoint and finish the full session.

## Expected Behavior

- The first run writes a resumable `session-checkpoint.json`.
- The resumed run continues from the saved round/question instead of restarting from the beginning.
- The final artifacts overwrite the paused session with a completed pass result.
- `session.json` records `resume_context` so downstream tooling can tell that this report came from a resumed interview.
