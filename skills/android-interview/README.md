<!-- markdownlint-disable MD013 -->
# Android Interview

English | [中文](./README.zh-CN.md)

`android-interview` is a Markdown-first skill for structured Android mock interviews from a JD, a resume, and optional Markdown question banks. Claude Code is expected to conduct the main interview flow directly from `SKILL.md` and `references/*.md`, while local Python scripts remain optional helpers for validation, rendering, TTS, and deterministic regression runs.

## Highlights

- Runs a multi-round Android interview flow instead of flat one-off Q&A
- Keeps the main interview intelligence in `SKILL.md` and `references/*.md`
- Uses JD, resume, and question-bank evidence to build a traceable interview plan
- Keeps legacy batch and interactive CLI runners available for fallback, demos, and regression
- Validates external Markdown question banks before the session starts
- Writes local artifacts including `report.html`, `score.json`, `transcript.md`, `screening-summary.md`, and checkpoint files
- Optionally generates TTS audio artifacts when `edge-tts` is installed

## Architecture

This skill is organized around a Markdown-first skill contract plus optional local helpers.

```mermaid
flowchart TD
  A[JD / Resume / Question Bank] --> B[SKILL.md]
  B --> C[references/*.md]
  C --> D[Claude Code Interview Engine]
  D --> E[Questioning / Follow-up / Scoring]
  E --> F[Round Deliberation]
  F --> G[Final Decision]
  G --> H[Optional Scripts]
  H --> I[Local Artifacts]
  H -. legacy .-> J[Deterministic Runtime]
```

- `SKILL.md` defines when to use the skill and the required read order for the references.
- `references/*.md` hold the primary interview behavior: intake, planning, question generation, follow-up, scoring, consistency checks, and reporting.
- `scripts/interview_core.py` holds the deterministic fallback planning, scoring, reporting, and routing logic.
- `scripts/render_skill_artifacts.py` renders local artifacts from structured `session.json` and `score.json` payloads without requiring the legacy runtime to conduct the interview.
- `scripts/run_interactive_session.py` and `scripts/run_interview_session.py` are legacy scripted runtimes for demo, validation, and explicit fallback usage.
- `scripts/ai_client.py`, `scripts/ai_schemas.py`, and `scripts/ai_services.py` provide an optional hot-swappable AI boundary for the scripted runtimes.
- `tests/skills/android-interview/` provides fixtures for repeatable validation.
- `tests/scenarios/android-interview/` and `tooling/run-skill-validation.py` verify the end-to-end behavior.

## Flow

1. Read `SKILL.md` and the required `references/*.md` files.
2. Analyze JD and resume into structured profiles.
3. Plan rounds, personas, question strategy, and output mode in the conversation.
4. Conduct the interview directly in chat, asking one question at a time and following up from evidence gaps.
5. Use scripts only when needed for deterministic helpers such as question-bank validation, rendering, TTS, or scripted regression.
6. Optionally render transcripts, scorecards, panel notes, pass/fail summaries, and HTML reports locally.

## Recommended Usage

Treat the skill conversation as the default product surface.

1. Start in Claude Code or Codex with a JD, a resume, and the target level.
2. Let the assistant read `SKILL.md` and `references/*.md`, then conduct the interview directly in chat.
3. If you need local deliverables, ask for structured outputs and render them with `scripts/render_skill_artifacts.py`.
4. Use the scripted runners only when you explicitly want deterministic fallback, demo runs, or regression validation.

## AI Runtime Modes

The current deterministic implementation has been demoted to a complete fallback path. You can hot-swap behavior with one flag:

- `--ai-mode off`
  - isolate AI completely and run the deterministic fallback end to end
- `--ai-mode assist`
  - try AI scoring/follow-up generation first, then fall back automatically if the provider is unavailable or returns invalid JSON
- `--ai-mode required`
  - require AI; fail fast instead of silently falling back

Provider options:

- `--ai-provider auto|openai-compatible|fixture|none`
- `--model <name>`
- `--ai-fixture-dir /path/to/fixtures`

