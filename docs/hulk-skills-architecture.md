# Hulk Skills Project Architecture

## 1. Project Positioning

`hulk-skills` is intended to be an open-source monorepo for personal AI skills.
It should serve three goals at the same time:

1. Aggregate multiple reusable skills in one repository.
2. Keep each skill self-contained, portable, and easy to install.
3. Provide a clean base for future growth, including tooling, validation, and distribution.

This repository should not become a loose dump of unrelated skill repos.
Instead, it should evolve into a curated skills workspace with consistent structure,
naming, maintenance rules, and upgrade paths.

## 2. Repository Design Principles

### Skill-first

Every skill should be independently understandable and runnable from its own directory.
The smallest usable unit in this repo is `skills/<skill-name>/`.

### Monorepo with light governance

Keep all skills in one repository, but avoid over-centralized coupling.
Each skill may have its own scripts, references, and assets, while shared tooling lives at repo level.

### Progressive disclosure

Keep `SKILL.md` concise and procedural.
Detailed references belong in `references/`.
Deterministic logic belongs in `scripts/`.

### Runtime-friendly

The repo should prefer structures that work well for `Claude Code` as the primary platform,
while leaving room to support `Codex` and other agent runtimes through adapters.

### Multi-platform canonical source

Each skill should have one canonical source of truth, then expose platform-specific adapters
only where the runtime requires it. Do not fork the skill logic per platform unless the runtime
actually changes behavior.

### Source normalization over raw vendoring

When migrating from standalone skill repos, prefer extracting the real skill package and its
essential resources instead of copying every upstream repository artifact into the monorepo root.

## 3. Recommended Repository Layout

```text
hulk-skills/
├── docs/
│   ├── hulk-skills-architecture.md
│   ├── roadmap.md                       # optional
│   └── migration-notes/                # optional
├── skills/
│   ├── word-counter/
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   └── openai.yaml             # optional Codex/OpenAI metadata
│   │   ├── platforms/
│   │   │   └── claude-code/            # optional runtime adapter files
│   │   ├── references/
│   │   ├── scripts/
│   │   └── assets/                     # optional
│   └── readme-generator/
│       ├── SKILL.md
│       ├── agents/                     # optional
│       ├── platforms/                  # optional
│       ├── references/
│       ├── scripts/                    # optional
│       └── assets/                     # optional
├── templates/
│   └── skill/
│       ├── SKILL.md
│       └── agents/openai.yaml
├── tooling/
│   ├── validate-skills.sh              # optional
│   ├── sync-runtime.sh                 # optional
│   ├── package-skills.py               # optional
│   └── run-skill-validation.py         # optional
├── tests/
│   ├── skills/                         # deterministic skill-level tests
│   └── scenarios/                      # real-world cross-platform validation cases
├── README.md                           # repo-level overview
└── .gitignore
```

## 4. Directory Responsibilities

### `skills/`

This is the core catalog.
Each child directory is one installable or portable skill package.

### `docs/`

Holds repository-level design decisions, migration notes, publishing strategy,
contribution rules, and roadmap materials.
Do not place agent runtime instructions here if they belong inside a specific skill.

### `templates/`

Stores starter templates for new skills.
This helps keep newly added skills structurally consistent.

### `tooling/`

Holds repo-wide maintenance scripts, such as:

- validation
- packaging
- installation helpers
- metadata generation
- synchronization across runtimes

### `tests/`

Stores deterministic tests that do not belong inside a single runtime package,
especially when shared scripts or parsing logic need regression coverage.
It should also hold scenario-based validation assets for real prompts across
`Claude Code` and `Codex`.

## 5. Platform Adaptation Strategy

The repository should treat `Claude Code` as the primary target platform and `Codex` as a
first-class compatibility target.

### Canonical model

- Keep one canonical skill directory per skill.
- Put shared instructions, rules, scripts, and references in that directory.
- Store platform-specific glue only when a runtime needs a different install shape or metadata format.

### Claude Code rules

- Prefer `skills/<skill-name>/SKILL.md` as the primary agent entry.
- Keep Claude Code as the canonical installation and runtime path for the skill.
- If a skill needs Claude-specific installation or wrapper files, keep them close to the skill
  as the default platform output.
- Claude-only instructions should stay in the canonical skill body only when they are truly shared.

### Codex rules

- Keep Codex-facing metadata in `agents/openai.yaml` when available.
- Treat Codex packaging as a compatibility layer unless the skill is explicitly Codex-first.
- If a skill is Codex-only for now, say so explicitly instead of pretending it is portable.

### Shared compatibility rules

- Do not duplicate business logic across platform folders.
- Keep prompts, counting rules, evidence policies, and other domain rules in one canonical place.
- Prefer generated platform artifacts over manually maintained copies when the formats diverge.
- When a skill cannot be made cross-platform cleanly, document the limitation in `docs/`.

