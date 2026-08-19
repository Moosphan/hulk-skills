import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1440
FONT_SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_HEI = "/System/Library/Fonts/PingFang.ttc"
FONT_ASSET_ROOT = "/System/Library/AssetsV2/com_apple_MobileAsset_Font7"
FONT_DIR = ROOT / "assets/fonts"

FONT_PRESETS = {
    "lxgw-wenkai": {"path": str(FONT_DIR / "LXGWWenKai-Regular.ttf"), "index": 0},
    "mashanzheng": {"path": str(FONT_DIR / "MaShanZheng-Regular.ttf"), "index": 0},
    "zcool-xiaowei": {"path": str(FONT_DIR / "ZCOOLXiaoWei-Regular.ttf"), "index": 0},
    "xingkai": {
        "path": f"{FONT_ASSET_ROOT}/aa99d0b2bad7f797f38b49d46cde28fd4b58876e.asset/AssetData/Xingkai.ttc",
        "index": 0,
    },
    "xingkai-light": {
        "path": f"{FONT_ASSET_ROOT}/aa99d0b2bad7f797f38b49d46cde28fd4b58876e.asset/AssetData/Xingkai.ttc",
        "index": 2,
    },
    "kaiti": {
        "path": f"{FONT_ASSET_ROOT}/54a2ad3dac6cac875ad675d7d273dc425010a877.asset/AssetData/Kaiti.ttc",
        "index": 0,
    },
    "kaiti-bold": {
        "path": f"{FONT_ASSET_ROOT}/54a2ad3dac6cac875ad675d7d273dc425010a877.asset/AssetData/Kaiti.ttc",
        "index": 3,
    },
    "hanzipen": {
        "path": f"{FONT_ASSET_ROOT}/9fdda46cbe802833590494a09b2787378340c597.asset/AssetData/Hanzipen.ttc",
        "index": 0,
    },
    "hannotate": {
        "path": f"{FONT_ASSET_ROOT}/8dc7805506cc9f233dcc19aabf593196842a47ae.asset/AssetData/Hannotate.ttc",
        "index": 0,
    },
    "libian": {
        "path": f"{FONT_ASSET_ROOT}/7278ac2566252649b05c5a2b07c7d45be59f47c5.asset/AssetData/Libian.ttc",
        "index": 0,
    },
    "baoli": {
        "path": f"{FONT_ASSET_ROOT}/9d5450ee93f17da1eacfa01b5e7b598f9e2dda2b.asset/AssetData/Baoli.ttc",
        "index": 0,
    },
    "fangsong": {
        "path": f"{FONT_ASSET_ROOT}/1821952872c81043711aab6910052b65da8edf2c.asset/AssetData/STFANGSO.ttf",
        "index": 0,
    },
    "lisong": {
        "path": f"{FONT_ASSET_ROOT}/5a3fc034b64879656271c040cab38b65d4ea6548.asset/AssetData/LiSongPro.ttf",
        "index": 0,
    },
    "simsong": {
        "path": f"{FONT_ASSET_ROOT}/857d6c90171c328a4892c1492291d34e401d7f25.asset/AssetData/SimSong.ttc",
        "index": 0,
    },
    "biaukai": {
        "path": f"{FONT_ASSET_ROOT}/584ea2a48d14147049c2f9eaee147fe5a1f279ac.asset/AssetData/BiauKai.ttc",
        "index": 1,
    },
    "wawati": {
        "path": f"{FONT_ASSET_ROOT}/18189590ed3a5f46cef20ed4d1cec2611dca13ff.asset/AssetData/WawaSC-Regular.otf",
        "index": 0,
    },
    "lingwai": {
        "path": f"{FONT_ASSET_ROOT}/e2c331b942cb338404a160a97a7cd6e8a31428e8.asset/AssetData/LingWaiSC-Medium.otf",
        "index": 0,
    },
    "yuanti": {
        "path": f"{FONT_ASSET_ROOT}/b86e58f38fd21e9782e70a104676f1655e72ebab.asset/AssetData/Yuanti.ttc",
        "index": 0,
    },
    "hiragino-mincho": {"path": "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc", "index": 0},
    "songti-light": {"path": FONT_SONG, "index": 3},
    "songti-regular": {"path": FONT_SONG, "index": 4},
    "songti-bold": {"path": FONT_SONG, "index": 1},
    "heiti": {"path": "/System/Library/Fonts/STHeiti Medium.ttc", "index": 1},
    "pingfang": {"path": FONT_HEI, "index": 5},
}

