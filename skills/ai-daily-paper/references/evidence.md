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

## X 卡片修复：Tweet not found（2026-11-06）
现象：react-tweet 渲染成 “Tweet not found”，但 vxtwitter API 有数据。
原因：浏览器直连 `cdn.syndication.twimg.com` 被墙，curl 走代理却是通的。
做法：
```bash
curl -sL --proxy http://127.0.0.1:7897 "https://cdn.syndication.twimg.com/tweet-result?id=<ID>" -o /tmp/syn.json
```
```js
await p.route('https://cdn.syndication.twimg.com/**', r => r.fulfill({status:200, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body: fs.readFileSync('/tmp/syn.json','utf8')}));
// 再打开 http://127.0.0.1:4399/?id=<ID>
```
样式：`*{box-shadow:none!important;border-radius:0!important}`，截图后裁 16px 边。

## X 卡片：一条命令（2026-11-06 定稿）
```bash
cd ~/dsh-video-remotion/news-video
node ~/.dsh/skills/ai-daily-paper/templates/tweet-render/render.mjs <tweetId> /tmp/x.png
python3 -c "from PIL import Image;im=Image.open('/tmp/x.png');w,h=im.size;im.crop((16,16,w-16,h-16)).save('/tmp/x.png')"
```
- 模板目录已装 `playwright@1.63.0`（必须和 news-video 版本一致，否则报找不到浏览器）
- `render.mjs` 内置 3 次重试，出现 “Tweet not found” 会自动重试；仍失败才是网络问题
- 代理默认 `http://127.0.0.1:7897`，可用 `HTTPS_PROXY` 覆盖
- 实测：浏览器直连 `cdn.syndication.twimg.com` 走代理是通的，之前失败是偶发 + 版本不匹配，不是墙

## 证据形式清单（每条主线至少 3 种不同载体）
1. 官方 blog 正文截图
2. System Card / 技术报告表格（如 Table 5/6）
3. benchmark 柱状图或表格
4. Hugging Face 模型卡（下载量、license、部署方式）
5. changelog / 定价页
6. 官方 demo 视频帧（X 原帖视频、YouTube 演示）
7. 真机/应用截图（手机、桌面端）
8. X 原帖卡片（react-tweet 渲染，见本文开头流程）
9. 官方架构图 / 公告配图

禁止：同一张图重复出现在多个面板；纯文字段落占满 4 格。

## 新模型发布：视频证据优先（2026-11-11 主人定）
遇到「新模型发布 / 官方演示」类新闻，证据优先级改为：
1. **官方演示视频**（X 原帖里的视频、官方发布视频、发布会录屏）——下载后直接嵌进画面播放
2. **演示作品截图**（视频里的关键帧、官方示例图）
3. 官方文字页 / 博客截图
4. 媒体转述截图

获取方法（已验通）：
```bash
# 1. 拿 vxtwitter JSON，取 mediaURLs
curl -sL "https://api.vxtwitter.com/i/status/<ID>" | python3 -c "import json,sys;print(json.load(sys.stdin)['mediaURLs'])"
# 2. 下载 mp4（带代理）
curl -L -A "Mozilla/5.0" "<video.twimg.com 链接>" -o public/evidence/<name>.mp4
# 3. 截取可用片段（无声，避免压掉旁白）
ffmpeg -y -ss 0 -t 12 -i <full>.mp4 -an -c:v libx264 -crf 20 <clip>.mp4
# 4. edition 里给 scene 加 "video": "evidence/<clip>.mp4"
```
模板已支持：`VideoPaper` 的 Story 在 `video` 字段存在时渲染 `OffthreadVideo muted`（380px 高，objectFit cover）。
截图只作补充，不允许整段只有一张静态图。

## 第三方测评视频（2026-11-11 定，优先 X）
**来源优先级：X 高热度原帖 > YouTube 测评 > 媒体转述。** X 是首选，不是兜底。

选片硬标准（缺一不可）：
- 平台：**X 原帖**（有 status ID，能出卡片/能下视频）
- 热度：**播放 ≥ 10 万或点赞 ≥ 2,000**；同一模型有多条时挑互动最高的
- 内容：有具体数字（指数分、价格、耗时、跑分），不是"感觉很厉害"
- 作者：有蓝标或可辨认的测评者/机构（@itsPaulAi、@scaling01、@ArtificialAnlys、@lmarena_ai 等）

获取流程：
1. `r.jina.ai/https://x.com/<handle>` 找候选帖 → 记录正文与互动数
2. 媒体文章 HTML 里 grep `status/(\d+)` 拿 ID（jina 输出常不带 ID）
3. `api.vxtwitter.com/i/status/<ID>` 取 `mediaURLs` → 下载 mp4 → ffmpeg 截 10 秒
4. 只有 X 上确实没有可用视频时，才降级到 YouTube（标注"降级来源"）
```bash
yt-dlp --proxy http://127.0.0.1:7897 "ytsearch5:<模型名> review" --print "%(id)s | %(title)s | %(duration)s"
yt-dlp --proxy http://127.0.0.1:7897 -f "bv*[height<=720]/b[height<=720]" -o "/tmp/rev.%(ext)s" "https://www.youtube.com/watch?v=<id>"
ffmpeg -y -ss 60 -t 10 -i /tmp/rev.mp4 -an -vf scale=1280:-2 -c:v libx264 -crf 22 public/evidence/<name>-review.mp4
```
- 选片标准：有具体数字（指数分、价格、耗时）的评测段，不要开场闲聊
- scene 里加 `"video": "evidence/<name>-review.mp4"`，标题写「第三方测评」，正文写他给出的具体结论
- 画面角标注明作者与平台（如「Kagan Erkan · YouTube」）

