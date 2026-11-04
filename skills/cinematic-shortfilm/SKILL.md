---
name: cinematic-shortfilm
description: 电影感科普短片（70–300 秒）的完整制作规格与工作流——剧本/旁白（Qwen3-TTS VoiceDesign 男声）、Remotion + Canvas 粒子/SVG 视觉系统、代码合成配乐、外部混音与 4K 交付、事实核对与发布包。做《人类简史·宇宙的自画像》《向下·DESCENT》这类片子，或要复用它们的规范时加载。
version: 1.0
---

# 电影感科普短片 · 统一制作规范 v1

来源：《人类简史 · 宇宙的自画像》（4K / 4'58" / 14 场）与《向下 · DESCENT》（2K / 1'30" / 90 秒垂直剖面）。
两部片子的规格、工作流、风格、踩过的坑，全部收在这里。**新片先读第 0、1 节，再读与本次相关的章节。**

---

## 0. 铁律（违反任何一条都会返工）

1. **先定声音，再定画面**。旁白逐句生成 → 量出时长 → 由时长反推每场帧数。绝不先排画面再配音。
2. **旁白与数据必须一致**：片中出现的数字、单位、量级，逐条对照事实表；旁白说 98，画面就不能写 90。单位错（如压力 atm ↔ t/m²）比配错色严重十倍。
3. **一颗镜头一个信息**：每场只允许一个主命题 + 最多 3 个读数；多出来的信息交给旁白。
4. **文字永远可读**：任何文字下方必须有底衬或压暗；层名 ≥ 30px、读数 ≥ 13px；小字透明度不低于 0.6。
5. **不许硬切**：场与场之间用叠化 / 黑场呼吸 / 连续运动；同一部片只能用一种转场语言。
6. **静音渲染**：Remotion 里 `<Audio>` 一律 `{false && ...}` 关掉，音频由 ffmpeg 外部合入（长 WAV 会让渲染卡在 audio preprocessing）。
7. **渲染前必须 `npx tsc --noEmit` 干净**，否则会渲出一堆坏帧再重来。
8. **交付前三件事**：全长校验、首尾帧校验、关键转场逐帧校验（每条 3–6 帧）。

---

## 1. 标准流水线（按顺序，不可跳）

```
script.json ──► VO 生成 ──► VO 后处理 ──► 时长表 ──► 时间轴
                                   │
                                   └──► 配乐（numpy）──► 混音 ──► master.m4a
画面（Remotion）──► 静音渲染 ──► ffmpeg mux ──► 交付
```

### 1.1 剧本
- 每条一个 file：`script.json`，字段 `id / act / text / caption`。
- 中文旁白 ≈ **4.2 字/秒**；60 秒片 ≈ 200–230 字，90 秒 ≈ 300–340 字。
- 数字写成中文读法（「三千六百八十八」），否则 TTS 会读错；画面里再用阿拉伯数字。

### 1.2 旁白（Qwen3-TTS VoiceDesign，男声纪实）
```python
INSTRUCT = ("A deep, calm, authoritative male documentary narrator. Slow, deliberate, cinematic. "
            "Low register, warm, intimate, restrained emotion, close-mic. Consistent, even pacing. Mandarin Chinese.")
generate_audio(text=..., model=model, lang_code="zh", instruct=INSTRUCT,
               temperature=0.65, top_p=0.9, repetition_penalty=1.05,
               output_path="vo_raw", file_prefix=id)
```
- 模型 `mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16`，`mx.random.seed(11)` 固定。
- **每条生成后立刻 `ffprobe` 验时长**：若某条 > 30 秒或出现整段重复，就是 TTS 退化了，删掉重生成（换 seed 或把 `repetition_penalty` 提到 1.12）。
- **ASR 复检**：`mlx_whisper` 转一遍，核对数字/生僻字（氢→清、硅→龟、铁→体 这类）。

### 1.3 声音后处理（统一链，不许各条不同）
```
highpass=f=70,
asetrate=24000*0.912341, aresample=48000, atempo=1.096081, atempo=1.055,
equalizer=f=190:t=q:w=1.0:g=1.4, equalizer=f=3300:t=q:w=1.4:g=-1.8, equalizer=f=7200:t=q:w=1.8:g=-1.0,
acompressor=threshold=0.14:ratio=2.2:attack=10:release=200,
loudnorm=I=-20:TP=-3:LRA=7
```
再按 20ms 能量包络裁掉首尾静音、把超过 0.34 s 的停顿压到 0.34 s，两端 12ms/50ms 淡入淡出。

