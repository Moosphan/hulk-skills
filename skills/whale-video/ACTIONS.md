# 小紫动作立绘（20 张 · 2026-11-05）

来源：`lavender-actions-all-2026-11-05`。两套各 10 张，同一编号是同一动作。

- `assets/actions-normal/`：正常比例，半身到胯，1536×2048 透明
- `assets/actions-chibi/`：Q 版全身，1536×2048 透明
- 总览图：`assets/preview-normal.jpg`、`assets/preview-chibi.jpg`

## 1. 和现有两套的区别

| 套 | 内容 | 用途 |
|---|---|---|
| `assets/emotes/`（20 张） | 半身**情绪** | 正片里"她现在什么表情" |
| `assets/chibi/`（12 张） | Q 版全身**情绪** | 封面、片头片尾 |
| `assets/actions-*`（20 张） | **动作/姿势** | 正在做什么：讲解、挠头、叹气、冲刺… |

动作图带手部动作和身体朝向，适合"她在做一件事"的画面；情绪图适合"她在想什么"。

## 2. 索引（两套同名）

| 编号 | 动作 | 文件 |
|---|---|---|
| 01 | 眨眼敬礼 | `01-wink-salute.png` |
| 02 | 掩嘴偷笑 | `02-covered-laugh.png` |
| 03 | 认真讲解 | `03-explaining.png` |
| 04 | 挠头疑惑 | `04-head-scratch.png` |
| 05 | 扶额叹气 | `05-facepalm.png` |
| 06 | 擦泪委屈 | `06-wiping-tears.png` |
| 07 | 握拳冲刺 | `07-ready-go.png` |
| 08 | 捂脸害羞 | `08-shy-cheeks.png` |
| 09 | 困困伸懒腰 | `09-stretch.png` |
| 10 | 飞吻告别 | `10-blowing-kiss.png` |

## 3. 放置参数

可见区约 1340×1840（底部留白约 104），必须按 alpha 可见区定位。

```python
e = Image.open(path).convert("RGBA")
sc = H * hr / e.height          # hr 相对整张 2048 高画布
e = e.resize((int(e.width*sc), int(e.height*sc)), Image.LANCZOS)
bb = e.getbbox()
img.alpha_composite(e, (W - right - bb[2], H + bottom - bb[3]))
```

| 套 | 场景 | hr | right | bottom |
|---|---|---|---|---|
| normal | 正片右 | 0.95 | -20 | 60 |
| normal | 封面 16:9 | 1.05 | -10 | 30 |
| normal | 封面 4:3 | 0.95 | 0 | 24 |
| chibi | 正片右 | 1.10 | 40 | 30 |
| chibi | 封面 16:9 | 1.35 | 20 | 10 |
| chibi | 封面 4:3 | 1.22 | 10 | 10 |

- normal 是半身到胯，底部本来就是切开的，`bottom` 可以给正值让它贴住画面底。
- chibi 是全身，脚必须压出画框 10–20px，否则悬空。
- 两套不要同屏混用；一集最多换 3–4 个动作。

## 4. 选图规则

1. 讲解类段落用 03 认真讲解；卡壳/数据看不懂用 04 挠头、05 扶额。
2. 结论/打脸用 07 握拳；自嘲用 02 掩嘴偷笑。
3. 片尾道别用 10 飞吻；片头用 01 敬礼（和 chibi 的 08 加油对应）。
4. 动作图已经是完整插画，不要再叠加表情素材。
