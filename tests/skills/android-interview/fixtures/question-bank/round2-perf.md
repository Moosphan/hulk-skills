---
id: round2-perf-001
title: Cold Start Optimization
direction: performance
round: round2
level: senior
difficulty: L4
language: en
tags:
  - android
  - startup
  - performance
  - tracing
  - benchmark
weight: 0.98
source: mvp-fixture
competencies:
  - technical_depth
  - architecture
  - engineering_execution
persona_fit:
  - technical_deep_diver
  - cross_examiner
must_ask: true
follow_up_limit: 2
expected_signal: Candidate can explain startup diagnosis, tradeoffs, metrics, and regression control.
---

## Question

How did you diagnose and optimize cold start time in a large Android application?

## Intent

Evaluate practical performance diagnosis ability, tradeoff reasoning, and ownership depth.

## Follow-ups

- Which optimizations had the highest ROI?
- What regressions did you guard against?

## Scoring Notes

- 1: only generic performance concepts
- 3: can explain metrics, tools, and one concrete optimization
- 5: can describe baseline, critical path, tradeoffs, rollout, and regression prevention

## Red Flags

- No metrics
- No diagnosis path
- No regression strategy

## Good Signals

- Uses measurement before optimization
- Can explain ROI tradeoffs
- Has rollback or release protection plan
