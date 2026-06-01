---
name: android-interview
description: Run a Markdown-first Android interview skill for Chinese candidates. The primary interview engine is Claude Code reading structured references, while local scripts remain optional helpers for question-bank validation, report rendering, TTS, demo runs, and deterministic fallback validation.
---

# Android Interview

This skill should behave like a serious structured Android interview conducted directly in the conversation, not like a thin wrapper around a Python CLI.

## When To Use

Use this skill when the user wants to:

- simulate a real Android interview from a JD and resume
- practice senior or TL-level Android interviews
- receive evidence-based questioning, follow-up, scoring, and pass/fail judgment
- use external Markdown question banks as optional input
- generate interview artifacts such as `report.html`, `score.json`, `transcript.md`, or screening notes

## Core Principle

Claude Code itself is the primary interview engine.

- Read `references/*.md` to drive the interview flow, follow-up strategy, scoring, consistency checks, and reporting behavior.
- Use local scripts only for deterministic helper work such as question-bank parsing, validation, HTML rendering, TTS, demo runs, or regression validation.
- Do not default to running the legacy Python runtime just to conduct the interview. Only use it when the user explicitly asks for batch/demo mode, deterministic fallback validation, or artifact generation that truly needs the scripts.

## Required Read Order

When this skill is invoked, use the following progression:

1. Read [references/00-overview.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/00-overview.md).
2. Read [references/01-intake.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/01-intake.md) to normalize inputs and defaults.
3. If JD/resume are provided, read [references/02-jd-resume-analysis.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/02-jd-resume-analysis.md) and produce structured profiles.
4. Read [references/03-interview-flow.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/03-interview-flow.md) to choose rounds and runtime state.
5. Read [references/04-question-generation.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/04-question-generation.md) before selecting or generating a question.
6. During each answer cycle, use [references/05-follow-up-policy.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/05-follow-up-policy.md) and [references/06-scoring-rubric.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/06-scoring-rubric.md).
7. Use [references/07-consistency-check.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/07-consistency-check.md) whenever later answers may contradict earlier claims.
8. At the end of each round, apply [references/08-round-deliberation.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/08-round-deliberation.md).
9. When producing deliverables, follow [references/09-report-output.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/09-report-output.md).
10. If a question bank is supplied, consult [references/10-question-bank-format.md](/Users/dorck/Documents/hulk-skills/skills/android-interview/references/10-question-bank-format.md) before reading or validating it.

## Default Behavior

- primary audience: candidate self-practice
- default level: `senior` / `tl`
- default language: immersive English
- default shape: full interview plus evaluation summary
- default output mode: in-conversation result, with local artifacts only when useful or requested

## Conversation Mode

Unless the user explicitly asks for batch mode or scripted demo mode, conduct the interview inside the chat:

- analyze JD and resume
- explain the planned rounds briefly
- ask one question at a time
- follow up based on evidence gaps
- score answers using the rubric
- perform round deliberation
- summarize the final decision and improvement areas

## Script Usage Policy

Use scripts only when they clearly add value:

- `scripts/question_bank.py`
  - optional helper for parsing Markdown question-bank metadata
- `scripts/validate_question_bank.py`
  - optional helper for validating an external Markdown bank before use
- `scripts/render_skill_artifacts.py`
  - optional helper for rendering local report artifacts from structured `session.json` and `score.json` payloads produced in the conversation
- `scripts/run_interactive_session.py`
  - legacy deterministic runtime for demo, regression, or explicit scripted mode
- `scripts/run_interview_session.py`
  - legacy batch runtime for demo, regression, or explicit scripted mode
- `scripts/run_mvp_demo.py`, `scripts/run_resume_demo.py`
  - legacy validation/demo wrappers
- `scripts/tts_support.py`
  - optional helper for audio artifacts

If you decide to use a script, say why that helper is needed and keep the reasoning and judgment in the conversation whenever possible.

## Outputs

Primary outputs should be structured interview results that can be delivered in chat or written locally:

- structured screening summary
- round-by-round transcript or notes
- score summary with evidence
- final pass / fail / borderline recommendation
- improvement suggestions
- optional local artifacts such as `report.html`, `score.json`, `transcript.md`, `session.json`

## Legacy Runtime Note

The existing Python runtime is a deterministic fallback and validation toolchain, not the canonical source of interviewer intelligence.

Use it only when:

- the user explicitly asks for scripted or batch mode
- the repo validation matrix needs to run
- offline deterministic regression is desired
- a helper script is needed to render or validate artifacts
