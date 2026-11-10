---
name: ai-daily-paper
description: 白音音的喵 B 站「AI 日报」模板化生产 skill——报纸头版视觉，早报浅色 / 晚报深色；覆盖资讯采集、证据链、选题、口播、渲染、发布与复盘。做白音音任何一期 AI 早报/晚报，或要改这套日报模板时加载。
---

# AI 日报（白音音的喵）

一套「报纸头版」风格的 AI 日报生产系统，服务 B 站账号 **白音音的喵**（catbus `-a main`）。
目标：每天一条，早报浅色、晚报深色，视觉统一、证据可查、可持续扩展。

## 何时用

- 生成当天的 AI 早报 / AI 晚报
- 改日报模板（版式、配色、字体、榜单、证据卡）
- 复盘日报数据、调整选题与节奏

## 分层能力模型

```
L0 采集层   sources.md     谁能用、怎么抓、抓不到怎么办
L1 证据层   evidence.md    第一现场、截图/引证、可信度分级
L2 编辑层   editorial.md   选题、去重、排序、口播稿结构
L3 视觉层   visual-paper.md 报纸模板、早浅/晚深、组件规范
L4 渲染层   render.md      remotion 合成、音频、质检
L5 发布层   publish.md     B站发布、封面、合集、复盘
```

扩展新能力时：只加层，不改层。例如新增「榜单页」属于 L3 组件 + L0 数据源，不重写 L2。

## 固定节奏

| | 早报 | 晚报 |
|---|---|---|
| 采集窗口 | 前一日 18:00 → 当日 08:30 | 当日 08:30 → 19:00 |
| 开始 | 08:30 | 19:00 |
| 发布 | 09:00 前 | 20:30 前 |
| 主题 | 浅色 paper | 深色 paper |
| 时长 | 60–90 秒 | 90–120 秒 |

## 一期的最小产物

1. `edition.json`（场景、口播、媒体）
2. `narration.wav`（白音音克隆音，speed 0.95）
3. `AI早报-YYYY-MM-DD-报纸版.mp4` 或 `AI晚报-...-深色版.mp4`
4. 封面 16:9 + 4:3
5. 证据清单（每条：原始出处 / 链接 / 截图路径）

## 命令入口

```bash
# 早报（浅色）
cd ~/dsh-video-remotion/news-video
npx remotion render NewsVideoPaper out/am.mp4 --codec=h264 --crf=18 --audio-codec=aac --audio-bitrate=192k

# 晚报（深色）
npx remotion render NewsVideoPaperPM out/pm.mp4 --codec=h264 --crf=18 --audio-codec=aac --audio-bitrate=192k

# 响度
ffmpeg -i out/am.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k ../AI早报-$(date +%F)-报纸版.mp4
```

## 硬规则

1. 只用白名单来源；第三方媒体只能当线索，不能当证据。
2. 证据必须挖到第一现场；拿不到就标「原始出处不可得」，不许伪装。
3. X 类证据必须贴原帖截图；无代理时明说不截。
4. 早报浅色 / 晚报深色，不互换。
5. 封面 16:9 + 4:3 必出。
6. 发布后回填 BV 号、时长、数据到 `报告/`。

## 参考

- `references/sources.md` 信息源白名单与抓取方式
- `references/evidence.md` 证据链规范
- `references/editorial.md` 选题与口播
- `references/visual-paper.md` 视觉模板规范
- `references/render.md` 渲染与质检
- `references/publish.md` 发布与复盘

## 固定结尾两页（2026-11-03 起）

早报、晚报都必须包含，缺一不可：

1. **Tibo 重置预测页**：上次重置、当前周期、28 天推算、官方状态
2. **模型排行榜页**：LiveBench 能力 / OpenRouter 使用量 / 价格三栏，带条形图与采集日期

版式：早报浅色 `#F2ECE0 + #B23A2E`，晚报深色 `#14100C + #E8912D`；两页放在片尾之前，进度条标签固定为 `Tibo`、`榜单`。

## 封面/片头红线（2026-11-03）

- 片头标题、副标、滚动条、竖排日期**全部从 edition 数据生成**，禁止写死
- 严禁复用上一期文案（例如「两家同时出手」）
- 每次渲染后必须目检首帧，确认日期、条数、条目标题与当天一致

## 结尾合并页（2026-11-03 修正）

