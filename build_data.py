"""Build data.json, copy_src.json and resized images for the Vibram FiveFingers lineup page.

Carried colours  = stock table (VFF Stock Dashboard, sources/stock_items.json)
Event colours    = colours that only appear in the Sep 2026 event stock workbooks
Prices (THB)     = list price column of the event workbooks (same price as the promotion poster)
Copy / images    = vibram.com (EN), barefootinc.jp (JA), promotion poster crops for models
                   that neither site lists any more
"""
import collections, io, json, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import openpyxl
from PIL import Image

ROOT = Path(__file__).parent
SRC = ROOT / "sources"
DL = Path(r"C:/Users/Barefootinc TH/Downloads")
EVENT_FILES = [DL / "イベント/EVENT_SeP2026.xlsx", DL / "rev.EVENT_T21_Rama3.stock_Nov_2026.xlsx"]
EVENT_SHEETS = ("VFF", "Not all sizes&Slow seller", "2023-2024")

stock = json.load(open(SRC / "stock_items.json", encoding="utf-8"))
vib = json.load(open(SRC / "vibram_com.json", encoding="utf-8"))
jp = json.load(open(SRC / "barefootinc_jp.json", encoding="utf-8"))


def key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().replace("grey", "gray"))


def mkey(s):
    return re.sub(r"[^A-Z0-9]", "", re.sub(r"\d\d[MWU]\d{4}", "", s or "").upper())


def nice_colour(s):
    s = re.sub(r"\s*/\s*", "/", (s or "").strip())
    s = s.replace("A. Green", "A.Green").replace("A Green", "A.Green")
    if s.isupper() or s.islower():
        s = re.sub(r"[A-Za-z]+", lambda w: w.group(0).capitalize(), s.lower())
    return s


MODEL_ALIAS = {"VFF V-Soul 26": "V-Soul", "VFF KMD Evo": "KMD EVO", "Vibram Furoshiki Eco F": "Furoshiki EcoFree"}


def model_name(raw):
    raw = raw.strip()
    if raw in MODEL_ALIAS:
        return MODEL_ALIAS[raw]
    return re.sub(r"^VFF\s+", "", raw)


# ---------------- stock table: carried colours ----------------
carried = {}   # (model, ckey, g) -> {"colour", "code", "qty"}
for it in stock["items"]:
    m = model_name(it["model"])
    g = it["size"][0]
    c = carried.setdefault((m, key(it["color"]), g), {"colour": nice_colour(it["color"]), "code": it["code"], "qty": 0})
    c["qty"] += it["qty"] or 0

# ---------------- event workbooks: event colours and prices ----------------
event = {}                       # (model, ckey, g) -> {"colour","code"}
prices = collections.defaultdict(collections.Counter)
for f in EVENT_FILES:
    wb = openpyxl.load_workbook(f, data_only=True, read_only=True)
    for sh in EVENT_SHEETS:
        if sh not in wb.sheetnames:
            continue
        for r in wb[sh].iter_rows(values_only=True):
            code = next((c for c in r if isinstance(c, str) and re.match(r"VFF\d{4}\(", c)), None)
            name = next((c for c in r if isinstance(c, str) and c is not code and re.search(r"\([MWU]\d+,", c)), None)
            if not code or not name:
                continue
            m = re.match(r"(.+?)\(([MWU])\d+,\s*(.+)\)\s*$", name)
            if not m:
                continue
            model, g, colour = model_name(m.group(1)), m.group(2), m.group(3)
            price = next((c for c in r if isinstance(c, (int, float)) and 3000 <= c <= 12000), None)
            if price:
                prices[model][int(price)] += 1
            event.setdefault((model, key(colour), g), {"colour": nice_colour(colour), "code": code})

price_of = {m: c.most_common(1)[0][0] for m, c in prices.items()}
json.dump(price_of, open(SRC / "prices.json", "w", encoding="utf-8"), indent=1)

# ---------------- model list ----------------
CAT = {
    "V-Run": "running", "EL-X Knit": "running",
    "V-Train 2.0": "training", "V-Soul": "training", "KSO EVO": "training", "KMD EVO": "training",
    "Graspifier": "training", "Groundsplay": "training", "Groundsplay LS": "training",
    "V-Alpha": "outdoor", "V-Trek": "outdoor", "Trailope": "outdoor", "Trailope WP": "outdoor",
    "Scramkey": "outdoor", "Spidrwalk": "outdoor", "Breezandal": "outdoor", "V-Aqua": "outdoor", "KSO": "outdoor",
    "CVT-Hemp": "casual", "CVT-Leather": "casual", "KSO ECO": "casual", "Furoshiki EcoFree": "casual",
}
ORDER = list(CAT)