### 1.4 时间轴
- `frames = round(seconds * 24)`；旁白偏移 = 场起点 + lead（一般 18–24 帧）。
- 每场：`lead + vo + tail`，tail 16–90 帧（结尾卡给足）。
- 生成 `timeline.ts`（自动生成，别手改），字段 `{ id, from, dur, voAt, voDur }`。

### 1.5 配乐（纯代码合成，numpy）
- **要有结构，不要铺满**：按时间码写「事件」，而不是一条 pad 到底。
- 和声：每 12–18 秒换一次，交界处交叉淡化；低音只做 55 Hz 以上的持续音。
- **不要低频轰鸣**：观众会形容为「轰轰声」「太吵」。低音截止 85–100 Hz，长音用纯正弦，不加八度谐波。
- 安静优先：音乐电平 ≈ 旁白的 −20 ~ −27 dB；旁白出现时再压 40–70%（侧链闪避）。
- 终混响度：纪实片 **−18 ~ −24 LUFS**（不是 −14，那是流媒体流行乐）。
- 教程式的「音效设计」（入水闷响、声呐、金属吱呀）**只在客户明确要时加**；被否过一次，默认不用。

### 1.6 画面（Remotion）
见第 2 节。

### 1.7 渲染与合入
```bash
npx tsc --noEmit
npx remotion render Film4K out/silent.mp4 --codec=h264 --crf=18 --concurrency=7
ffmpeg -i out/silent.mp4 -i public/audio/master.m4a \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart out/final.mp4
```
- 4K = 1920×1080 布局 + `transform: scale(2)`；2K = `scale(2560/1920)`。**只写一套布局**。
- 局部返工：只重渲该段帧区间 → `ffmpeg` `trim/concat` 三段拼接 → `-c:v copy` 只换音轨；要换画面就三段重编码拼接（约 5–10 分钟）。

---

## 2. 视觉系统

### 2.1 底板
- 画布 1920×1080，24 fps；`AbsoluteFill` 背景近黑（`#01050A` / `#010407`），**永远不要纯黑 #000**。
- 三层结构：**背景渐变 → 体积光/粒子 → 信息层（文字、深度尺、读数）**。
- 收尾统一：`Vignette` + 静态 `Grain`（0.04，**必须 `animate={false}`**，动态颗粒会让细线闪）。

### 2.2 字体
- 标题/诗句：`Songti SC`（serif），字距 0.4–0.6em，大字号（90–250px）。
- 数据/读数：`SF Mono`，8–14px，字距 0.16–0.36em。
- 说明：`PingFang SC`，14–19px，透明度 0.55–0.7。

### 2.3 调色（两部片各自的「世界观色」）
| 片种 | 顶部亮 | 中段 | 底 | 强调色 |
|---|---|---|---|---|
| 宇宙 / 时间 | `#050506` 底 | 奶油 `#F3E7D0` | — | 琥珀 `#E8B06A` |
| 海洋 / 深度 | `#1E7C93` 水面 | `#07232E` | `#01050A` | 青 `#4FE0C0` |

规则：**同一部片只用一个强调色**；生物发光/热液这类例外最多两种，且各自绑定一种物理量。

### 2.4 粒子引擎（Canvas 2D）
- 确定性随机（hash），同一帧永远同一结果；云类型：`ball / filament / disk / globe-surface / sphere-shell / figure / city / helix / neuron / glyph / single / text / timeline`。
- 两遍绘制：先大半径低透明度做辉光，再小半径高透明度画核心；`globalCompositeOperation = 'lighter'`。
- **点云边界必须在画面外**：`makeCloud('text', n)` 是 3×1.2 的盒子，投影后会出现**矩形边**（最常被观众指出的 bug）。用 `expand(cloud, kx, ky, kz)` 放 2.4–3.2 倍。

