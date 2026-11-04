#!/usr/bin/env python3
"""封面生成器 · 深海底 + 紫标签 + 珊瑚色块 · 双比例

用法：
  python3 cover.py                    # out/cover-16x9.png + out/cover-4x3.png
  python3 cover.py --ratio 4x3        # 只出 4:3
  python3 cover.py --out a.png --ratio 16x9
"""
import os, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))

COPY = {
    "badge": "番外", "day": "DAY 8",
    "line1": "体检", "line2": "挂了", "tile": "3", "after": "项",
    "sub": "最后 60 分，刚好及格",
    "note": "含 AI 生成内容 · 非官方二创",
    "emote": "19-overwhelmed.png",
}

# 亮紫主色（B）。想换深紫 A：chip/tile 改 (124,92,224)，chip_fg/tile_fg 改 (255,250,255)
P = dict(bg1=(6, 11, 22), bg2=(10, 16, 30), beam=(16, 38, 74), halo=(92, 140, 220),
         chip=(124, 92, 224), chip_fg=(255, 250, 255),
         tile=(226, 88, 72), tile_fg=(255, 246, 242),
         ink=(250, 247, 240), sub=(226, 231, 242), note=(206, 212, 224))

LAYOUT = {
    "16x9": dict(W=1920, H=1080, m=96, chip=(36, 32, 68), head=190, sub=64,
                 y_chip=96, y_l1=470, y_sub=856,
                 char=(1.10, -30, 148, "square"), halo=(1480, 400, 560, 120)),
    "4x3": dict(W=1440, H=1080, m=72, chip=(30, 26, 58), head=136, sub=46,
                y_chip=84, y_l1=404, y_sub=760,
                char=(1.00, 10, 30, "visible"), halo=(1180, 360, 400, 130)),
}

def find(paths, what):
    for p in paths:
        if os.path.exists(p):
            return p
    sys.exit(f"找不到 {what}：{paths}")

PING = "/System/Library/Fonts/PingFang.ttc"
SF = "/Library/Fonts/SF-Compact-Display-Black.otf"
KUA = find([
    os.path.join(ROOT, "assets", "fonts", "ZCOOLKuaiLe-Regular.ttf"),
    os.path.join(ROOT, "..", "..", "assets", "fonts", "ZCOOLKuaiLe-Regular.ttf"),
    os.path.expanduser("~/dsh-space/whale-video/assets/fonts/ZCOOLKuaiLe-Regular.ttf"),
], "站酷快乐体")
EMOTE = find([
    os.path.join(ROOT, "public", "emotes", COPY["emote"]),
    os.path.join(ROOT, "assets", "emotes", COPY["emote"]),
    os.path.join(ROOT, "..", "..", "assets", "emotes", COPY["emote"]),
], "表情图")

def FP(sz, w="semibold"):
    return ImageFont.truetype(PING, sz, index={"regular": 2, "medium": 5, "semibold": 8}[w])

def FS(sz): return ImageFont.truetype(SF, sz)
def FK(sz): return ImageFont.truetype(KUA, sz)

def background(W, H):
    img = Image.new("RGB", (W, H), "#060B16")
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(P["bg1"][i] * (1 - t) + P["bg2"][i] * t) for i in range(3)))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for x in [W * 0.13, W * 0.36, W * 0.61, W * 0.81]:
        gd.polygon([(x, -200), (x + 140, -200), (x + 420, H + 120), (x + 40, H + 120)], fill=P["beam"])
    img = Image.blend(img, Image.blend(img, glow.filter(ImageFilter.GaussianBlur(95)), 0.9), 0.55)
    d = ImageDraw.Draw(img)
    random.seed(11)
    for _ in range(64):
        x, y, r = random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 6)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(150, 190, 235), width=1)
    return img.convert("RGBA")

def halo(img, W, H, cx, cy, r, alpha):
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    a = np.clip(1 - dist, 0, 1) ** 1.5 * alpha
    layer = Image.new("RGBA", (W, H), P["halo"] + (0,))
    layer.putalpha(Image.fromarray(a.astype(np.uint8)))
    return Image.alpha_composite(img, layer)

