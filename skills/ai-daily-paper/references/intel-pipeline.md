# 情报流水线（2026-11-05 起强制）

采集 → **同业对照** → 补池 → 选题清单 → 主人确认 → 制作

## A. 采集（窗口内）
1. 官方 changelog / newsroom（OpenAI、Anthropic、Google、Mistral、Qwen、DeepSeek、腾讯混元）
2. 官方 X 账号 + 爆料号（@testingcatalog、@btibor91、@kimmonismus、@legit_rumors）
3. Hacker News 首页 / r/LocalLLaMA
4. GitHub Trending + Releases / HuggingFace 新模型
5. arXiv / HF Papers（有代码的优先）
6. 一手媒体：The Information、Reuters、Bloomberg、晚点、36氪、机器之心、量子位

## B. 同业对照（生成视频前必做）
固定盯两位同行当日更新：
- Ba1ya 白鸦 `uid 3747520268208345`
- 黑鸦 Heya `uid 3706929260006322`

```bash
catbus -a main bilibili user items <uid> --limit 12
```
取当日标题 + 简介，抽出他们讲到的「事件关键词」，与自己的选题池做差集。

## C. 补池
差集里的每个事件：
1. 先找官方源（官网/X/GitHub/HF）
2. 找不到官方就找一手媒体
3. 验证不了就标注「未证实」，不进 S 级
4. 补进 `research/pool/<date>.json`：`{event, source, time, evidence, verified}`

## D. 选题与确认
按 S/A/B 出清单，主人确认后进入制作。

## 工具与自动化
- RSS：RSSHub + Feedly/NetNewsWire，订阅官方 blog、HN、GitHub releases
- X：vxtwitter 取原帖；官方账号列表单独分组
- 每日 2 次扫描：07:00（早报）、18:30（晚报）
- 线索去重：按 URL 与事件关键词 hash

## 反面案例（2026-11-05）
- 漏掉 OpenAI Images 2.6（GIF 生成、速度 +50%）
- 漏掉 Anthropic 用 Claude 解析原核 Vault 结构（3 天 → 90 分钟）
- 两者同行当日都做了，我们没进池

## 资讯源优先级（2026-11-05 定稿）

按顺序找，前一级拿不到才降级：

1. **官方 X 原帖**（有 status ID 就用 `tools/tweet-card.mjs` 出卡）
2. **官方页面**（newsroom / blog / 模型页 / 定价页 / GitHub / HF）
3. **官方演示素材**（官方页里的 `<video>`、benchmark 图、产品截图）
4. **一手媒体正文**（机器之心、量子位、36氪、财联社、新浪科技、凤凰）
5. 聚合站/二手转述（仅在没有以上时使用，并在画面标来源）

### 找 X 帖子 ID
- 文章 HTML 里正则 `(?:x|twitter)\.com/([A-Za-z0-9_]+)/status/(\d+)`
- 搜索引擎 `site:x.com <关键词>` / `<账号> status`
- 拿到 ID 后：`api.vxtwitter.com/i/status/<id>` → `tweet-card.mjs`
- X 需登录、搜不到 ID 时，跳到第 2 级，不硬等

### 找不到证据怎么办
- 官方没有、媒体也没有 → **不进片**
- 只有二手转述 → 标「未经官方确认」，且必须配可读截图

## 扩展深度与广度（2026-11-06 对标白鸦）
- 广度：主线 4–6 类（模型/安全、开源基座、芯片、资本并购、工具、政策），快讯再补 6 条不同类别
- 深度：每条主线必须回答「是什么 / 数字 / 谁能用」，缺一层就只能是快讯
- 来源：每条主线配 2–4 个官方 URL（blog、System Card、HF、changelog），快讯 1 个一手链接
- 国内厂商：官网 + Hugging Face 双证据；海外：官网 + X 原帖
- 官方没有的：标「未官方」，并保留媒体原文截图

## 每日三条硬规矩（2026-11-08 主人定）
1. **同行对照必须同档期**：做早报就查同行当天早报；做晚报就查同行当晚晚报。跨档期对比不算数。
2. **资讯查重**：近 3 天发过的条目不再重复，除非有实质更新（新数字、官方回应、结果落地），重复时必须写「更新」。
3. **榜单与 Tibo 每次现拉**：
   - 能力：LiveBench 2.0（`livebench.ai` 表格前三）
   - 使用量：OpenRouter 周榜（`openrouter.ai/rankings`）
   - 价格：OpenRouter `/api/v1/models` 取 completion 价格最低三个
   - Tibo 重置：codex-resets.com 查最新周期与「第 N 天」
   - 四项都必须在页脚写「采集于 MM-DD」，与视频日期一致，禁止沿用上一期数据