### Recommended delivery pattern

1. Canonical skill lives under `skills/<skill-name>/`.
2. Claude Code output is the default platform artifact.
3. Codex metadata and adapters are generated or maintained beside it.
4. Release artifacts are treated as build outputs, not the source of truth.

## 6. Skill Directory Specification

Each skill should follow this baseline:

```text
skills/<skill-name>/
├── SKILL.md
├── agents/
│   └── openai.yaml             # optional Codex/OpenAI metadata
├── platforms/
│   ├── claude-code/            # default runtime-specific adapter files
│   └── codex/                  # optional compatibility adapter files
├── references/                 # optional
├── scripts/                    # optional
└── assets/                     # optional
```

### Required

- `SKILL.md`

### Recommended

- `agents/openai.yaml`
- `references/`

### Optional

- `platforms/`
- `scripts/`
- `assets/`

## 7. Skill Authoring Rules

### Naming

- Use kebab-case for directory names, such as `word-counter`.
- Keep the `name:` field in `SKILL.md` aligned with the directory name whenever possible.
- Avoid runtime-specific names in the directory unless the skill is truly runtime-bound.

### `SKILL.md`

- Keep it focused on workflow and usage triggers.
- Prefer less than 500 lines.
- Put long explanations, examples, rules, and edge cases into `references/`.
- Avoid duplicating reference content inside `SKILL.md`.

### References

- Put exact rules, formulas, taxonomies, decision tables, and longer examples in `references/`.
- Prefer one level of navigation from `SKILL.md`.

### Scripts

- Put deterministic logic in `scripts/`.
- Scripts should be runnable directly and not depend on hidden local state.
- Prefer portable shell or Python entrypoints unless a stronger dependency is necessary.

### Assets

- Only include assets that are used by the skill output or workflow.
- Avoid turning skill directories into general project dumps.

## 8. Dual-platform Validation Strategy

The repository should validate each important skill in real usage scenarios on both
`Claude Code` and `Codex`, not only through static structure checks.

### Validation layers

#### Layer 1: Structure validation

Checks that:

- required files exist
- directory naming is consistent
- metadata files are readable
- no nested Git state is present

#### Layer 2: Deterministic logic validation

Checks scripts and rule-driven outputs that can be verified locally, such as:

- parser behavior
- counting formulas
- generated markdown structure
- fixture-based expected outputs

#### Layer 3: Scenario validation

Uses realistic prompts and repository inputs to verify that the skill behaves correctly
from an end-user perspective.

Examples:

- `word-counter`: mixed Chinese-English chapter count, concise output, detailed output, file input
- `readme-generator`: greenfield README generation, README simplification, release-oriented rewrite

#### Layer 4: Cross-platform runtime validation

The same scenario should be checked on both `Claude Code` and `Codex` when the skill claims
dual-platform support.

The validation should confirm:

- the skill can be discovered or invoked on each platform
- the expected adapter files are present
- the skill follows platform-specific install and runtime conventions
- the output stays semantically aligned across platforms

### Minimum validation requirement per skill

Each maintained skill should eventually have:

1. one structure check
2. one deterministic fixture test if scripts or formulas are involved
3. at least two realistic scenario cases
4. at least one `Claude Code` validation record
5. at least one `Codex` validation record if Codex compatibility is claimed

### Recommended scenario format

Each scenario case should describe:

- skill name
- scenario name
- target platform
- input prompt
- optional input files or fixtures
- expected behavior
- acceptance criteria
- notes about known platform differences

### Acceptance criteria examples

- the skill is actually selected or invoked
- no unsupported commands are invented
- output language follows the user language
- output structure matches the contract defined by the skill
- platform-specific metadata is sufficient for execution
- important claims are grounded in repository evidence

### Validation artifact recommendations

Store cross-platform scenarios under `tests/scenarios/` and deterministic checks under `tests/skills/`.
When possible, keep scenario definitions machine-readable so they can later be consumed by CI or
tooling scripts.

Recommended layout:

```text
tests/
├── skills/
│   └── word-counter/
│       └── fixtures/                   # optional deterministic inputs
└── scenarios/
    ├── validation-matrix.yaml
    ├── word-counter/
    │   ├── claude-code-mixed-text.md
    │   └── codex-mixed-text.md
    └── readme-generator/
        ├── claude-code-simplify-readme.md
        └── codex-simplify-readme.md
```

### Repository-level validation workflow

Recommended execution order:

1. run structure validation
2. run deterministic script tests
3. run scenario validation for `Claude Code`
4. run scenario validation for `Codex`
5. compare behavior differences and record exceptions

The default CI implementation should be GitHub Actions and live in
`.github/workflows/skill-validation.yml`.
The same workflow should also build installable package artifacts for both
`Claude Code` and `Codex` and upload them as CI artifacts.
Release publishing should live in `.github/workflows/release-packages.yml` and
attach the same package set to GitHub Releases.

