# L1 证据层：第一现场与引证

## 证据优先级

1. 官方博客 / 公告原文
2. 官方 X 原帖 / 产品后台截图 / GitHub commit diff
3. 权威媒体原文（B 级）
4. 第三方转引（仅线索，不进画面）

## 证据卡五要素

1. **原文引证**：带「」的原始句子，不改写
2. **原始出处**：账号/机构 + 时间 + 链接
3. **关键数据**：3 个以内 chips（参数/价格/日期）
4. **为什么重要**：一句判断，不复述左边
5. **可信度标记**：官方 / 爆料 / 转引

## 截图规则

- 只截正文关键段，裁掉导航、URL 栏、右侧推荐、广告
- 推文截图必须含：作者、时间、正文
- 页面截图用 Playwright 元素截图，不用整页
- 拿不到截图：写「截图不可得」+ 链接，不得用网页截图冒充

## 常见坑

- 163 等页面标题 ≠ 原始出处；必须点进去找源头
- 源码泄漏类：证据是 HTML 源码片段或原作者推文，不是媒体标题
- 榜单数字：必须带榜单名 + 更新日期 + 口径

## 证据素材获取（2026-11-04）

### 一、文字线索（RSS / API）
- OpenAI 官方：`https://openai.com/news/rss.xml`
- Microsoft 官方博客：`https://blogs.microsoft.com/feed/`
- Anthropic：无 RSS，抓 `anthropic.com/news` 列表页
- HuggingFace Blog：`https://huggingface.co/blog/feed.xml`
- arXiv：`http://export.arxiv.org/rss/cs.AI`
- The Verge / TechCrunch：均有 `/rss`
- X：RSSHub 自建 `rsshub.app/twitter/user/<id>`，或用 official API v2，或用 `platform.twitter.com/embed/Tweet.html?id=<id>` 渲染截图

### 二、截图（静态证据）
Playwright 脚本，带登录 cookie，`viewport 1400×900`，`deviceScaleFactor 2`，等 2s 再截；裁掉导航栏，只留正文。

### 三、录屏（动态证据）
同一 Playwright 上下文开 `recordVideo`，滚轮模拟浏览，得到 webm，可直接放进 Remotion `OffthreadVideo`。
真实产品演示用 OBS 或 QuickTime 录屏。

### 四、X 原帖
优先官方 API 拿原帖 JSON；没有 key 时用 embed 页截图；再不行用 RSSHub。

### 五、证据卡规则
- 每条新闻至少 1 张可用证据，最多 3 张
- 优先顺序：官方原文截图 > 官方 X 帖 > 产品界面 > 媒体转述
- 403/验证码/空白页一律弃用

### 截图工具（2026-11-04）
脚本：`news-video/tools/capture-evidence.mjs`

```bash
node tools/capture-evidence.mjs <url> <out.png>
node tools/capture-evidence.mjs <x-status-url> <out.png> --x
HTTPS_PROXY=http://127.0.0.1:7890 node tools/capture-evidence.mjs <url> <out.png>
```

规则：
- 自动点掉登录/订阅/注册弹窗（aria-label close、×、modal 内按钮），再按 Esc
- 删除 `position: fixed` 悬浮层和 cookie/newsletter 条
- 优先截 `article`/`main` 正文元素，取不到才整页
- 输出用 `object-fit: contain` 展示，禁止裁切

### X 原帖获取（有代理）
1. **官方 API v2**：`GET /2/tweets/:id?expansions=author_id,attachments.media_keys`，Bearer Token
2. **登录态截图**：Playwright 注入 cookies，代理走 `HTTPS_PROXY`，截 `article[data-testid="tweet"]`
3. **免登录 embed**：`platform.twitter.com/embed/Tweet.html?id=<id>`，脚本 `--x` 模式
4. **RSSHub 自建**：`/twitter/user/<screen_name>`，配合代理

优先级：API > 登录态截图 > embed > RSSHub。

### X 原帖深挖（免代理，2026-11-04 验证）
直连 x.com 不通，但可以这样拿到原帖：