## X 检索（无 API Key 的实测结论，2026-11-11）
工具：`tools/x-find.py "关键词" --only-video --min-likes 200`
链路：DuckDuckGo HTML（`html.duckduckgo.com/html/?q=site:x.com+"关键词"`，返回 status 链接）→ `api.vxtwitter.com` 取互动/媒体 → 按点赞排序。

实测有效性：
- ✅ DDG HTML：能出 status ID（首轮拿到 8 条），但**连续查询会 202 限流**，需间隔数分钟 + 换 UA
- ❌ x.com/search（登录墙）、xcancel（451）、Bing/Mojeek（不返回 x.com 链接）、searx.be（验证码）
- ❌ lite.duckduckgo.com（同样 202）

开源可参考（按可行性）：
1. **twscrape**（Python，需一个可登录的小号 cookie，能搜索、能翻页，最稳）
2. **twikit**（同上，登录态 + 搜索 API）
3. Nitter 系（多数实例已死，只剩零星可用）
4. snscrape（2023 起基本失效，不要用）
5. RSSHub 的 twitter 路由（需 auth token）

结论：**要稳定搜 X，必须给一个登录态或 API key**；无凭证时只能用 DDG 碰运气 + 已知 ID 直取。

## X 登录态获取与检索（2026-11-11 全流程跑通，照抄即可）

### 1. 一次性：拿到 auth_token + ct0
`auth_token` 是 httpOnly，DevTools 里常看不到。直接从本机 Chrome 解密：

```bash
# 前提：Chrome 里已登录小号（哪个 profile 都行，默认 Default）
cd ~/dsh-video-remotion
.venv-x/bin/python ~/.dsh/skills/ai-daily-paper/templates/x/chrome-cookie.py
# 输出 auth_token / ct0，并写入 ~/dsh-video-remotion/.x-cookies.json
```
实现：读 `~/Library/Application Support/Google/Chrome/Default/Cookies` → Keychain `Chrome Safe Storage` → PBKDF2(saltysalt, 1003) → AES-CBC(v10) → 去掉 32 字节 host hash。

### 2. 一次性：装 twscrape 并导入账号
```bash
cd ~/dsh-video-remotion
python3 -m venv .venv-x && .venv-x/bin/pip install twscrape cryptography
.venv-x/bin/python - <<'PY'
import json, asyncio
from twscrape import AccountsPool
ck = json.load(open('.x-cookies.json'))
async def main():
    pool = AccountsPool("x_accounts.db")
    await pool.add_account("zya_burner", "", "", "",
        cookies=f"auth_token={ck['auth_token']}; ct0={ck['ct0']}",
        proxy="http://127.0.0.1:7897")
    await pool.login_all()
asyncio.run(main())
PY
```

### 3. 每次检索：按播放量排序
```bash
.venv-x/bin/python ~/.dsh/skills/ai-daily-paper/templates/x/x-search.py \
  '"Gemini 4 Carbon"' --limit 50 --min-faves 20 --out /tmp/x.json
```
输出 `views / likes / user / text / videos[]`，按 views 降序。twscrape 的 `t.media` 是对象**不可迭代**，要用 `.videos` / `.animated`。

### 4. 下载证据视频
```bash
bash ~/.dsh/skills/ai-daily-paper/templates/x/x-video.sh "<video.twimg.com 链接>" 3 11 public/evidence/xxx-x.mp4
```

### 5. 硬限制
- X 搜索接口 **约每 15 分钟放行一次**（`SearchTimeline` 队列），一天 3 次巡检刚好
- Playwright 直开 x.com 登录会被拦（报「出现意外错误」），**不要走浏览器自动化登录**
- 无凭证兜底：DDG HTML `site:x.com "关键词"`（会 202 限流）→ `api.vxtwitter.com` 取正文

## 首选：catbus X（2026-11-11 确认）
catbus 自带 X 支持，**带播放量**，比 twscrape 更好用，优先用它。

```bash
# 一次性：cookie 登录（必须带 --proxy，否则超时）
node ~/self-projects/catbus/dist/cli/main.js -a main_x --proxy http://127.0.0.1:7897 \
  x auth login --cookie @/tmp/xck.txt --method cookie

# 搜索视频帖（--type video，按热度返回，带 views/likes）
node ~/self-projects/catbus/dist/cli/main.js -a main_x --proxy http://127.0.0.1:7897 \
  x item search "Gemini 4 Carbon" --type video --limit 8
# 支持 --sort latest、--type video|image、--limit N、--all、--cursor

# 取单条（含媒体 URL）
node ... --raw x item get <ID>

# 下载媒体（注意：大文件常超时，建议改成 curl 直下）
node ... x item download <ID> --dir /tmp/xdl
```
下载失败时的替代：`--raw x item get <ID>` 里 grep `https://video.twimg.com/...mp4`，再
`curl -sL --proxy http://127.0.0.1:7897 "<url>" -o /tmp/x.mp4`。

实测样例（Gemini 4 Carbon）：@Google 1,426,135 播放 / @GoogleAI 279,038 / @lyraxana 99,537（三代同测）/ @GoogleDeepMind 58,748 / @lucasjvds 23,273。
