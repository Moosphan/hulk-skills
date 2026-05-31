---
name: readme-generator
description: Generate or update a professional README.md for a code repository. Use when the user wants a new README, a rewrite of an existing README, a simpler or shorter README, release-ready polishing, or only specific sections such as quick start, installation, API reference, or contribution guide.
---

# README Generator

Create README content that is accurate, useful, easy to scan, and evidence-first.

## When To Use

Use this skill when the user asks to:

- create a new `README.md`
- rewrite or improve an existing README
- simplify, shorten, or declutter an existing README
- generate only one README section
- prepare a repository README for open source release

## Default Behavior

Default to a single-pass draft. Do not stop after analysis unless:

- the repository evidence is conflicting
- a missing decision would materially change the README
- the user asked for staged review

When you need clarification, ask only the smallest high-impact question.

## Step 1: Detect Mode

Choose one mode before writing:

- `greenfield`: no useful README exists
- `refactor`: a README exists and should be improved
- `partial`: the user requested only specific sections
- `release`: optimize for public/open source consumption

If the user did not specify a mode, infer it from the repository and proceed.
See `references/modes.md` for mode-specific output priorities.

## Step 2: Detect Profile

Choose one profile before writing:

- `minimal`: only the key information needed to understand and use the project
- `standard`: the default balanced README
- `extended`: more complete coverage for larger or more public-facing repositories

If the user explicitly says the README is too long, too complex, too heavy, too verbose,
or asks to simplify it, switch to `minimal`.

If the user says the README is too thin, missing context, or not ready for public release,
consider `extended`.

If the user did not specify a profile, infer it from repository complexity and audience.
See `references/profiles.md`.

## Step 3: Build Evidence First

Inspect the repository before writing. Prioritize:

- package metadata: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`
- lockfiles to infer package manager
- entrypoints and main modules
- existing `README.md`
- config and env templates
- CI files, release files, changelog, license

Build an internal project profile with:

- project type
- core problem solved
- target audience
- primary workflows
- supported install/run paths
- confidence level for each important claim

Only show the profile to the user when it is ambiguous, high-risk, or explicitly requested.

## Step 4: Follow Evidence Rules

Never invent repository facts.

- Do not create badges unless their source can be derived from the repo or provided by the user.
- Do not claim package-manager commands that do not match repository evidence.
- Do not add npm, PyPI, Homebrew, Docker, or crates.io install commands unless publishing evidence exists.
- Do not fabricate API shapes, CLI flags, environment variables, screenshots, URLs, or benchmarks.

When evidence is partial:

- prefer omission over invention
- use conservative wording
- label inferred content clearly

See `references/evidence-policy.md` for the full decision policy.

## Step 5: Identify Project Type

Classify the repository into one primary type:

- CLI tool
- frontend library or component
- backend service or API
- full-stack application
- developer tool or DevOps utility
- library or SDK

Use the primary type to decide which sections deserve the most space.
See `references/project-types.md`.

## Step 6: Generate Only What Matters

Start with the minimum high-value structure:

1. Title
2. One- or two-sentence value proposition
3. Key features or use cases
4. Quick start
5. Installation
6. Configuration or API or commands
7. Contributing and license

Add a table of contents only when the README has more than five major sections.

Avoid empty or ceremonial sections. If a section cannot be supported by evidence, omit it.

When `profile=minimal`, aggressively trim:

- no table of contents unless the README still exceeds six major sections
- no architecture section unless it is core to understanding usage
- no contribution guide unless the user asked for it
- no broad API matrix unless the project truly exposes one
- prefer one runnable example over many variants

## Step 7: Optimize For First Success

Quick start must be runnable by a new user without hidden assumptions.

- include prerequisites when needed
- use the repository's actual package manager
- include required environment-variable setup
- prefer the shortest correct path to first success
- if verification is possible, include a short success check

## Step 8: Keep Language Consistent

Use one language for the whole README unless the user asks for bilingual output.

- keep technical identifiers in their original form
- use fenced code blocks with language tags
- keep prose concise and skimmable
- avoid long marketing copy

## Step 9: Handle Simplification Requests

When a user reacts to an existing README with feedback such as:

- "README 太复杂了"
- "太长了"
- "能不能简化一下"
- "只保留关键信息"
- "做个极简版"

treat this as a simplification request and a refinement request, not a brand-new task.

Default behavior:

1. infer `mode=refactor`
2. infer `profile=minimal`
3. preserve correct project facts
4. compress structure and prose

If the user only expressed dissatisfaction but did not explicitly ask to rewrite, ask one
short confirmation before editing:

`要不要我把它精简成极简版，只保留项目简介、核心特性、最短上手方式和必要配置？`

If the user already asked to simplify, do not pause for another confirmation.

## Step 10: Validate Before Returning

Check for:

- commands that do not match the repo
- missing prerequisites
- undocumented required env vars
- sections that overstate certainty
- examples that do not match code

If the task is to update an existing README, preserve strong existing content unless it is wrong, stale, or redundant.

## Output Style

Return Markdown that is ready to save as `README.md`.

When `profile=minimal`, target a compact result that answers these questions first:

1. what is this project
2. why would someone use it
3. how do they run or install it
4. what must they configure
5. what is the smallest working example

If the user asked for a review-first workflow, provide:

1. a brief project profile
2. key README risks or gaps
3. the proposed README draft
