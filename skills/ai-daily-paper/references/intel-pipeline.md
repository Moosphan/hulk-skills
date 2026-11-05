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