Tibo 与模型榜合并为**同一页**，不再拆两页：
- 上半：`额度重置，周X前后` + 四行（上次重置 / 当前周期 / 28 天推算 / 官方状态）
- 下半：三栏榜单（能力 / 使用量 / 价格），带条形图
- 页脚：`数据：LiveBench 2.0 · OpenRouter · 官方定价页 · 采集于 YYYY-MM-DD`
- 进度条标签：`Tibo + 榜单`

## 风格宪法（2026-11-03 定稿，长期遵循）

### 一、片头/封面禁止硬编码
- 片头标题、副标、teaser、滚动条、竖排日期全部由 `edition` 生成
- 禁止复用上一期文案，渲染后必须目检首帧

### 二、证据必须落地
- 每条新闻必须有：来源域名 + 原文链接；X 帖必须有截图
- 没有截图就截原网站关键信息，**禁止出现「待补」「仍在核实」**
- 证据卡优先放截图，没图才放原文引语

### 三、配音 QC
- 口播避免英文夹中文（如 Flash），容易出电音
- 全部场景一次生成，不拼接旧音频
- 发布前必须过 `highpass 80Hz + afftdn + deesser`，并对首尾做 50ms 淡入淡出
- 检查：无爆音、无呼吸杂音、无缺句

### 四、时间轴
- 每场景独立音频，视频 `frames` 来自该场景音频真实时长
- 禁止用逐句 round 累加，避免漂移
- 渲染后抽查 3 个切点，确认声画同步

### 五、收尾合并页
- Tibo + 模型榜同一页，禁止拆两页
- Tibo 必须有视觉元素（D-N 倒计时或 28 天进度条）
- 榜单三栏 + 条形图 + 来源日期

### 六、封面
- 16:9 与 4:3 独立排版，禁止裁剪
- 一个视觉重心：大数字或大字标题
- 信息密度≥4 层：品牌、主标题、副标、底部条目条
- 头像竖直居中，昵称在下方
- 留白不超过画面 35%

### 七、排版密度
- 每页至少 3 个信息块，禁止整屏只有标题
- 右侧栏目必须有内容（截图/引语/数据），不能空

## 2026-11-03 追加修正

### 证据卡
- 截图必须目检：空白、403、验证码页面一律弃用
- 不能用截图时，改成「大字号原文引语 + 来源域名」，不要留空
- 每条至少一张可用图；优先官方站截图、X 原帖截图

### 首页人物
- 头像 + 昵称整体**竖直居中**（容器 `top:50%` + `translateY(-50%)`）
- 不允许贴顶或贴底

### 封面品牌
- 底部必须放三条要闻的品牌标识或品牌色块
- 每条：logo/品牌块 + 一行短标题
- 让观众不看标题也能一眼知道来源

## 2026-11-03 夜间修正

### Logo 规范
- 品牌 logo 必须从官方或 theSVG 素材抓取：`https://cdn.jsdelivr.net/gh/glincker/thesvg@main/public/icons/<brand>/default.svg`
- 禁止手绘/近似图形
- 封面底部三条要闻各配一个官方 logo + 一行短标题

### 音频 QC（强制）
- 片头、片尾句单独生成，生成后先用 `adeclick + afftdn + agate` 过一遍
- 全部场景统一响度后，再整体 `loudnorm -15 LUFS`，最后单独 `loudnorm -14` 出片
- 首尾必须 50–500ms 淡入淡出
- 时间轴必须与最终旁白同一份 concat 结果计算，禁止用旧时长

### 音频致命坑（2026-11-03）
- `afade=t=out:d=0.5` 若不带 `st=`，会从 0 秒开始淡出，整条变静音
- 正确写法：`afade=t=out:st=<总时长-0.5>:d=0.5`
- 出片前必须 `volumedetect` 校验：mean 应在 -18~-14dB，max < -0.5dB；mean < -40dB 直接判废

## 音频装配标准流程（2026-11-03 定稿）

1. 每句 TTS 单独生成，生成后立即：
   `silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04` + 反向同参数（去首尾静音）
2. 句间固定 0.15s，场景间固定 0.3s
3. 拼接后用 `adeclick + highpass 110 + afftdn nr=18 + agate 0.01 + deesser + loudnorm -15`
4. 片尾淡出必须写 `afade=t=out:st=<总时长-0.4>:d=0.4`
5. 出片 `-ar 48000`，避免 96kHz
6. 发布前跑三项校验：
   - `volumedetect`：mean -18~-14dB，max < -0.5dB
   - `silencedetect d=1.0`：不允许 >1s 静音
   - 逐场景 RMS：不允许 < -40dB
7. 配音完成后开独立 subagent 质检（响度/静音/首尾/2s/同步/逐场景有声），FAIL 先修再发

