"""Cut the old-model shoe photos out of the promotion poster (user-supplied) onto a white square.

Used only for models that are not on vibram.com or barefootinc.jp any more.
"""
import sys
from pathlib import Path
from PIL import Image, ImageFilter

POSTER = Path(sys.argv[1])
OUT = Path(__file__).parent / "img"
CELLS = {  # file stem -> crop box in poster pixels (1413 x 2000)
    "poster_cvt-hemp_black": (835, 672, 952, 732),
    "poster_cvt-hemp_khaki": (955, 672, 1068, 732),
    "poster_kso-eco_gray": (1090, 448, 1250, 522),
    "poster_kso-eco_beige": (1170, 520, 1315, 584),
    "poster_el-x-knit_gray": (1095, 685, 1310, 790),
    "poster_v-aqua_black": (235, 1222, 366, 1305),
    "poster_cvt-leather_brown": (545, 1222, 672, 1305),
}
im = Image.open(POSTER).convert("RGB")
for stem, box in CELLS.items():
    c = im.crop(box)
    bg = c.getpixel((2, 2))
    diff = Image.new("L", c.size)
    px, dp = c.load(), diff.load()
    for y in range(c.height):
        for x in range(c.width):
            dp[x, y] = min(255, max(abs(px[x, y][i] - bg[i]) for i in range(3)) * 6)
    mask = diff.point(lambda v: 0 if v < 24 else min(255, v)).filter(ImageFilter.GaussianBlur(0.8))
    bbox = mask.point(lambda v: 255 if v > 60 else 0).getbbox()
    c, mask = c.crop(bbox), mask.crop(bbox)
    pad = int(max(c.size) * 0.12)
    s = 4
    c = c.resize((c.width * s, c.height * s), Image.LANCZOS)
    mask = mask.resize(c.size, Image.LANCZOS)
    side = max(c.size) + pad * s * 2
    canvas = Image.new("RGB", (side, side * 3 // 4 if side * 3 // 4 >= c.height + 2 * pad * s else c.height + 2 * pad * s), (255, 255, 255))
    canvas.paste(c, ((canvas.width - c.width) // 2, (canvas.height - c.height) // 2), mask)
    canvas.thumbnail((720, 720))
    canvas.save(OUT / f"{stem}.jpg", "JPEG", quality=88)
    print(stem, canvas.size)
