[![平台](https://img.shields.io/badge/Platform-Claude%20Code%20%2B%20Codex-blue)](./README.md)
[![Skill 数量](https://img.shields.io/badge/Skills-3-green)](./README.md)
[![协议](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

# hulk-skills

[English](./README.md) | 中文

`hulk-skills` 是一个个人 AI skills 的 monorepo 仓库，当前以 `Claude Code` 为主平台，同时兼容 `Codex`。

## 项目亮点

- 当前包含 3 个 skill：`word-counter`、`readme-generator` 和 `android-interview`
- 覆盖 `Claude Code` 与 `Codex` 的真实场景验证
- 可以构建两平台的可安装 skill 包
- 已接入 GitHub Actions 校验与 GitHub Release 产物发布
- 使用 `MIT` 协议

## 架构说明

仓库采用“源码优先”的组织方式：

- `skills/<skill-name>/` 是 skill 的 canonical source
- skill 内的 `platforms/` 目录用于放置平台适配层
- `tests/scenarios/` 存放双平台真实场景验证用例
- `tooling/` 存放校验与打包脚本
- `dist/packages/` 是最终安装包产物目录

## 目录结构

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

## 当前 Skills

- `word-counter` - 用于中英文和混排文本的确定性字数统计
- `readme-generator` - 用于基于仓库证据生成或重构 README
- `android-interview` - 用于结构化 Android 模拟面试、本地报告与 TTS 语音产物生成

## 本地校验与构建

```bash
python3 -m pip install pyyaml
python3 tooling/run-skill-validation.py
python3 tooling/build-skill-packages.py --clean --version local
```

这些命令会执行双平台场景校验，并产出适用于 `Claude Code` 和 `Codex` 的安装包 zip。

## 产物目录

- `dist/packages/claude-code/`
- `dist/packages/codex/`
- `dist/package-manifest-<version>.json`

## 更多信息

完整的项目架构、迁移规范、平台适配策略见 [docs/hulk-skills-architecture.md](docs/hulk-skills-architecture.md)。

## License

MIT