## 刷新榜单必须改的两处代码（2026-11-08 事故）
- 浅色：`src/VideoPaper.tsx` → `BoardLight`
- 深色：`src/VideoPaperPM.tsx` → `TiboBoard`
两处都要改数值 + `采集于 MM-DD` + `D–N`；只改一处 = 没刷新。
交付前用 `ffmpeg -ss <榜单时间>` 抽帧目检，确认不是上一期数字。

## Tibo 重置的正确读法（2026-11-10 纠正）
- 每次现查两个站：`codex-resets.com`（公告历史）+ `limitdigest.com/resets/codex/`（下次排期）
- **必须区分两种重置**：
  - `full reset`：官方「usage limits have been reset」，额度直接刷新
  - `banked reset`：发一张存量重置券，要在 Codex App 里手动领、有有效期，**不等于额度刷新**
- 不许再用「28 天周期推算」这个说法，节奏已不稳定；只写「最近一次 full reset 日期 + 下次是否已排期」
- **人事变更**：Tibo（@thsottiaux）2026-11-06 已转岗负责 OpenAI 内部安全，重置按钮可能移交 Andrew Ambrosino（未官宣），口播不要再写「Tibo 的 28 天周期」

## 资讯源巡检清单（2026-11-10 补，P0 强制）
每天三次（09:00 / 14:00 / 18:00）扫以下源，只取 24h 内：
- **X 一手**：@elonmusk、@sama、@AnthropicAI、@OpenAI、@GoogleDeepMind、@MetaAI、@deepseek_ai、@Alibaba_Qwen、@Zai_org、@MiniMax_AI、@MoonshotAI、@ThinkingMachines
- **海外媒体**：The Verge AI、TechCrunch AI、Reuters Tech、Bloomberg Tech
- **模型库**：HuggingFace Trending top10
- **社区**：Linux.do、r/LocalLLaMA、HN 前 20
聚合站（金十/华尔街见闻/星岛）只作线索，必须回查一手；X 原帖可直接引用但需截图卡片。

## 资讯源清单（2026-11-10 落库，P0）
每日三次巡检（09:00 / 14:00 / 18:00），只取 24h 内；产出写 `candidates.json`。

### 一手（直抓，已验通）
| 源 | URL | 方式 |
|---|---|---|
| Anthropic | https://www.anthropic.com/news | HTML，grep 日期 |
| Google DeepMind | https://deepmind.google/discover/blog/ | HTML |
| Google 官方博客 | https://blog.google/technology/ai/ | HTML |
| Meta AI | https://ai.meta.com/blog/ | HTML |
| HuggingFace 新模型 | https://huggingface.co/api/models?sort=createdAt&direction=-1&limit=20 | JSON |
| 英伟达 IR/新闻稿 | https://nvidianews.nvidia.com/news | HTML |
| 外资行情 | https://stockanalysis.com/stocks/<ticker>/ | HTML（股价证据） |
| 外交部实录 | https://www.mfa.gov.cn/fyrbt_673021/jzhsl_673025/ | HTML，按日期取 |
| 腾讯/阿里/字节公告 | 各官网/公众号 | HTML |

### X（按 evidence.md 的既有方法）
1. 先找 status ID：媒体报道 HTML 里 grep `(x|twitter)\.com/<user>/status/(\d+)`
2. `curl -sL "https://api.vxtwitter.com/i/status/<ID>"` 取正文/时间/互动
3. 用 `templates/tweet-render/render.mjs` 渲染卡片
4. 新增兜底：`https://r.jina.ai/https://x.com/<handle>` 可读个人页（实测 200，但只回置顶与部分帖）；`x.com/search` 需登录，不可用
5. 找不到 ID 时按 evidence.md 降级：官方页 > 金十/快讯全文 > 媒体正文截图

### 二手告警（只做线索，必须回查一手）
金十快讯 https://flash.jin10.com 、华尔街见闻 https://wallstreetnews.com 、C114、星岛头条、TechCrunch、The Verge、Reuters

### 验证过的两个今天案例
- **Grok 4.8**：金十 17:38 快讯有马斯克完整引述（弃用 JAX/SGLang、C/C++ 重写、本周灰度 Bot 用户）；X 原帖 ID 未在媒体页找到 → 按降级规则用金十快讯作证据
- **Gemini 4 Carbon**：DeepMind 官网标注 October 2026 已发布，**不是「发布在即」**；选稿前必须先查官方博客确认状态