### 2.5 生物与地形（SVG）
- 一律**侧视、头朝运动方向**；眼睛、鳍、嘴线、喉褶、藤壶等解剖细节至少 4 处，否则像贴图。
- 剪影 + 边缘光（0.2–0.35 透明度）；**不要**用 `feTurbulence` 叠在身体上（会变成花岗岩）。
- 地形：**多段折线 + 岩层线 + 岩屑 + 沉积**，不要三角形；山体**不要画基线**（会变成图表）。
- 生物出现窗口按「深度/时间」绑定，别同时出现三种以上。

### 2.6 信息层（HUD）
- 层带铭牌：深色渐变底（0.72→0）+ 左侧 2px 强调色竖条 + 中文 30–35px 纯白。
- 读数：每层 2–3 组，`LABEL` 8.5px / `VALUE` 13–14.5px。
- 刻度尺：刻线 + 当前值加粗；**当前值必须实时计算**，不能写死（写死会与指针矛盾）。
- 所有数字带单位；单位用空格分隔（`1,093 atm`）。

### 2.7 转场
- 首选**连续运动**（一镜到底）：深度/时间是一个连续量，内容随它进出画面。
- 次选**短叠化**（4–6 帧，只有新镜头淡入、旧镜头保持不透明被覆盖）——亮度不塌、HUD 不叠字。
- 禁用：斜向光扫、长交叉溶解、垂直推镜（会露出暗边）、黑场后硬切（除非是「入水」这类物理动机）。

---

## 3. 事实与数据

- 建一张 `facts.md`：每条 `数字 / 单位 / 来源范围 / 片中怎么写`。
- **三处最容易错**：① 单位换算（1 atm ≈ 10.3 t/m² ≈ 1.03 kgf/cm²）；② 「平均」与「极值」混用（平均 3,688 m vs 最深 10,935 m）；③ 简化说法（90 vs 98 种元素）。
- 全片统一一种精确版本；旁白与画面必须同源。

---

## 4. 交付物清单

```
deliverables/
  片名-4K-旁白版.mp4           # 主版本
  片名-4K-纯音乐版.mp4         # 如需要
  海报-4K.png / 预览-4K.png    # 关键帧合成
  封面/                        # 1920 PNG + 4K PNG + 1146×717 JPG
  导演阐述.md                  # 结构、声音、修改记录
  发布文案-B站.md              # 标题/简介/标签/置顶评论/封面建议
  事实表.md
```

发布包必带：AI 生成声明、制作分工（模型做了什么、人做了什么）、一版「容易看错的数字」置顶评论。

---

## 5. 踩坑记录（按出现频率排序）

| 现象 | 根因 | 修法 |
|---|---|---|
| 渲染卡在 audio preprocessing | 长 WAV + `<Audio>` | 静音渲染，外部 mux |
| 文字在粒子上一片糊 | 无底衬 + 透明度 0.4–0.5 | 底衬 + 纯白 + 加大字号 |
| 画面出现规则矩形（观众最爱问） | 点云盒子边界进画 | `expand()` 放大 2.4–3.2× |
| 细线/山体闪烁 | 动态 film grain | `Grain animate={false}` |
| 鲸/鱼「倒着游」 | 头和尾画反、眼在尾端 | 侧视重构：头在 +x |
| 山体像图表 | 路径用 `L ... Z` 收了水平基线 | 底边沉到画面外 |
| 转场打断视线 | 光扫/长溶解 | 短叠化或连续运动 |
| 配乐「轰轰」 | 27–80 Hz 持续低音 | 高通 85–100 Hz，去掉 sub drone |
| 音画不同步 | 画面节拍与旁白内容不对应 | 深度/时间曲线按旁白内容重排 |
| TTS 单条 600 s | 模型退化循环 | 删掉重生成，`repetition_penalty` 1.12 |
| 4K 返工太慢 | 全片重渲 | 只渲改动帧区间 + concat |

---

## 6. 两部参考片的位置

- 《人类简史 · 宇宙的自画像》：`~/dsh-video-remotion/film/src/scenes/*`，14 场，4K，4'58"。
- 《向下 · DESCENT》：`~/dsh-video-remotion/film/src/ocean/*`，6 层带，2K，1'30"；旁白与配乐在 `~/dsh-video-remotion/ocean/`。
- 两者共用 `src/engine/particles.tsx`（粒子）、`src/engine/atmos.tsx`（Vignette/Grain）、`src/theme.ts`（字体/调色/缓动）。