### Package outputs

The build step should publish zipped install packages under `dist/packages/`:

```text
dist/packages/
├── claude-code/
│   └── <skill-name>-claude-code-<version>.zip
└── codex/
    └── <skill-name>-codex-<version>.zip
```

Each archive should contain a ready-to-install skill directory, not the raw repo root.
The build process should also emit a manifest that lists package names, platforms, and hashes.

### Policy for platform support claims

- Do not mark a skill as dual-platform ready until both platforms have scenario evidence.
- If only one platform has been verified, document the other as unverified rather than assumed.
- If outputs intentionally differ by platform, document the allowed difference explicitly.

## 9. Migration Rules For Existing Skill Repositories

When importing a standalone skill repo into `hulk-skills`, use the following rules:

1. Identify the actual skill package entry.
2. Extract only the skill directory and the resources required for it to work.
3. Move it into `skills/<skill-name>/`.
4. Re-home shared repo tooling only if it still provides value in the monorepo.
5. Do not preserve nested Git metadata.
6. Record any non-obvious migration decisions in `docs/` if needed.

### What should usually be migrated

- `SKILL.md`
- `agents/openai.yaml` if present
- `references/`
- `scripts/` required by the skill
- `assets/` if the skill depends on them

### What should usually not be migrated directly

- per-repo install scripts that assume a single-skill repository layout
- duplicate README variants inside each skill directory
- release automation that only made sense for the standalone repo
- nested `.git/` directories or Git submodule state

## 10. Migration Decisions For The Current Two Skills

### `word-counter-skill`

Source repo contains:

- the real skill package under `skills/codex/word-counter/`
- optional Claude runtime packaging
- standalone repo release and packaging scripts
- Python implementation and tests outside the packaged skill

Recommended migration target:

- move the packaged skill into `skills/word-counter/`
- keep Claude Code as the default runtime shape
- preserve Codex compatibility through metadata and adapters
- do not carry over nested standalone repo Git state
- add real-scenario validation for both `Claude Code` and `Codex`
- consider moving shared tests or packaging logic later only if this monorepo will maintain them

### `readme-generator-skill`

Source repo contains:

- a single `readme-generator/` skill directory
- standalone install scripts
- repo-level bilingual README files

Recommended migration target:

- move `readme-generator/` into `skills/readme-generator/`
- keep `references/`
- default the runtime layout to Claude Code
- preserve Codex compatibility through metadata and adapters
- drop nested repo Git state
- add real-scenario validation for both `Claude Code` and `Codex`
- defer install script redesign to repo-level tooling later

## 11. Repository Norms

### Language policy

- Prefer English for directory names, filenames, and machine-facing metadata.
- Repository-level docs may be written in Chinese when that better fits the maintainer audience.
- If bilingual docs are added, keep one canonical source and one translated companion, not many drifting copies.

### Documentation policy

- Skill-internal documentation should serve the agent.
- Repo-level documentation should serve maintainers and contributors.
- Avoid adding redundant `README.md` files to every skill unless they provide real installation or maintenance value.

### Git policy

- This repository is the only Git root.
- Imported skills must not retain nested `.git` directories.
- If a source repo was cloned locally for migration, clean its Git metadata before final placement.

### Versioning policy

- Start with monorepo-level versioning discipline before per-skill semver.
- Once skill count grows, consider adding a changelog or release notes per skill.

### Validation policy

- New skills should not be considered complete without at least one realistic scenario case.
- Skills that claim multi-platform support should carry validation evidence for every claimed platform.
- Regression fixes should add or update a deterministic or scenario-based test whenever practical.

## 12. Suggested Next Steps

### Near term

1. Add a root `README.md` that explains what `hulk-skills` is and lists available skills.
2. Add a `templates/skill/` starter for future additions.
3. Add a lightweight validation script to check that every skill has `SKILL.md`.
4. Add a dual-platform scenario matrix for `Claude Code` and `Codex`.
5. Add GitHub Actions CI for repository validation.
6. Add a simple contribution guide for adding new skills.
7. Add a release workflow that can publish build artifacts.

### Mid term

1. Add repo-level install/export tooling for Claude Code and Codex.
2. Add CI to validate directory structure, basic script execution, and scenario matrices.
3. Add a generated skill index for discoverability.
4. Add automated cross-platform validation reports.

### Long term

1. Introduce metadata-driven packaging and publishing.
2. Support multiple runtimes from one canonical skill source when needed.
3. Build a stronger skill quality bar with linting, smoke tests, and sample prompts.

## 13. Practical Rule Of Thumb

If a file helps one skill do its job, keep it inside that skill directory.
If a file helps the repository manage many skills, keep it at repo level.
