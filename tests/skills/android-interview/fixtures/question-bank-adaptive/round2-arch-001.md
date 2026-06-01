---
id: round2-arch-001
title: Modular Boundary and Initialization Design
direction: architecture
round: round2
level: senior
difficulty: L3
language: en
tags:
  - architecture
  - modular
  - startup
  - tradeoff
weight: 1.0
source: adaptive-fixture
competencies:
  - architecture
  - engineering_execution
persona_fit:
  - technical_deep_diver
must_ask: true
follow_up_limit: 2
expected_signal: Candidate can explain how they designed module boundaries, startup impact, and migration risk control.
---

## Question

How did you design Android module boundaries and protect startup stability during migration?

## Intent

Evaluate architecture judgment, migration sequencing, and release risk control.

## Follow-ups

- Why did you keep or change specific module boundaries?
- What did you monitor before rollout?

## Scoring Notes

- 1: only talks about modularization slogans
- 3: explains boundaries and one rollout safeguard
- 5: explains boundary logic, startup impact, phased migration, and risk control

## Red Flags

- Speaks in generalities without real module decisions
- No release gating or monitoring plan

## Good Signals

- Clear boundary rationale
- Startup / ANR measurement
- Phased rollout or rollback protection
