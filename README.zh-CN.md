[![平台](https://img.shields.io/badge/Platform-Claude%20Code%20%2B%20Codex-blue)](./README.md)
[![Skill 数量](https://img.shields.io/badge/Skills-6-green)](./README.md)
[![协议](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

# hulk-skills

[English](./README.md) | 中文

`hulk-skills` 是一个面向现代 coding agents 的可复用 AI skills、runtime 与 workflow tools 集合，适用于 `Claude Code`、`Codex` 以及类似系统。

它的目标是把工程、内容、自动化与日常效率场景中的可重复任务，沉淀为可跨平台复用的 agent workflow。

## 项目亮点

- 当前包含 6 个 skill：`word-counter`、`readme-generator`、`android-interview`、`xiaohongshu-poem-fill`、`food-recipe-post` 和 `daily-outfit-social-post`
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
├── skills/
│   ├── android-interview/
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

## 当前 Skills

- `word-counter` - 用于中英文和混排文本的确定性字数统计
- `readme-generator` - 用于基于仓库证据生成或重构 README
- `android-interview` - 用于结构化 Android 模拟面试、本地报告与 TTS 语音产物生成
- `xiaohongshu-poem-fill` - 用于生成小红书诗词填空类笔记，包含原创古风短诗、话题标签与可选本地封面渲染
- `food-recipe-post` - 迁移后的每日菜谱社媒作品生成流程，用于小红书/抖音单菜或多菜推荐，包含 baoyu-imagine 封面提示词、明亮手写体封面风格和 500 字以内中文制作正文
- `daily-outfit-social-post` - 用于生成小红书/抖音每日穿搭作品，包含固定博主人设、摄影级穿搭图、连续性约束和短中文标题正文

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

以上仓库结构和校验流程就是当前对外可见的权威说明；如果需要看某个 skill 的细节，请直接查看 `skills/` 下对应目录。

## License

MIT