## 封面规范（已在 references/visual-paper.md 定稿）
- 四层结构：品牌层 / 主视觉数字 / 副标 / 品牌条
- 底部三条要闻各配官方 logo（theSVG CDN）+ 一行短标题
- 16:9 与 4:3 独立排版，头像竖直居中，留白 ≤35%

## 爆音/键盘声（2026-11-03）
- 场景/句子硬切会产生「咔哒」或「键盘」感，必须在每句拼接前加 20ms 淡入、50ms 淡出
- 场景之间留 0.3s 静音，句间 0.18s
- 整条再过一次 `adeclick`，并在片头 0.06s、片尾 0.45s 做淡入淡出（片尾必须带 st）
- 禁止直接 concat 未做淡入淡出的 TTS 片段

## 语气词
- VoxCPM 会在句尾带出「啊/呢」的口癖，这是模型韵律，不是文本
- 要彻底去掉只能换 TTS，或换参考音后重新训练音色

## VoxCPM 短句填充坑（2026-11-03）
- 短句（如「十一月三号，AI 晚报。」）会被固定生成到 3.2s，尾部常带多余语气或杂音
- 处理：对短句 `atrim` 保留 0.12–2.55s，再做 30/120ms 淡入淡出
- 每句生成后先比「字数/时长」，字符率 <3.2 字/秒 视为异常，需要修剪或重生成

## 白音音配音方案切换（2026-11-03 起）
- 早报/晚报送音改用 **Microsoft Edge TTS `zh-CN-XiaoyiNeural`**，rate +0%，pitch +0Hz
- 生成命令：`edge-tts --voice zh-CN-XiaoyiNeural --text "..." --rate=+0% --pitch=+0Hz`
- 后处理：`highpass 90 → 压缩 2.5:1 → loudnorm -16`，48kHz
- 逐句 `silenceremove -50dB` + 15ms 淡入 / 40ms 淡出，句间 0.15s，场景间 0.3s
- 不再使用 VoxCPM 生成正片旁白（短句 3.2s 填充问题）
- 片尾淡出必须带 `st`

## 转场键盘音效（2026-11-04 定稿）
- 文件：`/Users/dorck/Documents/ChatGPT/video-projects/output/keyboard-transitions/five-choices/01_laptop_soft.mp3`
- 用**完整 1.2 秒，不裁剪**，每个进度切换点触发一次（从第 2 个场景开始）
- 音量 1.0，与旁白 amix 后再 loudnorm -14
- 混音后必须验证：切换点前后差分 RMS > 0.02，否则音效没进

## 证据使用边界（2026-11-04）
- 只有**新产品 / 新版本 / 新模型发布**时才贴 release notes、changelog、版本日志
- 融资、并购、诉讼、政策、人事类新闻，用官方公告、法院/政府原文、权威媒体原文，不要硬贴 release
- Tibo 重置类信息，必须附 codex-resets.com 卡片或 @thsottiaux 原帖

## 证据预检（强制，2026-11-04）
- 渲染前必须跑：`python3 tools/check-evidence.py <evidence...>`
- 校验项：文件 >20KB、尺寸 ≥600×400、灰度标准差 ≥12、白色占比 ≤92%
- 任何一项 FAIL 必须换源或换形态，禁止直接渲染
- 常见失败：页面白屏、懒加载未完成、登录墙、403 占位图
- 兜底：官方站抓不到时，用「品牌 + 标题」的证据卡，但要在卡片上标明来源，不能留白

## 早晚报增量门禁（2026-11-04 起强制）

### 时间基准
- **早报**：只收 `07:30` 之前发布/发生的消息
- **晚报**：只收 `[早报发布成功时间, 19:00]` 之间的新消息
- 早报发布成功时间 = `catbus` 返回 `ok:true` 的时间，不是计划时间

### 发布门禁
1. 统计晚报窗口内、**来源时间晚于早报发布成功时间**的条目数 N
2. `N ≥ 2` → 正常出晚报
3. `N < 2` → **不出新视频**，改为：
   - 发一条文字动态/专栏做「今日复盘 + 榜单更新」，或
   - 直接跳过，不硬凑
4. 例外（允许 N=1 也出片）：该条为 P0 级——
   - 新模型 / 新版本 / 新产品发布
   - 官方重大政策、法院判决、重大并购
   - 必须在片头明确「晚间增量」

### 记录
- `edition-pm.json` 增加字段：`morningPublishAt`、`newItemCount`、`gatePassed`
- 发布包简介写明「本集新增 N 条晚间消息」

