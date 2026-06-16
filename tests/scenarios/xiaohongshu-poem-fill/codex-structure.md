# Xiaohongshu Poem Fill - Codex - Structure

## Scenario

Inspect the `xiaohongshu-poem-fill` skill and confirm that it exposes a Markdown-first contract, reusable references, and a local cover renderer with bundled background templates.

## Input

`请使用 xiaohongshu-poem-fill skill，生成一条诗词填空玩法，并说明本地封面如何渲染。`

## Expected Behavior

- The skill is selected successfully.
- The contract is defined in `SKILL.md` and `references/*.md`.
- The local renderer is discoverable.
- Reusable cover templates are bundled with the skill.

## Acceptance Criteria

- The skill directory follows the `hulk-skills` structure.
- The references describe output, writing rules, and cover workflow.
- The local script path is correct and usable.
