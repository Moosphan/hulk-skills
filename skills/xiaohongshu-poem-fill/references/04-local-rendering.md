# Local Rendering

Use the local renderer when the user wants a concrete cover file or when Chinese text accuracy matters.

## Script

`scripts/render_xhs_cover.py`

## Example Commands

```bash
python3 skills/xiaohongshu-poem-fill/scripts/render_xhs_cover.py --style ink-mountain --blank-chars 1
python3 skills/xiaohongshu-poem-fill/scripts/render_xhs_cover.py --style bamboo-tea --blank-chars 2
python3 skills/xiaohongshu-poem-fill/scripts/render_xhs_cover.py --style moon-boat --font songti-light
python3 skills/xiaohongshu-poem-fill/scripts/render_xhs_cover.py --style paper-minimal --font xingkai --line-spacing 72
python3 skills/xiaohongshu-poem-fill/scripts/render_xhs_cover.py --style paper-minimal --font-path /path/to/custom-font.ttf
```

## Font Notes

The following portable open-source presets are bundled with the skill. They are all
licensed under SIL Open Font License 1.1 and can be used when the skill is moved to
another machine:

- `zcool-xiaowei` (default): poised, high-contrast display text for classical covers
- `lxgw-wenkai`: soft and literary handwritten feel
- `mashanzheng`: measured calligraphic display text

The script also supports locally installed presets such as:

- `xingkai`
- `kaiti`
- `fangsong`
- `lisong`
- `biaukai`
- `wawati`
- `songti-light`
- `songti-regular`
- `songti-bold`
- `pingfang`

`shangwei` is intentionally not supported and must not be used for future covers.

If a requested preset is unavailable on the local machine, the script falls back to an available Songti preset.

## Migrated Templates

Reusable background templates are stored in:

`assets/generated/styles/bg-*.png`

The source prompts used to generate those text-free backgrounds are stored in:

`prompts/style-backgrounds/`

Only the reusable text-free backgrounds are treated as canonical templates. Rendered demo covers and contact sheets are not required for normal operation.
