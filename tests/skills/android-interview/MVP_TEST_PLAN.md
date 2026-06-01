# Android Interview MVP Test Plan

## Goal

Verify that the Android interview MVP forms a closed loop from inputs to local artifacts and TTS outputs.
The current validation baseline also checks multi-question rounds, `round3`, and generated fallback questions when the external Markdown bank does not fully cover the planned round focus.

## Scope

- JD input
- resume input
- Markdown question bank import
- dynamic fallback questions when the bank does not fully cover a round
- scripted candidate answers
- scoring output
- transcript output
- HTML report output
- TTS output via `edge-tts`

## Main Validation Command

```bash
python3 -m pip install pyyaml jinja2 edge-tts
python3 skills/android-interview/scripts/run_mvp_demo.py --session-id local-demo --output-dir dist/interview-reports/local-demo --enable-tts
python3 skills/android-interview/scripts/run_interactive_session.py --jd tests/skills/android-interview/fixtures/jd.md --resume tests/skills/android-interview/fixtures/resume.md --question-bank tests/skills/android-interview/fixtures/question-bank --scripted-answers tests/skills/android-interview/fixtures/answers.json --output-dir dist/interview-reports/local-interactive-demo --session-id local-interactive-demo
python3 tooling/run-skill-validation.py --skill android-interview
```

## Required Artifacts

Each scenario should produce:

- `session.json`
- `screening-summary.json`
- `screening-summary.md`
- `score.json`
- `interview-plan.json`
- `turn-events.json` for interactive mode
- `transcript.md`
- `report.html`
- `pass-summary.md` when the candidate passes
- `tts/opening.mp3`
- `tts/questions.mp3`
- `tts/summary.mp3`

## Acceptance Criteria

- The session runner exits with code `0`
- The final decision is printed
- TTS status is `generated`
- The local artifact directory exists
- The screening summary exists and contains pre-interview fit signals
- The score file contains question-level evidence
- The pass scenario writes `pass-summary.md`
- The score file shows multiple questions across technical rounds and includes `round3`
- Interactive scenarios record `switch_topic` when the session moves to a new topic inside the same round
- Adaptive routing scenarios record `adaptive_route` when the next question is reordered inside the same round
- Failure scenarios write `mail-reject.html` and `fail-summary.md`
- The report file is readable HTML

## Current Fixture Set

- `fixtures/jd.md`
- `fixtures/resume.md`
- `fixtures/answers.json`
- `fixtures/question-bank/`

## Current Validation Tooling

- `tooling/run-skill-validation.py`
- `skills/android-interview/scripts/run_interview_session.py`