`openai-compatible` reads `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, and optional `OPENAI_MODEL` from the environment. Each run writes `ai-runtime.json`; AI requests and failures are audited under `ai-calls/`.

## Directory Layout

```text
skills/android-interview/
├── agents/
│   └── openai.yaml
├── references/
│   ├── 00-overview.md
│   ├── 01-intake.md
│   ├── 02-jd-resume-analysis.md
│   ├── 03-interview-flow.md
│   ├── 04-question-generation.md
│   ├── 05-follow-up-policy.md
│   ├── 06-scoring-rubric.md
│   ├── 07-consistency-check.md
│   ├── 08-round-deliberation.md
│   ├── 09-report-output.md
│   └── 10-question-bank-format.md
├── scripts/
│   ├── interview_core.py
│   ├── question_bank.py
│   ├── render_skill_artifacts.py
│   ├── run_interactive_session.py
│   ├── run_interview_session.py
│   ├── run_mvp_demo.py
│   ├── run_resume_demo.py
│   ├── tts_support.py
│   ├── validate_question_bank.py
│   └── requirements.txt
├── README.md
├── README.zh-CN.md
└── SKILL.md
```

## Requirements

- `python3`
- `pip`
- Python packages listed in `skills/android-interview/scripts/requirements.txt`

Install dependencies from the repository root:

```bash
python3 -m pip install -r skills/android-interview/scripts/requirements.txt
```

If you want audio output, keep `edge-tts` installed and add `--enable-tts` to the session command.

## Skill-First Quick Start

Use the skill directly in the chat first. A typical request looks like:

```text
Use the android-interview skill. Here is the JD, here is the resume, target level is senior, and I want a full interview plus local report artifacts.
```

If the conversation already produced structured `session.json` and `score.json` payloads, render the standard local artifacts with:

```bash
python3 skills/android-interview/scripts/render_skill_artifacts.py \
  --session-json /path/to/session.json \
  --score-json /path/to/score.json \
  --output-dir dist/interview-reports/rendered-from-skill
```

## Legacy Runner Quick Start

All commands below assume you are running from the repository root. These commands are for fallback, demo, or regression usage rather than the default skill experience.

### 1. Run the batch MVP demo

```bash
python3 skills/android-interview/scripts/run_mvp_demo.py \
  --session-id local-demo \
  --output-dir dist/interview-reports/local-demo \
  --enable-tts
```

This wrapper uses the repository fixtures under `tests/skills/android-interview/fixtures/` and calls `run_interview_session.py`.

### 2. Run a scripted interactive session

```bash
python3 skills/android-interview/scripts/run_interactive_session.py \
  --jd tests/skills/android-interview/fixtures/jd.md \
  --resume tests/skills/android-interview/fixtures/resume.md \
  --question-bank tests/skills/android-interview/fixtures/question-bank \
  --scripted-answers tests/skills/android-interview/fixtures/answers.json \
  --output-dir dist/interview-reports/local-interactive-demo \
  --session-id local-interactive-demo
```

### 3. Run a real interactive practice session

```bash
python3 skills/android-interview/scripts/run_interactive_session.py \
  --jd /path/to/jd.md \
  --resume /path/to/resume.md \
  --question-bank /path/to/question-bank \
  --output-dir dist/interview-reports/my-session \
  --session-id my-session
```

In live CLI mode, the session supports `/help`, `/status`, `/plan`, `/feedback`, `/scorecard`, `/checkpoint`, `/repeat`, `/skip`, and `/quit`.

## Main Entry Points

- `scripts/run_interview_session.py`
  Batch interview pipeline with scripted answers.
- `scripts/run_interactive_session.py`
  Turn-by-turn interview flow with multiple questions per round, follow-ups, checkpoints, and early termination controls.
- `scripts/run_mvp_demo.py`
  Repository fixture demo for the batch pipeline.
- `scripts/run_resume_demo.py`
  Pause-and-resume demo for checkpoint recovery.
- `scripts/validate_question_bank.py`
  Standalone validator for external Markdown question banks.

## Question Bank Validation

Validate a bank before using it in a real session:

```bash
python3 skills/android-interview/scripts/validate_question_bank.py \
  --question-bank tests/skills/android-interview/fixtures/question-bank \
  --output-dir dist/interview-reports/question-bank-validation
