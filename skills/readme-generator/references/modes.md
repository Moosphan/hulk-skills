# README Modes

Use one mode per task.

Mode answers "what kind of README task is this?".
Profile answers "how dense should the README be?".

Choose mode first, then profile. See `profiles.md`.

## `greenfield`

Use when the repository has no README or only a placeholder.

Priorities:

1. explain what the project is
2. show the fastest path to run or use it
3. document only the most important commands or API surface

## `refactor`

Use when a README already exists and should be improved.

Priorities:

1. keep strong existing sections
2. remove stale, repetitive, or unsupported claims
3. reorganize for faster scanning
4. preserve repository-specific voice when it is good

Before rewriting, compare the existing README against repository evidence and note:

- outdated commands
- missing setup steps
- vague value proposition
- duplicated sections
- unsupported badges or claims

## `partial`

Use when the user asks for only one area such as:

- quick start
- installation
- configuration
- API reference
- contribution guide

Generate only the requested sections plus any tiny dependency section that is required
for correctness.

## `release`

Use when the repository is being prepared for public or open source visibility.

Priorities:

1. clear value proposition in the first screen
2. practical quick start
3. trust signals backed by evidence
4. concise feature framing and audience fit

Add badges only when the repository supports them. Good candidates include:

- license
- CI status
- package version

Skip vanity badges unless the user explicitly wants them.