STYLES = {
    "ink-mountain": {"name": "水墨山居", "accent": (90, 83, 72)},
    "snow-lamp": {"name": "雪夜孤灯", "accent": (76, 84, 92)},
    "bamboo-tea": {"name": "竹影茶席", "accent": (78, 96, 76)},
    "moon-boat": {"name": "月下归舟", "accent": (72, 76, 88)},
    "plum-cold": {"name": "梅枝冷香", "accent": (110, 70, 74)},
    "paper-minimal": {"name": "宣纸极简", "accent": (86, 80, 72)},
    "old-book": {"name": "旧书页复古", "accent": (115, 82, 54)},
    "mist-river": {"name": "江南烟雨", "accent": (74, 92, 94)},
    "lotus-pond": {"name": "荷塘听雨", "accent": (72, 104, 86)},
    "pine-temple": {"name": "松风古寺", "accent": (78, 88, 74)},
    "desert-pass": {"name": "大漠关山", "accent": (128, 92, 58)},
    "palace-moon": {"name": "宫墙月影", "accent": (122, 70, 58)},
    "orchid-window": {"name": "兰亭雅集", "accent": (86, 91, 112)},
    "peach-spring": {"name": "桃花春水", "accent": (134, 82, 86)},
    "maple-bridge": {"name": "枫桥秋色", "accent": (128, 78, 45)},
}


def cover_resize(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    tw, th = size
    scale = max(tw / im.width, th / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def centered_text(draw: ImageDraw.ImageDraw, y: int, text: str, font, fill, spacing=18):
    lines = text.splitlines()
    boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_heights = [b[3] - b[1] for b in boxes]
    total_h = sum(line_heights) + spacing * (len(lines) - 1)
    cursor = y - total_h // 2
    for line, box, lh in zip(lines, boxes, line_heights):
        width = box[2] - box[0]
        draw.text(((W - width) / 2, cursor), line, font=font, fill=fill)
        cursor += lh + spacing


def blank(chars: int) -> str:
    chars = max(1, chars)
    return "　" * chars


def load_font(preset: str, size: int, path: str | None = None, index: int | None = None):
    if path:
        return ImageFont.truetype(path, size, index=index or 0)

    config = FONT_PRESETS.get(preset, FONT_PRESETS["songti-light"])
    if not Path(config["path"]).exists():
        config = FONT_PRESETS["songti-light"]
    return ImageFont.truetype(config["path"], size, index=config["index"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--style", choices=sorted(STYLES), default="ink-mountain")
    parser.add_argument("--background", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--blank-chars", type=int, default=1)
    parser.add_argument("--line1", default="半卷云{blank}暮雨，")
    parser.add_argument("--line2", default="一灯月{blank}归舟。")
    parser.add_argument("--line-spacing", type=int, default=72)
    parser.add_argument("--poem-font-size", type=int, default=None)
    parser.add_argument("--title-y", type=int, default=210)
    parser.add_argument("--rule-y", type=int, default=270)
    parser.add_argument("--poem-center-y", type=int, default=640)
    parser.add_argument("--heading", default="诗词填空")
    parser.add_argument("--label", default="画龙点睛挑战")
    available_fonts = sorted(k for k, v in FONT_PRESETS.items() if Path(v["path"]).exists())
    default_font = "zcool-xiaowei" if "zcool-xiaowei" in available_fonts else available_fonts[0]
    parser.add_argument("--font", choices=available_fonts, default=default_font)
    parser.add_argument("--font-path", default=None)
    parser.add_argument("--font-index", type=int, default=0)
    parser.add_argument("--show-footer", action="store_true")
    parser.add_argument("--footer", default="")
    args = parser.parse_args()

    style = STYLES[args.style]
    bg = args.background or ROOT / f"assets/generated/styles/bg-{args.style}.png"
    out_path = args.output or ROOT / f"assets/generated/styles/cover-{args.style}.png"

    base = cover_resize(Image.open(bg).convert("RGB"), (W, H)).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    draw.rectangle((0, 0, W, H), fill=(250, 248, 242, 34))

    title_font = load_font("pingfang", 34)
    poem_size = args.poem_font_size or (
        92 if args.blank_chars <= 1 else 84 if args.blank_chars == 2 else 76
    )
    poem_font = load_font(args.font, poem_size, args.font_path, args.font_index)
    foot_font = load_font("pingfang", 24)

    title = f"{args.heading} · {args.label}"
    gap = f"（{blank(args.blank_chars)}）"
    poem = args.line1.format(blank=gap) + "\n" + args.line2.format(blank=gap)
    accent = style["accent"]

    tw = draw.textbbox((0, 0), title, font=title_font)[2]
    draw.text(((W - tw) / 2, args.title_y), title, font=title_font, fill=(*accent, 172))
    draw.line((382, args.rule_y, 698, args.rule_y), fill=(*accent, 58), width=1)

    centered_text(
        draw,
        args.poem_center_y,
        poem,
        poem_font,
        fill=(22, 22, 20, 238),
        spacing=args.line_spacing,
    )

    if args.show_footer:
        footer = args.footer or "SHI CI     TIAN KONG     TIAO ZHAN"
        fw = draw.textbbox((0, 0), footer, font=foot_font)[2]
        draw.text(((W - fw) / 2, 1278), footer, font=foot_font, fill=(*accent, 150))

    out = Image.alpha_composite(base, overlay).convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path, quality=95)
    print(out_path)


if __name__ == "__main__":
    main()
