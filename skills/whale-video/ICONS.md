# 三连图标规范（点赞 / 投币 / 收藏 / 关注）

片子里的三连按钮**不许用文字或手绘形状代替**，一律用 B 站官方 iconfont 字形。

## 1. 素材

- 字体：`assets/fonts/bili-icon.ttf`（B 站视频页 `iconfont` 字体，`vanfont`）
- 成品：`assets/icons/like.png`、`coin.png`、`collect.png`、`follow.png`（1024px 透明 PNG）
- 字形名（重新导出时用）：

| 图标 | 字形 | 色值 |
|---|---|---|
| 点赞 | `videodetails_like` | `#00AEEC` |
| 投币 | `videodetails_throw` | `#FFB800` |
| 收藏 | `videodetails_collec` | `#FFAC38` |
| 关注 | `general_addto_s` | `#FB7299` |

## 2. 重新导出（需要换色/换尺寸时）

```python
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
f = TTFont("assets/fonts/bili-icon.ttf"); rev = {v: k for k, v in f["cmap"].getBestCmap().items()}
ft = ImageFont.truetype("assets/fonts/bili-icon.ttf", 300)
t = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
ImageDraw.Draw(t).text((210, 210), chr(rev["videodetails_like"]), font=ft, fill=(0,174,236,255), anchor="mm")
t = t.crop(t.getbbox()); s = 1024 / max(t.size)
t.resize((int(t.width*s), int(t.height*s)), Image.LANCZOS).save("like.png")
```

- 必须**从字体渲染**（矢量轮廓，1024px 起），不要用 PIL 多边形手画——会出锯齿。
- 导出后检查：放大到 200% 边缘应是平滑灰阶，没有阶梯。

## 3. 画面里的用法（片尾三连）

```
圆环 132×132，border 4px 品牌色
图标按比例居中：点赞 0.60 / 投币 0.62 / 关注 0.46
关注要明显比另外两个小（字形本身是细十字，撑满会显大）
下方文字 22px 灰色：点赞 / 投币 / 关注
```

Remotion 写法：

```tsx
<div style={{ width: 132, height: 132, borderRadius: "50%", border: `4px solid ${c}`,
              display: "flex", alignItems: "center", justifyContent: "center" }}>
  <Img src={staticFile("icons/like.png")} style={{ width: 132 * k, height: 132 * k, objectFit: "contain" }} />
</div>
```

- 三个图标等距 80px，整组居中在左半区，不要压到人物。
- 出现顺序：点赞 → 投币 → 关注，弹入 `spring(damping 11, stiffness 160)`，间隔 10 帧。

## 4. 检查项

- [ ] 四个图标都来自字体，不是文字"赞/币/+"或手绘
- [ ] 圆环是品牌色，粗细 4px（1080p 下）
- [ ] 关注图标明显小于点赞/投币
- [ ] 图标与文字标签上下对齐，间距 14px