1. **定位帖子 ID**：媒体文章会嵌入推文，`curl` 文章 HTML，正则 `(?:x|twitter)\.com/(user)/status/(\d+)`
2. **取原帖内容**：`https://api.vxtwitter.com/i/status/<id>` 返回 JSON（作者、正文、时间、点赞、转推、回复）
3. **渲染卡片**：`tools/tweet-card.mjs <status-url|id> <out.png>`
4. 卡片含头像、蓝标、@handle、正文、时间、互动数，可直接作为证据窗口素材

### 搜索帖子 ID 的入口
- 搜索 `site:x.com <关键词>` / `<账号名> status`
- 外媒报道（Frandroid、TechCrunch、The Verge）正文常嵌入推文
- 官方账号：@OpenAI @AnthropicAI @thsottiaux @MistralAI @Alibaba_Qwen @DeepSeek_ai

## 证据体系 2.0（2026-11-04）

### 信息源分级
**T1 一手官方**
- 官方博客/Newsroom：OpenAI、Anthropic、Microsoft、Google、Mistral、Meta
- 官方 changelog / release notes / version log
- 官方文档、定价页、状态页
- GitHub Release / commit / PR diff、HF 模型卡
- 政府/法院/监管原文（发改委、法院公告、SEC）

**T2 官方账号**
- X：@OpenAI @AnthropicAI @MistralAI @thsottiaux @Alibaba_Qwen @DeepSeek_ai
- 获取：媒体文章扒 status id → `api.vxtwitter.com/i/status/<id>` → 卡片渲染

**T3 追踪站/社区**
- codex-resets.com（Tibo 重置历史，含 View on X）
- LMArena / LiveBench / OpenRouter / Artificial Analysis
- Hacker News、Reddit 原帖

**T4 权威媒体**
- Reuters、Bloomberg、FT、WSJ、The Verge、TechCrunch、Ars Technica
- 国内：新华社、财联社、机器之心、量子位、InfoQ

### 证据形态（至少一种，优先前三种）
1. 截图卡（原文页，裁到标题+导语）
2. X 原帖卡（头像/蓝标/正文/时间/互动）
3. 产品界面/演示截图
4. 录屏片段（滚动、点击、演示）
5. changelog/版本日志片段
6. 代码 diff / GitHub release
7. 图表（榜单、价格、参数对比）
8. 音频/官方播客片段

### 失败与替换
- 403/验证码/空白/弹窗无法关闭 → 换源：官方站 > 官方 X > 追踪站 > 媒体
- 连续 3 个源不可用，才允许标「原始出处不可得」
- 同一事件至少准备 2 个候选源

### 版式
- 不改报纸主版式；证据以浮动窗口覆盖，宽 800，纸色边框 + 投影
- 图片 `contain`、不留黑边、不裁切；来源条 + 「证据」角标
- Tibo 重置页必须附 codex-resets.com 卡片或 @thsottiaux 原帖

### OpenAI 访问受限（2026-11-04 实测）
- `openai.com/news/`、`openai.com/index/*` 在本机返回 **403**（Cloudflare 区域拦截），换 UA 无效
- `openai.com/news/rss.xml` 返回 **200**，含全部标题、日期、原文链接（无正文）
- 处理顺序：
  1. 有代理：`HTTPS_PROXY=... node tools/capture-evidence.mjs <url> out.png`
  2. 无代理：用 RSS 元数据生成「OpenAI 官方 RSS」证据卡（标题 + 日期 + 原文链接），标明来源为 RSS
  3. 需要正文时，改引权威媒体原文（Reuters/The Verge/36氪）并明确标注为转述
- 禁止把 403 白屏截图放进成片

### 代理与 OpenAI（2026-11-04 定位）
- 根因：本机走系统代理 `127.0.0.1:7897`（Clash），Shell/Playwright 默认不走系统代理，所以 openai.com 直连 403
- 修复：`capture-evidence.mjs` 自动读 `scutil --proxy` 的 HTTPSProxy/HTTPSPort，无需手填
- 仍需配合：真实 UA、`waitForSelector('h1, article, main h2')`、加载后滚过 hero（OpenAI 首屏是渐变遮罩）
- 实测：代理 + UA + 滚动后，openai.com/news 与具体文章均可截图
- X 走同一代理后可直接访问；无代理时仍用 vxtwitter 卡片