### 反面案例
- 2026-11-04 晚报 6 条与早报 6 条完全重合，N=0，仍出了 82 秒视频 → 违反门禁

### 结束语（强制）
- 每期必须有独立结束语，且音频尾部留 ≥1.0s 静音
- 结束语模板：`今天就到这里。<一句钩子>，明天见。`
- 渲染前校验：`narration` 时长 ≤ 视频时长 − 1.0s，否则补静音或延长 composition
- 禁止用最后一个正片句子当结束语

### 发布类资讯的取材顺序（强制）
1. 官网新闻室 / 官方博客（文字 + 图 + 视频 + 价格）
2. 官方 GitHub / HuggingFace（仅当对应版本已发布）
3. 官方 X 原帖
4. 权威媒体（仅补充，不替代官方）
版本号必须与发布版本一致；正式版找不到资料就留白，不拿 preview 顶替。

## 10. 发布类资讯路径（强制）
见 [`references/launch-sourcing.md`](references/launch-sourcing.md)：
官方模型站（含演示视频/图）→ 官方新闻稿（数字/benchmark 图）→ 官方账号 → 官方仓库（仅对应版本）→ 媒体补充。
最低证据组合：1 段官方演示视频 + 1 张官方图表 + 1 张官方页面截图。
工具：`scripts/official-model-media.mjs`。

## 11. 交付包与封面（强制，2026-11-06）

### 长版结构（对标白鸦，2026-11-06 起）
- 3–4 分钟；主线 4–6 条 × 35–45 秒；顶部快讯 6 条（一手链接）
- 每条主线 ≥3 个视觉面板，载体不重复：官方正文 / System Card / benchmark 图 / HF 卡 / changelog / demo 帧 / X 卡片 / 真机截图
- 模板已支持：`panels: string[]`（2×2 网格）与 `ticker` 场景（浅色 `NewsVideoPaper`、深色 `NewsVideoPaperPM` 均已加）
- 简介必须含：章节时间轴 + 官方来源 URL 清单
- 细则见 [`references/longform-structure.md`](references/longform-structure.md)
封面一律用 `templates/cover/poster.py`（v5 海报版）生成，16:9 + 4:3 双版；规范见 [`references/cover-spec.md`](references/cover-spec.md)。早报、晚报、插播、番外同一套版式，禁止每期重排。
每次出片，必须**一次性**交付以下四样，不等主人再要：
1. 成片 mp4
2. 封面 16:9（1920×1080）
3. 封面 4:3（1440×1080，**独立版式**，不许裁 16:9）
4. 发布信息：标题、简介（含时间节点）、标签、分区
5. 发布时**同时上传 16:9 与 4:3 两张封面**（见 `references/publish.md` 双封面发布）

缺任何一项都算未完成。

**发布硬门禁**：成片与两版封面必须先给主人确认，收到「发」之后才允许 publish；定时任务只做到「待确认」。

### 封面必备元素
- 栏目头 + 日期 + 期次（AI 晚报 / 晚间增量）
- **热点词**：官方定性的原话，如「最强开源」「首次视觉」「会操作电脑」
- **品牌 logo：贴纸式，至少两个，分主次**——主 logo 280px、次 logo 200px；白色描边 25px + 投影 alpha 14 / 偏移 3% / 模糊 2.8%；**先给 logo 自身加 15% 透明边再描边**，否则描边会被 logo 画布裁断；不要圆框、不要底块
- 两个 logo 之间留 ≥200px 间距，右下错落摆放
- **默认不写厂商名**；只有「新版本/新产品发布」时才在标题里带版本号（如 Images 2.6）
- 用**产品 logo** 而非公司 logo：Claude 用星芒（#D97757），不用 Anthropic 的 A
- **不放头像**，右侧空间全部留给 logo
- 焦点大字：型号（Hy4 / GPT-5.5 / ML4…）
- 头像 + 账号名，圆形描边
- 底部 3 张信息卡
- 留白 ≤35%

### 锯齿与清晰度
- 画布按 **4× 超采样**渲染，最后 LANCZOS 缩到目标尺寸
- 圆形头像描边最终 ≥3px，禁止直接在大图上画 1px 圆
- 文字用系统字体原尺寸绘制，不许先小图再放大

### 4:3 版式
- 独立布局：字号下调约 25%，信息块改 2×2，底部信息条一条
- 禁止直接裁 16:9

### 审核
封面先给主人过目，确认后再替换线上封面。

