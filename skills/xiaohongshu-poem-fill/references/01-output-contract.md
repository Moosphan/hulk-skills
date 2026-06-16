# Output Contract

For a standard request, return content in this order:

1. title
2. body
3. poem text with blanks
4. recommended answer
5. alternative answers
6. hashtags
7. optional local cover command

## Title

- Keep it short, interactive, and comment-oriented.
- Good patterns:
  - `诗词填空｜这一字你会怎么点？`
  - `画龙点睛挑战｜你会填哪个字？`
  - `古风填词｜这句你想补什么动作？`

## Body

- Show the blanked lines first.
- Invite the user to comment instead of revealing the answer immediately.
- Do not over-explain the poem background.

## Poem

- Prefer two lines.
- Prefer 5-9 Chinese characters per line.
- Keep both lines at the same length unless the user asks otherwise.

## Answers

- Always provide one recommended answer.
- Provide 2-3 alternatives when possible.
- Alternatives should feel plausible but shift the mood or image slightly.

## Hashtags

Include a compact hashtag set such as:

- `#诗词填空`
- `#画龙点睛挑战`
- `#古风短句`
- `#古诗词`
- `#中文之美`

## Cover Command

When the user asks for a local cover, append one runnable command using `scripts/render_xhs_cover.py`.
