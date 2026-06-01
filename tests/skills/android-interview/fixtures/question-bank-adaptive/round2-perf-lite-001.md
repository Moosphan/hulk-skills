---
id: round2-perf-lite-001
title: Startup Diagnostics Basics
direction: performance
round: round2
level: senior
difficulty: L2
language: en
tags:
  - performance
  - startup
  - tracing
weight: 0.6
source: adaptive-fixture
competencies:
  - technical_depth
  - problem_solving
persona_fit:
  - guided_mentor
must_ask: false
follow_up_limit: 2
expected_signal: Candidate can explain the basic diagnosis path and one practical optimization.
---

## Question

Walk me through a smaller startup optimization case where you first found the bottleneck and then made one safe improvement.

## Intent

Check whether the candidate can start from measurement and avoid overengineering.

## Follow-ups

- What data told you where to start?
- How did you make sure the fix did not cause regression?

## Scoring Notes

- 1: generic performance talk
- 3: can describe one measurement and one safe fix
- 5: can explain the measurement path, fix, and regression guardrails

## Red Flags

- No concrete measurement
- No regression protection

## Good Signals

- Measurement-first thinking
- Clear rollback or verification plan
