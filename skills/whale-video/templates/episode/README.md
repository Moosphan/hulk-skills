# 鲸鱼娘单集模板（复用包）

一集 = **同一套组件 + 不同 cues**。不要每期重写背景、片头、片尾、物件。

## 文件
- `theme.ts`：色板 C、字体 F（唯一色源）
- `ui.tsx`：Backdrop（深海夜光）、HUD、Rights、Caption、Paper、Stamp、Emote、Scene、enter/fade
- `Episode.example.tsx`：一集完整结构（片头 → 场景 → 片尾）
- `Cover.tsx`：封面，复用同一个 Backdrop

## 用法
1. 新项目里建 `src/`，放入 `theme.ts`、`ui.tsx`、`Cover.tsx`
2. 只写 `cues.json`：每句 `{id,text,start,dur,scene}`
3. 写 `Episode.tsx`：按 `scene` 切场，每场放 1 主物件 + 1 辅物件
4. 片头、片尾固定用模板里的实现，不改尺寸/颜色
5. 封面用 `npx remotion still Cover <out> --frame=20`，不另画背景

## 硬规则
- 背景只允许 `ui.tsx` 的 Backdrop，禁止另写渐变/光效
- 立绘只用 `assets/emotes`（正片）与 `assets/chibi`（封面/片头片尾）
- 封面背景必须由同一个 Backdrop 渲染，禁止 PIL 另画
- 片尾三连固定 132px、gap 80、spring damping 11 / mass .5 / stiffness 160
