# checkup · 示例：已完成的一集

对应《AI 员工年度体检》（番外，88.8s，1080p30）。**这是示例，不是模板**：看做法，不要照搬版式与台词。

## 目录

```
src/ui.tsx        Backdrop(深海夜光) / HUD / Paper / Stamp / Icon / Emote / Caption / Scene
src/Checkup.tsx   10 场：红头文件 / 答题卡 / 参考文献 / 上下文 / 监控 / 心率 / 报告单 / 投票 / 片尾
src/theme.ts      色板与字体
src/Root.tsx      注册 composition（读 public/data/checkup_timeline.json）
build_audio.py    TTS → cue 表 → 混音（BGM + ≤5 个点音）→ timeline.json
gen_sfx.py        三个柔和音效的合成
cover.py          1920×1080 封面生成（按 VISUAL-SYSTEM §9：深底 + 快乐体 + 珊瑚数字块 + 双角标）
script.json       台词源（一集 18 句，每句标 scene）
```

## 从零跑通

1. 新建项目目录，`package.json` 用 remotion 4.0.539 + react 19；`node_modules` 可直接软链到已有 Remotion 工程（逐包软链，保证 `.cache` 可写）。
2. 放素材：
   - `public/emotes/*.png` ← 20 张表情
   - `public/fonts/Muyao-Ruanbi.ttf`（可选）
   - `public/audio/Carefree.mp3`（BGM，CC BY 4.0，简介署名）
   - `public/shots/*.jpg`（真实 B 站画面，如需要）
3. `python3 -m venv .venv-tts && .venv-tts/bin/pip install edge-tts`
4. `python3 gen_sfx.py && python3 build_audio.py`（生成 `public/audio/checkup.wav` 与 `public/data/checkup_timeline.json`）
5. `npx remotion still src/index.ts Checkup preview/f.png --frame=330 --bundle-cache=false` 看静帧
6. `npx remotion render src/index.ts Checkup out/checkup.mp4 --bundle-cache=false --concurrency=6 --crf=18`
7. `python3 cover.py` 出封面

## 注意

- `build_audio.py` 里 `TTS` 路径指向项目上一级的 `.venv-tts`，按实际改。
- 改台词只需改 `script.json` 后重跑第 4 步，画面自动对齐（场景时间来自 cue）。
- 音效列表在 `build_audio.py` 的 `for lid, name, g in [...]`，删掉整行即为纯人声 + BGM。