### 录屏与演示视频（2026-11-04 修正）
- **不要**用 Playwright `recordVideo`（headless 常拍空白），也**不要**用 4fps 逐帧截图（卡顿）
- 正确做法：CDP `Page.startScreencast` 抓帧 + `minterpolate=fps=30` 插值，输出 30fps
- 录制前先点掉 cookie/订阅弹窗，避免横幅入镜
- 可混入官方/非官方演示视频：直接放 `public/evidence/video/*.mp4`，`evidenceType:'video'`

### 变更证据优先级
1. GitHub Release / commit 页面**截图**
2. 官方 changelog 页面截图
3. 文字卡片（仅兜底，需标注版本号/日期/来源）

### 录屏清晰/流畅（2026-11-04 二次修正）
- 用 **有头浏览器**（`headless:false`）+ `recordVideo` 1080p/1280×800，直接得到 25–30fps 的真实录屏
- 再用 ffmpeg 转 mp4（`fps=30, scale=1280:800, crf 20`），不做插值，避免拖影
- 录制前点掉 cookie 横幅；用 `window.scrollTo` 分步滚动，速度放慢
- 官方/非官方演示视频可直接放 `public/evidence/video/*.mp4`

### 长截图可读性
- GitHub/官网长页面：先裁到「版本号 + 前 2–3 条改动」区域，再进窗口
- 不要整页缩进 800px 窗口，否则字太小
- 裁剪宽高比控制在 2.2–2.4，窗口内文字才清楚

### 录屏最终方案（2026-11-04 三修）
- **无头浏览器** + CDP `Page.startScreencast`
- 页面内用 `requestAnimationFrame` 平滑滚动 8 秒，触发持续重绘
- 帧率可达 ~30fps（实测 470 帧 / 8 秒），按 30fps 直接编码，**不做插值**
- 不再使用有头浏览器、不再用 4fps 截图

### 截图完整性与清晰度
- 一律**完整视口截图**（1200–1440 宽，deviceScaleFactor 2），禁止裁掉右/下内容
- GitHub Release 类页面：滚到版本头，保证「版本号 + 日期 + Highlights 前 6 条」都在画面内
- 窗口内展示时用 `contain`，不加裁切；清晰度靠 2x 像素密度

### 证据命中检查（2026-11-05 强制）
截图不能只截首页/列表，必须命中该条新闻的关键词：
```bash
node tools/capture-evidence.mjs <url> <out.png> --expect="SenseNova 6.8 Flash"
```
- 脚本加载后检查 `body.innerText` 是否包含任一关键词；不命中直接退出码 3，不出图
- 命中后自动滚动到含关键词的段落再截图
- 同时写 `<out>.meta.json`：`{url, expect, ok}`

检查规则：
1. 每条资讯必须有证据图，或原文文字引用（quote 卡）
2. 有图时，图里必须能读到该条的关键数字/型号/标题
3. 列表页、首页、导航页截图不算证据
4. 跑 `python3 tools/check-evidence.py <img...>`，FAIL 不许进片
5. 图片证据缺失时，必须补 quote 卡（标注来源），不能空着

### 截图规范（2026-11-05 升级）
- 设备像素比 **3x**，最终图 ≥2400px 宽
- 用 `--expect` 命中关键词后，只截**关键词所在段落**（宽 ≤780、高 ≤380），不截整页
- 自动隐藏 `aside/footer/nav/form` 与 comment/sidebar/advert/related/recommend/follow/share 区块
- 禁止把广告、评论区、关注栏、相关推荐带进画面
- 每张证据图必须能读出：标题或型号 + 关键数字

### 截图裁切（2026-11-05 再修）
- 先按关键词选**最小、最深的正文块**（p/li/h2/h3），宽 >320、高 >80 CSS px
- 裁切范围 = 该块外接框 + 12px 内边距，宽度不得超过 1100 CSS px
- 高度至少 240 CSS px，避免只截到一行
- 禁止按固定坐标裁整页；禁止把导航/侧栏/评论一起带入
- 输出后人工看一眼：每行中文必须完整，不得右边截断

### X 帖子优先
- 有原帖 ID 时，一律先做 X 卡片（`tools/tweet-card.mjs`），比网页截图干净
- 拿不到 ID（X 需登录、搜索引擎无索引）时，再用官方页或媒体正文截图
- 卡片必须含头像、蓝标、@handle、正文、时间

## 正文截图 SOP（2026-11-05 定稿）