all_keys = {}  # (model, ckey, g) -> info (+ status)
for k, v in carried.items():
    if v["qty"] > 0:
        all_keys[k] = dict(v, status="regular")
for k, v in event.items():
    if k not in all_keys:
        all_keys[k] = dict(v, status="event")
dropped = [(k, v) for k, v in carried.items() if v["qty"] <= 0 and k not in all_keys]  # in stock list, zero stock, not at the event

models_seen = {k[0] for k in all_keys} | {k[0] for k, _ in dropped}
unknown = models_seen - set(CAT)
assert not unknown, f"models without a category: {unknown}"
missing_price = {m for m in models_seen if m not in price_of}
assert not missing_price, f"no price for {missing_price}"

# ---------------- official colour range (vibram.com current listing) ----------------
VIB_NAMES = {"V-Run": ["V-Run"], "V-Soul": ["V-Soul"], "KSO EVO": ["KSO EVO"], "Graspifier": ["Graspifier"],
             "Breezandal": ["Breezandal"], "V-Alpha": ["V-Alpha"], "Trailope": ["Trailope"], "Trailope WP": ["Trailope WP"],
             "Scramkey": ["Scramkey"], "Spidrwalk": ["Spidrwalk"], "Groundsplay": ["Groundsplay"],
             "Groundsplay LS": ["Groundsplay LS"], "KSO": ["KSO"], "KMD EVO": ["KMD EVO"],
             "Furoshiki EcoFree": ["Men's Furoshiki EcoFree", "Women's Furoshiki EcoFree"]}
vib_by_model = collections.defaultdict(list)
for p in vib:
    for m, names in VIB_NAMES.items():
        if p["name"] in names:
            g = "W" if p["name"].startswith("Women") else "M" if p["name"].startswith("Men") else p["sku"][0]
            vib_by_model[m].append(dict(p, g=g))

# ---------------- images ----------------
JP_MODEL = collections.defaultdict(list)
for o in jp:
    JP_MODEL[mkey(o["title"])].append(o)
POSTER = {("CVT-Hemp", "black"): "poster_cvt-hemp_black", ("CVT-Hemp", "khaki"): "poster_cvt-hemp_khaki",
          ("KSO ECO", "gray"): "poster_kso-eco_gray", ("KSO ECO", "beige"): "poster_kso-eco_beige",
          ("EL-X Knit", "gray"): "poster_el-x-knit_gray", ("V-Aqua", "black"): "poster_v-aqua_black",
          ("CVT-Leather", "brown"): "poster_cvt-leather_brown"}
jobs = []


def stem(model, ck, g):
    return f"{key(model)}_{ck}_{g}"


def find_images(model, ck, g):
    """-> (list of (kind, url_or_file)), source label"""
    for p in vib_by_model.get(model, []):
        if key(p["color"]) == ck and (p["g"] == g or p["g"] == "U" or g == "U"):
            return [("url", u + "?sw=720&sh=720") for u in p["images"][:4]], "vibram.com"
    for o in JP_MODEL.get(mkey(model), []):
        if key(o["color"]) == ck and o["code"][2] in (g, "U") and o["images"]:
            return [("url", o["images"][0])], "barefootinc.jp"
    f = POSTER.get((model, ck))
    if f:
        return [("file", f"img/{f}.jpg")], "poster"
    return [], None


# ---------------- assemble ----------------
models = collections.OrderedDict()
for m in ORDER:
    if m not in models_seen:
        continue
    models[m] = {"name": m, "cat": CAT[m], "price": price_of[m], "cw": [], "range": []}

for (m, ck, g), info in sorted(all_keys.items(), key=lambda kv: (ORDER.index(kv[0][0]), kv[0][2], kv[1]["status"] != "regular", kv[1]["colour"])):
    imgs, srcname = find_images(m, ck, g)
    models[m]["cw"].append({"colour": info["colour"], "g": g, "regular": info["status"] == "regular", "ck": ck,
                            "code": re.match(r"(VFF\d{4})\(([^,]+),", info["code"]).group(1) + " · " + re.match(r"(VFF\d{4})\(([^,]+),", info["code"]).group(2),
                            "imgs": imgs, "img_src": srcname})

