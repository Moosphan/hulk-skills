---
name: xiaohongshu-poem-fill
description: 生成小红书诗词填空类推文，包括原创古风短诗、可配置挖空字数、互动型标题正文、话题标签，以及可复用的古风封面模板与本地渲染脚本。
---

# Xiaohongshu Poem Fill

Use this skill when the user wants to create or batch-produce Xiaohongshu poem-fill posts such as `诗词填空` or `画龙点睛挑战`.

This skill is Markdown-first. The assistant should generate the post copy, poem options, answer set, and cover instructions directly in the conversation. The local Python script is an optional helper for deterministic Chinese text rendering onto prepared cover backgrounds.

## What To Produce

Default deliverables:

- one interactive title suitable for Xiaohongshu
- one short body that invites comments without revealing the answer
- one original two-line classical-style poem with 1-3 blanks
- one recommended answer and 2-3 alternative answers
- one hashtag set
- one cover render command when the user wants a local cover image

## Required Reading Order

Read these references before generating output:

1. `references/01-output-contract.md`
2. `references/02-poem-generation-rules.md`
3. `references/03-cover-system.md`

Only read `references/04-local-rendering.md` when the task includes local cover rendering, font selection, or template migration details.

## Operating Rules

- Prefer original lines instead of adapting existing famous verses.
- Treat the blank as the center of the interaction. By default, blank out a verb or verb phrase.
- Keep the result comment-friendly. Do not present the answer as uniquely correct unless the user explicitly asks for a single-answer puzzle.
- When the user asks for a cover, prefer the bundled local renderer over asking an image model to draw Chinese text.
- If the user asks for batch output, keep each card stylistically distinct while preserving the same output contract.

## Local Assets

- Reusable background templates live under `assets/generated/styles/`.
- Background generation prompts live under `prompts/style-backgrounds/`.
- The deterministic renderer is `scripts/render_xhs_cover.py`.
- Example post outputs and cover samples live under `examples/`.
- Codex metadata lives in `agents/openai.yaml`.

## Typical Invocation

- “写 10 条诗词填空小红书笔记，默认单字挖空”
- “给我来 6 条双字挖空，偏江南烟雨”
- “生成一张 `paper-minimal` 风格的封面，诗句用宋体细字”
- “把这句改成更适合评论区互动的填空玩法”