```

The validator reports:

- `question_bank_status`
- `question_count`
- `file_count`
- `error_count`
- `warning_count`

It returns exit code `2` when the bank is invalid, and exit code `3` when `--fail-on-warnings` is set and warnings exist.

## Question Bank Format

Each question file is a Markdown document with YAML frontmatter and structured sections. Example:

```md
---
id: round1-core-001
title: Lifecycle and State Handling
direction: android-core
round: round1
level: senior
difficulty: L3
language: en
tags:
  - lifecycle
  - viewmodel
source: custom-bank
competencies:
  - technical_depth
must_ask: true
follow_up_limit: 2
expected_signal: Candidate can reason about lifecycle transitions and durable state management.
---

## Question

How do you prevent lifecycle-related bugs when a feature has background work and frequently recreated screens?

## Intent

Evaluate lifecycle reasoning, state separation, and practical Android implementation discipline.

## Follow-ups

- Which part belongs in UI state and which part belongs in persistent state?
- How did you verify the fix was stable?

## Scoring Notes

- 1: only textbook lifecycle terms
- 3: workable ViewModel and lifecycle-aware answer
- 5: clear state model, failure mode, and verification path

## Red Flags

- Cannot explain recreation or duplicate work issues

## Good Signals

- Can explain state boundaries
```

Supported values from the current validator:

- `round`: `intro`, `screening`, `round1`, `round2`, `round3`, `hr`
- `level`: `mid`, `senior`, `tl`
- `language`: `zh`, `en`, `bilingual`
- `difficulty`: `L1`, `L2`, `L3`, `L4`, `L5`

## Useful Session Options

- `--mode simulate|screening|round1|round2|round3|hr`
- `--level mid|senior|tl`
- `--language zh|en|bilingual`
- `--enable-tts`
- `--voice en-US-AndrewNeural`
- `--default-persona technical-deep-diver`
- `--round-persona-overrides round2=business-outcome,hr=leadership-evaluator`
- `--round-language-overrides round2=bilingual,hr=zh`
- `--question-target-overrides round1=1,round2=2,round3=1,hr=1`
- `--no-live-feedback`
- `--adaptive-runtime-routing`
- `--deliberation-bridge-probes`
- `--stop-after-questions N`
- `--resume-state /path/to/session-checkpoint.json`
- `--ai-mode off|assist|required`
- `--ai-provider auto|openai-compatible|fixture|none`
- `--model <name>`
- `--ai-fixture-dir /path/to/fixtures`

## Output Artifacts

Session output directories can include:

- `session.json`
- `screening-summary.json`
- `screening-summary.md`
- `session-checkpoint.json`
- `session-progress.json`
- `score.json`
- `ai-runtime.json`
- `ai-calls/`
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
- `mail-reject.html`
- `fail-summary.md`
- `pass-summary.md`
- `tts/`

The exact set depends on whether the run is interactive, whether the candidate passes, and whether TTS is enabled.

## Validation

The repository test plan uses these commands:

```bash
python3 -m pip install pyyaml jinja2 edge-tts
python3 skills/android-interview/scripts/run_mvp_demo.py --session-id local-demo --output-dir dist/interview-reports/local-demo --enable-tts
python3 skills/android-interview/scripts/run_interactive_session.py --jd tests/skills/android-interview/fixtures/jd.md --resume tests/skills/android-interview/fixtures/resume.md --question-bank tests/skills/android-interview/fixtures/question-bank --scripted-answers tests/skills/android-interview/fixtures/answers.json --output-dir dist/interview-reports/local-interactive-demo --session-id local-interactive-demo
python3 tooling/run-skill-validation.py --skill android-interview
```

See `tests/skills/android-interview/MVP_TEST_PLAN.md` for the current acceptance baseline.

## License

This skill lives inside the `hulk-skills` repository, which is licensed under `MIT`.
