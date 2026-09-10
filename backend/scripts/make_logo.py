"""Generate the original "Usman Public School" crest artwork (Pillow).

Produces ``src/student_management/static/branding/logo.png`` (1024x1024,
transparent background). Run from the backend directory:

    python -m scripts.make_logo

The crest is original artwork (not derived from any real institution's logo):
a green shield with gold border, crescent-star, rising flame over an open
book, and the school name on a ribbon banner.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    from PIL import ImageDraw as _  # noqa: F401  (import guard handles PIL)
except ImportError:
    sys.exit("Pillow is required; run: pip install Pillow")

SIZE = 1024

GREEN = (11, 107, 79)
GREEN_DARK = (7, 82, 60)
GOLD = (217, 164, 65)
GOLD_DARK = (177, 126, 39)
CREAM = (248, 240, 226)
INK = (42, 38, 30)

OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "student_management" / "static" / "branding"

FONT_CANDIDATES = [
    "C:/Windows/Fonts/georgia.ttf",
    "C:/Windows/Fonts/constantb.ttf",
    "C:/Windows/Fonts/timesbd.ttf",
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).is_file():
            if "DejaVu" in path:
                size = int(size * 0.94)
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _star(cx: float, cy: float, outer: float, inner: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(10):
        r = outer if i % 2 == 0 else inner
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _shield_outline(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle([312, 196, 712, 648], radius=62, fill=GOLD)
    draw.polygon([(312, 430), (712, 430), (644, 688), (512, 872), (380, 688)], fill=GOLD)

    draw.rounded_rectangle([340, 222, 684, 638], radius=48, fill=GREEN)
    draw.polygon([(340, 480), (684, 480), (616, 690), (512, 846), (408, 690)], fill=GREEN)


def _crest_top(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon(_star(512, 262, 30, 12), fill=GOLD)
    draw.ellipse((452, 268, 572, 388), fill=GOLD)
    draw.ellipse((478, 300, 598, 420), fill=GREEN)


def _flame(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((432, 428, 592, 532), fill=GOLD_DARK)
    draw.polygon([(512, 400), (470, 458), (512, 500), (554, 458)], fill=GOLD)
    draw.polygon([(512, 426), (488, 458), (512, 478), (536, 458)], fill=CREAM)


def _book(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((452, 588, 572, 652), fill=GREEN_DARK)
    draw.polygon(
        [(512, 530), (408, 552), (438, 622), (512, 608)], fill=CREAM, outline=GOLD, width=3
    )
    draw.polygon(
        [(512, 530), (616, 552), (586, 622), (512, 608)], fill=CREAM, outline=GOLD, width=3
    )
    draw.line((512, 532, 512, 610), fill=GOLD, width=5)


def _star_mid(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon(_star(512, 720, 26, 11), fill=GOLD)


def _banner(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon(
        [(512, 846), (470, 826), (366, 812), (366, 838), (470, 850), (512, 870), (554, 850), (658, 838), (658, 812), (554, 826)],
        fill=GOLD_DARK,
    )
    draw.rounded_rectangle((252, 858, 772, 952), radius=24, fill=GOLD)
    draw.rounded_rectangle((252, 858, 772, 952), radius=24, outline=GOLD_DARK, width=3)

    font = _load_font(44)
    text = "USMAN PUBLIC SCHOOL"
    width = max(1, draw.textlength(text, font=font))
    x = 512 - width / 2
    draw.text((x, 890), text, font=font, fill=GREEN_DARK)


def main() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    _shield_outline(draw)
    _crest_top(draw)
    _flame(draw)
    _book(draw)
    _star_mid(draw)
    _banner(draw)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "logo.png"
    img.save(out)
    print(f"Wrote {out} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()