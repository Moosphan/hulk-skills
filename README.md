[![Platform](https://img.shields.io/badge/Platform-Claude%20Code%20%2B%20Codex-blue)](./README.zh-CN.md)
[![Skills](https://img.shields.io/badge/Skills-7-green)](./README.zh-CN.md)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

# hulk-skills

English | [中文](./README.zh-CN.md)

`hulk-skills` is a curated collection of reusable AI skills, runtimes, and workflow tools for modern coding agents such as `Claude Code`, `Codex`, and similar systems.

It is designed to turn repeatable engineering, content, automation, and productivity tasks into portable agent workflows that can be reused across different platforms.

## Highlights

- 7 skills: `word-counter`, `readme-generator`, `android-interview`, `xiaohongshu-poem-fill`, `food-recipe-post`, `daily-outfit-social-post`, and `clean-voice`
- Local speech extraction, denoising, and natural-language trimming with `clean-voice`, including a DeepSeek Harness installer
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
├── skills/
│   ├── android-interview/
│   ├── clean-voice/
│   ├── daily-outfit-social-post/
│   ├── food-recipe-post/
│   ├── readme-generator/
│   ├── xiaohongshu-poem-fill/
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
- `xiaohongshu-poem-fill` - Xiaohongshu poem-fill post generation with original classical-style lines, hashtag sets, and optional local cover rendering
- `food-recipe-post` - migrated daily recipe social post workflow for Xiaohongshu/Douyin, with baoyu-imagine cover prompts, bright handwritten cover style, and short Chinese cooking copy
- `daily-outfit-social-post` - Xiaohongshu/Douyin OOTD post workflow with fixed creator persona, photorealistic outfit images, continuity locks, and short Chinese captions
- [`clean-voice`](./skills/clean-voice/README.md) - extract speech from local audio/video or supported URLs, separate background music, reduce noise, and edit by timestamps, transcript phrases, or silence; supports Claude Code, Codex, and DeepSeek Harness

## Clean Voice Quick Start

Clone this repository, then install the skill for your assistant:

```bash
git clone https://github.com/Moosphan/hulk-skills.git
cd hulk-skills
python3 skills/clean-voice/scripts/install.py --target codex
```

Replace `codex` with `claude` or `dsh` as needed. Python 3.10+ and FFmpeg/ffprobe are required; model dependencies are prepared separately. Ask your assistant: “Extract the speech from this video, remove the background music, and keep only 00:15–01:10.”

See the [Clean Voice README](./skills/clean-voice/README.md) for setup, CLI examples, and limitations. Its installers and CLI are tested; natural-language invocation has not been verified in all three assistant sessions. Separation may retain overlapping speech, singing, or effects.

## Validation And Packaging

```bash
python3 -m pip install pyyaml
python3 tooling/run-skill-validation.py
python3 tooling/build-skill-packages.py --clean --version local
```

These commands validate the scenario matrix and build installable zip packages for both `Claude Code` and `Codex`.

Skills may list extra runtime files in `package-files.txt`; the packager includes these alongside the standard skill resources. Clean Voice uses this to ship its Python core and portable installer dependencies. Its focused validation is:

```bash
python3 tooling/run-skill-validation.py --skill clean-voice
python3 -m unittest discover -s skills/clean-voice/tests -v
python3 -m unittest discover -s tests/tooling -v
```

## Release Outputs

- `dist/packages/claude-code/`
- `dist/packages/codex/`
- `dist/package-manifest-<version>.json`

## More

The repository structure and validation flow above reflect the current source-of-truth. For skill-specific details, check each skill directory under `skills/`.

## License

MIT
