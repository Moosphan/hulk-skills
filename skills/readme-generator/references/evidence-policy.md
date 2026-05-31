# Evidence Policy

Use this policy whenever repository evidence is incomplete.

## Confidence Levels

Assign internal confidence to important claims:

- `confirmed`: directly supported by code, config, or committed docs
- `inferred`: strongly implied by repository structure
- `unknown`: plausible but not supported enough to state as fact

Only `confirmed` claims should be stated as plain fact.

## Badge Rules

Only add badges when the source is discoverable.

- license badge: allowed when a license file exists
- CI badge: allowed when CI workflow identifiers are known
- package version badge: allowed when a publish target is known

Do not guess GitHub owner, repository slug, package name, branch name, or registry.

## Installation Rules

Installation instructions must match repository evidence.

- use `pnpm` if `pnpm-lock.yaml` exists and the repo uses it
- use `yarn` if `yarn.lock` is authoritative
- use `npm` if `package-lock.json` is authoritative
- use `bun` only when the repo actually uses it

If there is no evidence of package publication, prefer local setup instructions over
registry install commands.

## URL Rules

Do not invent:

- homepage URLs
- docs sites
- demo links
- screenshot paths
- API base URLs not present in config or docs

## Existing README Rules

When refactoring an existing README:

- keep correct custom explanations
- remove stale commands
- compress repetition
- preserve useful repository-specific terminology

## Ambiguity Rules

Ask the user only when ambiguity would materially alter the output, for example:

- bilingual vs single-language README
- public release vs internal team usage
- multiple competing install methods with no clear default
- missing repository identity needed for exact badges

Otherwise, proceed with a conservative draft and note assumptions briefly.