# fallback: same colour in the other gender, then the model's first picture
for M in models.values():
    pool = [c for c in M["cw"] if c["imgs"]]
    for c in M["cw"]:
        if c["imgs"]:
            continue
        alt = next((p for p in pool if p["ck"] == c["ck"]), None)
        if alt:
            c["imgs"], c["img_src"], c["ref"] = alt["imgs"][:1], alt["img_src"], "gender"
        elif pool:
            c["imgs"], c["img_src"], c["ref"] = pool[0]["imgs"][:1], pool[0]["img_src"], "model"

# official range
for m, M in models.items():
    rng = collections.OrderedDict()
    for p in vib_by_model.get(m, []):
        e = rng.setdefault(key(p["color"]), {"name": nice_colour(p["color"])})
        gs = ["W", "M"] if p["g"] == "U" else [p["g"]]
        for g in gs:
            e[g] = ""
    for c in M["cw"]:
        e = rng.setdefault(c["ck"], {"name": c["colour"]})
        e[c["g"] if c["g"] != "U" else "M"] = "regular" if c["regular"] else "event"
        if c["g"] == "U":
            e["W"] = "regular" if c["regular"] else "event"
    M["range"] = list(rng.values())
    M["listed"] = m in vib_by_model

# ---------------- source copy for the translators ----------------
def jp_pick(m):
    cands = JP_MODEL.get(mkey(m), [])
    return max(cands, key=lambda o: o["code"][:2]) if cands else None


copy_src = []
for m, M in models.items():
    o = jp_pick(m)
    vs = vib_by_model.get(m, [])
    en = vs[0]["desc"] if vs else ""
    M["jp_url"] = f"https://www.barefootinc.jp/view/item/{o['id']}" if o else ""
    M["vib_url"] = vs[0]["url"] if vs else ""
    copy_src.append({"model": m, "ja": ({"overview": o["overview"], "sole": o["sole"], "spec": o["spec"]} if o else None), "en": en or None})
json.dump(copy_src, open(SRC / "copy_src.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------------- download images ----------------
def fetch(job):
    url, out = job
    if out.exists():
        return
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=60).read()
    im = Image.open(io.BytesIO(data))
    if im.mode in ("RGBA", "P", "LA"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[-1]); im = bg
    im = im.convert("RGB"); im.thumbnail((720, 720))
    im.save(out, "JPEG", quality=80, optimize=True, progressive=True)


for M in models.values():
    for c in M["cw"]:
        files = []
        for i, (kind, ref) in enumerate(c["imgs"]):
            if kind == "file":
                files.append(ref)
            else:
                fn = f"img/{stem(M['name'], c['ck'], c['g'])}_{i}.jpg"
                files.append(fn); jobs.append((ref, ROOT / fn))
        c["imgs"] = files
with ThreadPoolExecutor(10) as ex:
    list(ex.map(fetch, jobs))

# ---------------- translated copy (written by the translation step) ----------------
i18n = {}
for f in sorted(SRC.glob("copy_i18n_*.json")):
    i18n.update(json.load(open(f, encoding="utf-8")))
# Where vibram.com and barefootinc.jp disagree, the checked value is kept here (see README notes).
overrides = json.load(open(SRC / "spec_overrides.json", encoding="utf-8"))
for name, sp in overrides.items():
    i18n.setdefault(name, {}).setdefault("specs", {}).update(sp)
for M in models.values():
    M["i18n"] = i18n.get(M["name"], {})
    for c in M["cw"]:
        c.pop("ck", None)

out = list(models.values())
json.dump({"asOf": stock["asOf"], "models": out}, open(ROOT / "data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n_reg = sum(c["regular"] for M in out for c in M["cw"]); n_all = sum(len(M["cw"]) for M in out)
print(len(out), "models,", n_all, "colourways,", n_reg, "regular,", n_all - n_reg, "event,", len(jobs), "downloads")
print("zero-stock, not at event (dropped):", [(k[0], k[2], v["colour"]) for k, v in dropped])
for M in out:
    for c in M["cw"]:
        if not c["imgs"]:
            print("NO IMAGE", M["name"], c["g"], c["colour"])
        elif c.get("ref"):
            print("REF IMAGE", c["ref"], M["name"], c["g"], c["colour"])
    if not M["i18n"]:
        print("no translated copy yet:", M["name"])