def character(img, W, H, hr, a, b, mode="square"):
    """square: 按整张图定位（a=右偏移, b=底偏移）；visible: 按可见区定位（a=右边距, b=底部裁切）"""
    e = Image.open(EMOTE).convert("RGBA")
    sc = H * hr / e.height
    e = e.resize((int(e.width * sc), int(e.height * sc)), Image.LANCZOS)
    if mode == "square":
        x, y = W - e.width + a, H - e.height + b
    else:
        bb = e.getbbox()
        x, y = W + a - bb[2], H + b - bb[3]
    img.alpha_composite(e, (x, y))
    return img

def chip(d, x, y, text, size, h, fg=None, bgc=None, padx=None, r=18):
    f = FP(size, "semibold")
    padx = padx or int(size * 0.85)
    w = d.textlength(text, font=f) + padx * 2
    d.rounded_rectangle([x, y, x + w, y + h], r, fill=bgc or P["chip"])
    d.text((x + padx, y + h / 2), text, font=f, fill=fg or P["chip_fg"], anchor="lm")
    return w

def outline_chip(d, x, y, text, size, h, padx=None, r=18):
    f = FP(size, "semibold")
    padx = padx or int(size * 0.8)
    w = d.textlength(text, font=f) + padx * 2
    d.rounded_rectangle([x, y, x + w, y + h], r, outline=P["ink"] + (170,), width=3)
    d.text((x + padx, y + h / 2), text, font=f, fill=P["ink"], anchor="lm")
    return w

def tile(d, x, base, digit, cnfont, scale):
    bb = cnfont.getbbox("项", anchor="ls")
    top, bot = base + bb[1] - 10 * scale, base + bb[3] + 8 * scale
    hgt = bot - top
    fd = FS(int(hgt * 0.70 / 0.72))
    db = fd.getbbox(digit, anchor="ls")
    cap = db[3] - db[1]
    w = d.textlength(digit, font=fd) + 60 * scale
    d.rounded_rectangle([x, top, x + w, bot], 20 * scale, fill=P["tile"])
    d.text((x + 30 * scale, top + (hgt - cap) / 2 - db[1]), digit, font=fd, fill=P["tile_fg"], anchor="ls")
    return w

def note(d, W, scale):
    f = FP(max(20, int(26 * scale)), "regular")
    txt = COPY["note"]
    w = d.textlength(txt, font=f) + 40 * scale
    x, y = W - w - 56 * scale, 56 * scale
    d.rounded_rectangle([x, y, x + w, y + 50 * scale], 25 * scale, outline=P["note"] + (150,), width=2)
    d.text((x + 20 * scale, y + 25 * scale), txt, font=f, fill=P["note"], anchor="lm")

def build(ratio="16x9"):
    L = LAYOUT[ratio]
    W, H, m = L["W"], L["H"], L["m"]
    scale = W / 1920
    img = halo(background(W, H), W, H, *L["halo"])
    img = character(img, W, H, *L["char"])
    d = ImageDraw.Draw(img)

    bw = chip(d, m, L["y_chip"], COPY["badge"], L["chip"][0], L["chip"][2])
    outline_chip(d, m + bw + 18 * scale, L["y_chip"], COPY["day"], L["chip"][1], L["chip"][2])
    note(d, W, scale)

    S = L["head"]
    HF = FK(S)
    L1 = L["y_l1"]
    L2 = L1 + S * 1.30
    d.text((m, L1), COPY["line1"], font=HF, fill=P["ink"], anchor="ls")
    d.text((m, L2), COPY["line2"], font=HF, fill=P["ink"], anchor="ls")
    x = m + d.textlength(COPY["line2"], font=HF) + 24 * scale
    tw = tile(d, x, L2, COPY["tile"], HF, scale)
    d.text((x + tw + 24 * scale, L2), COPY["after"], font=HF, fill=P["ink"], anchor="ls")

    d.text((m + 8 * scale, L["y_sub"]), COPY["sub"], font=FP(L["sub"], "semibold"), fill=P["sub"])
    return img.convert("RGB")

if __name__ == "__main__":
    if "--out" in sys.argv:
        path = sys.argv[sys.argv.index("--out") + 1]
        r = sys.argv[sys.argv.index("--ratio") + 1] if "--ratio" in sys.argv else "16x9"
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        build(r).save(path)
        print(path)
    else:
        os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
        ratios = [sys.argv[sys.argv.index("--ratio") + 1]] if "--ratio" in sys.argv else ["16x9", "4x3"]
        for r in ratios:
            p = os.path.join(ROOT, "out", f"cover-{r}.png")
            build(r).save(p)
            print(p)