### 抓取
1. `deviceScaleFactor: 3`，视口 1200×900
2. `--expect="关键词1,关键词2"`：正文必须命中，否则退出码 3，不出图
3. 选**最小、最深的正文块**（p/li/h2/h3），宽 >320、高 >80 CSS px
4. 裁切 = 该块外接框 + 12px 内边距，宽 ≤1100 CSS px，高 ≥240 CSS px
5. 隐藏 `aside/footer/nav/form` 与 comment/sidebar/advert/related/follow/share

### 验收（人工 + 脚本）
- 每一行中文完整，右侧不截断
- 画面里能读到：型号/标题 + 关键数字
- 不出现导航条、二维码、评论区、关注按钮、相关推荐
- `python3 tools/check-evidence.py <img>` PASS（>20KB、≥600×400、非白屏）
- 尺寸目标：宽 1800–3200px

### 失败处理
- 截图被裁断/带侧栏 → 重抓，不许将就
- 媒体页反爬（163/搜狐常见）→ 换 36氪/财联社/新浪/凤凰/官方
- 连续 3 个源失败 → 该条降级或剔除

## X 原帖抓取（2026-11-04 已验证可用）
直连 x.com 需要登录，**不要**用 Playwright 打开 x.com（返回空页）。可用链路：

1. **拿 status ID**
   - 媒体文章 HTML：`curl -sL <url> | grep -oE '(x|twitter)\.com/[A-Za-z0-9_]+/status/[0-9]+'`
   - 搜索：`site:x.com <关键词>`、`<账号> status <关键词>`
   - 官方博客/新闻稿里的嵌入推文
- **英文科技站的推文嵌入**（techcityauthority、TNW、The Verge）HTML 里常有 `status/<ID>`，这是今天找到 OpenAI Images 2.6 原帖的路径
2. **取原帖数据**
   ```bash
   curl -sL "https://api.vxtwitter.com/i/status/<ID>"
   ```
   返回作者、蓝标、正文、时间、点赞/转推/回复/浏览
3. **渲染卡片**
   ```bash
   node tools/tweet-card.mjs "https://x.com/i/status/<ID>" out.png
   # 或
   scripts/x-card.sh <ID> out.png
   ```
   卡片规格：1040 宽、2x、头像 + 蓝标 + @handle + 正文 + 时间 + 互动数
4. **验收**：卡片能读到发布者、正文、时间；空白/登录墙一律重来

### 何时放弃 X
- 搜不到 ID 且正文无嵌入 → 降到官方页面
- vxtwitter 返回空 → 换官方页面，别反复试 x.com

### 为什么昨天能成功
昨天的 Anthropic / Tibo 帖子，都是**先从媒体报道 HTML 里扒出 status ID**，再走 vxtwitter，而不是直接打开 x.com。

## X 卡片：改用开源 react-tweet（2026-11-05）
自绘卡片样式不对，改用 **vercel/react-tweet**（GitHub 1.8k star，X 官方风格，带媒体/时间/互动数）。

流程：
1. `templates/tweet-render/`：Vite + React + react-tweet
2. `npm i && npx vite build`
3. `python3 -m http.server 4399 -d dist`
4. Playwright 打开 `http://127.0.0.1:4399/?id=<ID>`，截 `article` 元素（3x）
5. 本地地址要 `bypass: '127.0.0.1,localhost'`，否则代理会返回 502

产出特征：头像 + 认证徽章 + @handle + 正文 + 媒体（视频/GIF 封面）+ 时间 + 点赞/回复 + Read replies。

## X 帖子卡规范（2026-11-05 定稿）
- 用开源 **vercel/react-tweet**（1.8k star）渲染，不要自绘
- 本地工程：`templates/tweet-render/`（Vite + React），`npm i && vite build`，`python3 -m http.server 4399 -d dist`
- Playwright 打开 `?id=<tweet-id>`，截 `article` 元素，3x
- **必须**：`* { box-shadow: none !important }`；卡片本体 `border-radius: 0`（按钮保留圆角）
- 截图后四边各裁 16px，去掉圆角外溢的灰边
- 代理要 `bypass: 127.0.0.1,localhost`，否则本地服务 502
- 卡片应包含：头像、认证徽章、@handle、正文、媒体（图/GIF 封面）、时间、点赞
- 验收：四角无灰边、无投影、正文完整
