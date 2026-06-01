---
name: android-interview
description: Simulate a structured Android interview for Chinese candidates using a real JD, resume, and optional external Markdown question banks. Use when the user wants a candidate-facing mock interview, multi-round evaluation, evidence-based scoring, local HTML interview reports, or TTS interview artifacts.
---

# Android Interview

Run a structured Android mock interview that feels like a real senior interviewer instead of a random Q&A bot.

## When To Use

Use this skill when the user wants to:

- simulate a real Android interview from a JD and resume
- practice senior or TL-level Android interviews
- use external Markdown question banks for targeted deep dives
- run a true round-by-round interview with multiple questions inside a round instead of a single flat Q&A
- generate local interview artifacts such as `report.html`, `score.json`, and `transcript.md`
- generate TTS audio artifacts for the interviewer opening and summary

## Default Mode

- primary audience: candidate self-practice
- default level: `senior` / `tl`
- default language: immersive English
- default output: local artifacts under `dist/interview-reports/`

## Inputs

- JD text or Markdown
- resume text or Markdown
- optional external question bank file or directory
- optional answer fixture for scripted validation

## Main Scripts

- `scripts/run_interview_session.py`
  - runs the batch MVP interview pipeline
- `scripts/run_mvp_demo.py`
  - runs the default MVP demo using repository fixtures
- `scripts/run_interactive_session.py`
  - runs a turn-by-turn interview with round intros, multiple questions per round, follow-up/challenge stages, round summaries, generated fallback questions, checkpoint writes, and early termination
- `scripts/run_resume_demo.py`
  - runs a controlled pause-and-resume demo to verify checkpoint recovery
- `scripts/question_bank.py`
  - parses Markdown question banks
- `scripts/validate_question_bank.py`
  - validates external Markdown question banks and writes auditable validation artifacts
- `scripts/tts_support.py`
  - generates TTS artifacts with `edge-tts` when available

## Typical Command

```bash
python3 skills/android-interview/scripts/run_interactive_session.py \
  --jd tests/skills/android-interview/fixtures/jd.md \
  --resume tests/skills/android-interview/fixtures/resume.md \
  --question-bank tests/skills/android-interview/fixtures/question-bank \
  --scripted-answers tests/skills/android-interview/fixtures/answers.json \
  --output-dir dist/interview-reports/demo \
  --session-id demo-interactive \
  --enable-tts
```

## Customization

- `--default-persona technical-deep-diver`
  - apply one interviewer persona preset to all rounds unless a round override is provided
- `--round-persona-overrides round2=business-outcome,hr=leadership-evaluator`
  - override persona presets for specific rounds
- `--round-language-overrides round2=bilingual,hr=zh`
  - override the language mode for specific rounds so technical and HR interviews can mix English, bilingual, and Chinese
- `--question-target-overrides round1=1,round2=1,round3=1,hr=1`
  - reduce or expand how many main questions each round should contain
- `--no-live-feedback`
  - disable the automatic per-question live feedback stream in interactive mode
- `--adaptive-runtime-routing`
  - reorder the remaining questions inside a round when the last answer suggests we should add pressure, lower difficulty, or switch focus earlier
- `--deliberation-bridge-probes`
  - allow later technical rounds to hold once for one extra targeted probe before advancing, so the panel decision can actually affect runtime flow

## Output Artifacts

The script writes a session directory that includes:

- `session.json`
- `screening-summary.json`
- `screening-summary.md`
- `session-checkpoint.json`
- `session-progress.json`
- `score.json`
- `interview-plan.json`
- `panel-notes.json`
- `panel-notes.md`
- `question-bank-validation.json`
- `question-bank-validation.md`
- `resume-prep.json`
- `resume-prep.md`
- `turn-events.json`
- `transcript.md`
- `report.html`
- `mail-reject.html` when the candidate does not pass
- `fail-summary.md` when the candidate does not pass
- `pass-summary.md` when the candidate passes
- `tts/` audio files when TTS is enabled and `edge-tts` is installed

## Interview Behavior

- starts with a self-introduction round
- generates a resume preparation brief before the interview so candidates can rewrite their resume and opening narrative before practice
- runs multiple questions in the same round for `round1`, `round2`, `round3`, and `hr`
- prefers external Markdown bank questions first
- validates the imported Markdown question bank before the session starts and records schema / quality warnings locally
- generates deterministic fallback questions when the bank does not fully cover a round
- records stage events such as `intro`, `questioning`, `follow_up`, `challenge`, `switch_topic`, `summary`, and `advance` / `reject`
- writes planning and failure artifacts such as `interview-plan.json` and `fail-summary.md`
- writes pre-interview screening artifacts so the flow is traceable from resume/JD screening through the final interview report
- in live CLI mode, supports `/help`, `/status`, `/plan`, `/feedback`, `/scorecard`, `/checkpoint`, `/repeat`, `/skip`, and `/quit`
- can emit automatic per-question live feedback after each completed answer unless `--no-live-feedback` is used
- supports configurable interviewer persona presets and per-round question target overrides
- can trigger runtime consistency challenges when a later answer conflicts with earlier ownership or metrics evidence
- emits an explicit round deliberation step before each round-level advance or reject decision
- supports adaptive runtime routing that can promote a harder or more relevant remaining question inside the same round
- can optionally hold a later technical round for one targeted bridge probe before the panel advances
- can carry one round’s review outcome into the next round’s opening strategy and first-question routing
- supports `--stop-after-questions` and `--resume-state` for checkpointed pause/resume flows
- performs cross-question consistency checks so the final report can surface mixed signals instead of only single-question scores

## Validation

Use the repository validation tooling to run both batch and interactive scenarios and check that all expected artifacts are produced.
