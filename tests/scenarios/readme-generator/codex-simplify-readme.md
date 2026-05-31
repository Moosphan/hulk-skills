# README Generator - Codex - Simplify README

## Scenario

Use the `readme-generator` skill in `Codex` to simplify an overly long project README.

## Input

`这份 README 太长了，请帮我改成极简版，只保留项目简介、核心特性和最短上手方式。`

## Expected Behavior

- The skill treats the request as a simplification/refactor task.
- The output is significantly shorter than a standard release README.
- Repository facts are preserved.
- The draft stays evidence-first and does not invent unsupported commands or claims.

## Acceptance Criteria

- The result keeps a minimal README structure.
- The result avoids fabricated badges, URLs, commands, or package-manager claims.
- The output is suitable to be saved directly as `README.md`.

