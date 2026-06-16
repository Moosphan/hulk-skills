# Cover System

## Cover Goal

Produce a Xiaohongshu-friendly vertical cover, usually `1080x1440`, with:

- heading: `诗词填空`
- label: `画龙点睛挑战`
- a centered two-line poem with blanks

By default, the rendered title becomes:

- `诗词填空 · 画龙点睛挑战`

## Supported Styles

- `ink-mountain`
- `snow-lamp`
- `bamboo-tea`
- `moon-boat`
- `plum-cold`
- `paper-minimal`
- `old-book`
- `mist-river`
- `lotus-pond`
- `pine-temple`
- `desert-pass`
- `palace-moon`
- `orchid-window`
- `peach-spring`
- `maple-bridge`

## Design Rules

- keep the center region readable
- do not let the background overpower the poem
- keep generous line spacing between the two lines
- hide footer text by default
- do not display the internal style name on the cover

## Recommended Workflow

1. use an image model only for a text-free background when needed
2. render Chinese text locally with `scripts/render_xhs_cover.py`
3. verify the blank length and readability before delivery
