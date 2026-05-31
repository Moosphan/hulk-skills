# README Profiles

Use one profile per task. Profile controls information density, not task type.

## `minimal`

Use when:

- the user asks for a shorter or simpler README
- the project is small, single-purpose, or internal
- the repository has only a few commands or config points
- the current README feels heavier than the product itself

Goals:

- explain the project in under one screen if possible
- make first use obvious in under three minutes
- keep only decision-relevant information

Recommended sections:

1. title
2. one-sentence description
3. key features or primary use cases
4. shortest install or run path
5. smallest usage example
6. necessary configuration
7. license

Default omissions unless clearly needed:

- table of contents
- architecture deep dives
- long background sections
- contribution guide
- exhaustive API reference
- large environment-variable tables

Guardrails:

- prefer 2 to 4 feature bullets
- prefer 3 to 5 quick-start steps
- prefer at most one table
- prefer one example over multiple variants

## `standard`

Use when:

- the user wants a normal polished README
- the repository has moderate complexity
- the project is intended for regular collaboration or public use

Goals:

- balance clarity, completeness, and scanability
- support a new contributor or adopter without overwhelming them

Typical sections:

- title and summary
- key features
- quick start
- installation
- usage
- configuration, commands, or API
- contributing and license when relevant

## `extended`

Use when:

- the project is large or multi-surface
- the repository is release-facing and needs extra context
- the user explicitly asks for a more complete README

Goals:

- provide deeper orientation without becoming a specification dump
- include additional context only when it helps adoption

Possible additions:

- architecture overview
- workflow breakdowns
- compatibility notes
- troubleshooting
- contribution guide

## Simplification Path

When a user first receives a `standard` README and later says it is too complex, too long,
or too detailed:

- reinterpret the request as `profile=minimal`
- keep the same factual base
- reduce section count
- shorten examples
- remove decorative or secondary material

If the user did not explicitly ask to rewrite, confirm once before rewriting. If they did,
rewrite immediately.