## 12. 情报流水线
资讯源顺序：**官方 X 原帖 → 官方页面 → 官方演示 → 一手媒体 → 二手**；每场必须有可读证据图，没有就不进片。
截图：3x DPI、关键词命中后裁最小正文块、宽 ≤1100/高 ≥240 CSS px、不得带侧栏评论、中文不许截断。
见 [`references/intel-pipeline.md`](references/intel-pipeline.md)：采集 → **同业对照（白鸦/黑鸦当日更新）** → 补池 → 选题 → 确认 → 制作。
未做同业对照不得进入写稿。


## 发布归档（2026-11-10 主人定，强制）
每期成品发布后，必须归到一个按日期排的目录，禁止散落在仓库根目录：

```
deliveries/YYYY-MM-DD/
  am/  AI早报-YYYY-MM-DD.mp4
       AI早报-YYYY-MM-DD-封面16x9.jpg
       AI早报-YYYY-MM-DD-封面4x3.jpg
       desc.txt            # 投稿简介原文
       edition.json        # 当天 edition
       evidence/           # 用到的证据图（只放本期用到的）
  pm/  AI晚报-YYYY-MM-DD.mp4 + 双封面 + desc.txt + edition-pm.json + evidence/
  publish.md               # 平台、BV号、链接、标题、标签、发布时间、状态
```

规则：
1. 发布成功后立刻归档，`publish.md` 回填 BV 号与链接；
2. 素材（音乐、模板、字体）不进归档目录，只放成品与证据；
3. 归档路径写进当日总结，方便回查；
4. 小红书笔记 ID 同样记进 `publish.md`。
5. 归档根目录固定为仓库的 `deliveries/`，不要再往根目录堆成品。


## 配音（紫鸦zya，2026-11-10 定稿 · 克隆模式）
- 配置：`voices/zya-voice.json`；参考音：`voices/zya-ref-P.wav` + `voices/zya-ref-P.txt`；样张：`voices/zya-P-reference.m4a`
- 生成器：`templates/tts/zya_tts.py`（一行命令出全套 wav）
- **为什么用克隆而不是 VoiceDesign**：VoiceDesign 是「按描述造声音」，逐句独立生成会音色漂移；必须先生成一条参考音，再用 Base 模型逐句克隆。
- 日常合成（唯一正确用法）：
```bash
~/dsh-space/whale-video/.venv-tts/bin/python \
  ~/.dsh/skills/ai-daily-paper/templates/tts/zya_tts.py lines.json assets/vo
```
  `lines.json` 结构：`{"scenes":[{"id":"open","lines":["..."]}, ...]}`
- 克隆参数：模型 `Qwen3-TTS-12Hz-1.7B-Base-bf16`、`ref_audio` + `ref_text`、`temperature 0.7 / top_p 0.9 / repetition_penalty 1.05`、**seed 11**、lang `zh`
- 换音色（极少用）：用 VoiceDesign 跑一次，描述 `A clear, cute young anime girl voice, 17, bright timbre, composed and professional, no attitude, efficient phrasing, clean cut sentence endings, soft close-mic, Mandarin Chinese.` + `speed 1.12`，把结果存成新的 `zya-ref-P.wav/.txt`
- 后处理：`aresample=48000,loudnorm=I=-16:TP=-1.5`；拼装 15ms 淡入 / 40ms 淡出，句间 0.15s，场景间 0.30s，片尾 ≥1.0s，终混 `loudnorm I=-15`
- 质量门：每句 `ffprobe` 验时长，>30s 或 <0.6s 视为退化，换 seed 重生成；整片 ASR 抽检数字与人名
- 禁止再用 Edge TTS（旧 Xiaoyi 参数仅作历史备份）


## B站话题标签（2026-11-10 强制）
每期早晚报**必带三个固定标签**，缺一不可：
1. `人工智能`
2. `AI日报`
3. `AI IN ALL！`（B站官方活动话题，tag_id 67376097；必须带，是主要流量入口）

再加 **3 个当天关键词**（公司 / 模型 / 垂类，如 Claude、英伟达、开源），总数 6–8 个，不超过 10。
标签顺序无所谓，但 `AI IN ALL！` 必须出现在列表里。发布命令示例：
```bash
catbus -a main bilibili item publish --video ... --tag 人工智能 --tag AI日报 --tag "AI IN ALL！" \
  --tag Claude --tag Anthropic --tag 开源
```
同行数据（16 条抽样）：`AI IN ALL！` 12 次、`人工智能` 10 次、`AI日报` 4 次——三个是我们的必带组合。
