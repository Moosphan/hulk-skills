# L0 采集层：信息源与抓取

## 白名单（按可信度）

**A 级 · 一手官方**
- OpenAI Blog / News、Anthropic News、Google DeepMind Blog、Meta AI、Mistral、xAI
- DeepSeek、Qwen（阿里云百炼/通义）、智谱、MiniMax、Kimi（月之暗面）、美团技术团队
- GitHub Releases / commit / changelog
- 官方 X 账号：@OpenAI、@AnthropicAI、@thsottiaux（Tibo）、@GoogleDeepMind、@DeepSeek_AI、@Alibaba_Qwen

**B 级 · 权威媒体（外网为主）**
- 综合：Reuters、Bloomberg、FT、WSJ、NYT、CNBC、AP
- 科技：TechCrunch、The Verge、Wired、Ars Technica、The Information、VentureBeat、SiliconANGLE、The Register
- 芯片/基础设施：SemiAnalysis、Tom's Hardware、AnandTech、Data Center Dynamics、IEEE Spectrum
- 能源/算力：BloombergNEF、Data Center Frontier、Utility Dive
- 学术：arXiv、Papers with Code、Hugging Face Papers
- 中文：新华社、财联社、证券时报、机器之心、量子位、新智元、InfoQ

**B+ 级 · 深度信源（观点/爆料）**
- Import AI、Interconnects、Latent Space、Stratechery、Hacker News 首页
- 用法：可引用其判断，但事实仍需回原始出处

**C 级 · 只能当线索**
- 163、新浪、搜狐、IT之家、CSDN、各类聚合号
- 用法：只用来发现事件，必须顺藤摸瓜找 A 级原文；不得直接进画面

**D 级 · 禁用**
- 匿名爆料号、无出处截图、标题党、AI 生成的假消息

## 抓取方式（本机已验证）

| 站点 | 状态 | 方式 |
|---|---|---|
| anthropic.com / openai.com / claude.com | 可访问 | Playwright，`domcontentloaded` + 4s |
| LiveBench（livebench.ai） | 可访问 | Playwright，取全表文本 |
| OpenRouter（rankings / benchmarks） | 可访问 | Playwright；全量 API 需登录 |
| LMArena / Artificial Analysis / HuggingFace | 连接被关闭 | 需代理 |
| x.com / nitter / xcancel | 连接被关闭 | 需代理；截图前不得声称有图 |
| GitHub | 经常超时 | 重试或 API |

## 采集流程

1. 按窗口拉取：早报前一日 18:00 起，晚报 08:30 起。
2. 每条记录四元组：`事件 / 一手链接 / 时间 / 证据类型`。
3. 交叉验证：至少两个独立来源，或一个 A 级 + 一个 B 级。
4. 去重：同一事件只保留信息量最大的一条；更新另起「更新」标签。
5. 抓不到就写 `原始出处不可得`，不许编。

## 覆盖范围（每期至少 6 条，最多 10 条）

按主题各取所需，避免全是模型发布：

1. **模型/产品**：新模型、版本、价格、API、Agent 产品
2. **基础设施**：GPU/TPU、数据中心、光模块、液冷、电力
3. **能源**：核电/燃气/储能/电网，AI 用电与电价
4. **芯片与供应链**：台积电、HBM、NAND、封装、出口管制
5. **资本**：融资、并购、IPO、估值
6. **政策与安全**：监管、版权、诉讼、安全事件
7. **开源与学术**：开源模型、论文、基准、工具链

> 重大事件少的日子可以少于 6 条；事件多的日子最多 10 条，超出按 L2 权重截断。

## 固定必扫

- 模型更新：OpenAI / Anthropic / Google / Meta / Mistral / Qwen / DeepSeek / 智谱 / MiniMax / Kimi
- Tibo（@thsottiaux）与 ChatGPT / Codex 额度、重置、灰度
- 榜单：LiveBench（能力）、OpenRouter（使用量）、Artificial Analysis（价格，需代理）

## 资讯源白名单与禁忌（2026-11-04）
- **不用** IT之家（广告多、二手编译）
- 优先：机器之心、量子位、新智元、36氪、InfoQ、硅星人；官方博客/新闻室为 T1
- 海外：Reuters / The Verge / TechCrunch / FT + 官方账号 X 原帖

## 开源项目必挖（强制）
涉及「开源 / 开放权重 / 模型发布」的资讯，必须找到项目源头：
1. GitHub 仓库（README：架构、参数、License、Model Links）
2. Releases / Tags（版本、发布时间、变更）
3. HuggingFace 模型卡
4. 截图至少 1 张 README + 1 张 release/Model Links
- 若尚无 release，明确写「仓库已建、暂无 release」，不许省略

## 新模型 / 新产品发布：官方优先（2026-11-04 强化）
1. **先查官网新闻室 / 官方博客**，用原文的标题、日期、数字、图、视频
2. 官方页面自带 benchmark 图、demo 视频、定价表 → 直接截，不用媒体二手
3. 官方口径里的数字（分数、通过率、价格）优先于任何媒体转述

### 版本必须对齐
- 发布的是 **正式版** 就只引正式版资料
- **禁止**把 preview / beta 的参数、repo、图表当成正式版证据
- 正式版还没有 repo / HF 模型卡时：**不放**，写「权重近期开源，仓库尚未发布」
- 开源项目位置查询顺序：官方新闻稿里的链接 → GitHub org → HuggingFace org → 官方文档

### 禁止
- 用过时版本的 README / 参数冒充新版本
- 用媒体截图替代官方 benchmark 图（官方有图就必须用官方）

## 官方模型页的「图 + 视频」挖掘（2026-11-04）
- 混元官方研究页：`https://hunyuan.tencent.com/research/<model>`（SPA，需等 10–20s 直到 Loading 消失）
- 页面里直接有 `<video>` 演示，`video.currentSrc` 就是可下载的 mp4（COS 签名链接）
- 抓法：
  1. Playwright 打开页面，轮询到正文出现
  2. `document.querySelectorAll('video')` 取 `currentSrc`
  3. `ffmpeg -t 8 -an` 裁成 8 秒静音片段，作为视频卡证据
- 同时截页面各段（hero / demo / benchmark），避免全片都是文字
- 官方新闻稿 `tencent.com` 有 benchmark 图；官方研究页有 demo 视频，两者都要用
