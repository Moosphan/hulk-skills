[![Platform](https://img.shields.io/badge/Platform-Claude%20Code%20%2B%20Codex-blue)](./README.zh-CN.md)
[![Skills](https://img.shields.io/badge/Skills-3-green)](./README.zh-CN.md)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

# hulk-skills

English | [中文](./README.zh-CN.md)

`hulk-skills` is a personal AI skills monorepo. `Claude Code` is the primary platform, and `Codex` is supported as a compatibility target.

## Highlights

- 3 skills: `word-counter`, `readme-generator`, and `android-interview`
- Dual-platform scenario validation for `Claude Code` and `Codex`
- Buildable install packages for both platforms
- GitHub Release artifacts and CI validation
- MIT licensed

## Architecture

The repository follows a simple source-first model:

- `skills/<skill-name>/` is the canonical skill source
- skill-local `platforms/` folders hold runtime-specific adapters when needed
- `tests/scenarios/` stores real-world cross-platform validation cases
- `tooling/` contains validation and packaging scripts
- `dist/packages/` is the build output for installable archives

## Directory Layout

```text
hulk-skills/
├── .github/workflows/
├── docs/
├── skills/
│   ├── readme-generator/
│   └── word-counter/
├── tests/
│   └── scenarios/
├── tooling/
├── README.md
├── README.zh-CN.md
└── LICENSE
```

## Skills

- `word-counter` - deterministic Chinese / English / mixed text counting
- `readme-generator` - evidence-first README generation and refactoring
- `android-interview` - structured Android mock interviews with local reports and TTS artifacts

## Validation And Packaging

```bash
python3 -m pip install pyyaml
python3 tooling/run-skill-validation.py
python3 tooling/build-skill-packages.py --clean --version local
```

These commands validate the scenario matrix and build installable zip packages for both `Claude Code` and `Codex`.

## Release Outputs

- `dist/packages/claude-code/`
- `dist/packages/codex/`
- `dist/package-manifest-<version>.json`

## More

See [docs/hulk-skills-architecture.md](docs/hulk-skills-architecture.md) for the full architecture, migration rules, and platform strategy.

## License

MIT
