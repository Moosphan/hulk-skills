# 新模型 / 新产品发布：资讯获取路径（SOP）

> 只要选题是「发布 / 上线 / 开源」，一律走这条路径，不走媒体优先。

## 0. 触发条件
- 新模型、新版本、新产品、重大功能上线
- 关键词：正式版 / 发布 / 开源 / GA / 开放权重

## 1. 官方模型站（第一优先，必须去）
按厂商找对应页面，不要停在集团新闻稿：

| 厂商 | 页面 |
|---|---|
| 腾讯混元 | `hunyuan.tencent.com/research/<model>`、`/model/hy-model` |
| OpenAI | `openai.com/index/<slug>`、`openai.com/news`（本机需代理） |
| Anthropic | `anthropic.com/news` |
| Google | `deepmind.google/discover/blog`、`blog.google/technology/ai` |
| Mistral | `mistral.ai/news` |
| 阿里 Qwen | `qwen.ai`、`qwenlm.github.io/blog` |
| DeepSeek | `deepseek.com`、`api-docs.deepseek.com/news` |
| 月之暗面 | `moonshot.cn` |

要点：
- 模型页通常有 **演示视频、产品截图、benchmark 图、定价表**
- SPA 要等：轮询 `body.innerText` 直到 `Loading` 消失且正文 > 3000 字
- 官方演示视频用 `document.querySelectorAll('video')` 取 `currentSrc` 直接下载

## 2. 官方新闻稿 / Newsroom（第二优先）
- 取：发布日期、官方定性（如「最强开源」）、benchmark 图、定价、上线平台
- 与模型页互补：模型页给演示，新闻稿给数字与图

## 3. 官方账号（第三）
- X：@OpenAI、@AnthropicAI、@MistralAI、@thsottiaux、@Alibaba_Qwen、@DeepSeek_ai
- 取原帖作为「发布时刻」证据，卡片化

## 4. 官方仓库（仅对应版本已发布时）
- GitHub org / HuggingFace org / ModelScope
- README：架构、参数、License、Model Links
- Releases / Tags：版本、时间、变更
- **正式版没有仓库就写「权重未放」，禁止拿 preview 顶替**

## 5. 媒体（只做补充）
- 机器之心、量子位、新智元、36氪、InfoQ
- 不用 IT之家
- 媒体只用于：补充背景、找第三方评价；不能替代官方数字与图

## 6. 一条发布资讯的最低证据组合
- ≥1 段官方演示视频（video 卡）
- ≥1 张官方图表（benchmark / 定价 / 架构）
- ≥1 张官方页面截图（标题 + 日期）
- 有官方 X 帖则再加 1 张帖子卡

## 7. 工具
```bash
node scripts/official-model-media.mjs <official-url> ./media --shots 4 --videos 3 --clip 8
```
输出 `shots/*.png`、`videos/*.mp4`、`media.json`。脚本自动读系统代理，需 `PW_ROOT` 指向有 playwright 的工程。

## 8. 记录
每条发布资讯落一个 `sources.json`：
```json
{"model":"Hy4","version":"正式版","officialPage":"...","pressRelease":"...","repo":null,"videos":["..."],"charts":["..."],"capturedAt":"..."}
```

## 9. 失败处理
- 官方页 403：走系统代理 + 真实 UA
- SPA 一直 Loading：延长轮询到 30s，仍失败则换官方新闻稿
- 找不到正式版资料：**不硬凑**，写「官方尚未公布」
