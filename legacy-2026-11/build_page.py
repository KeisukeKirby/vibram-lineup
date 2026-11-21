"""Inline data.json into template.html.

index.html      -> Artifact-style fragment
site/index.html -> standalone page for Vercel (own skeleton, noindex) + site/img
"""
import json, shutil
from pathlib import Path

root = Path(__file__).parent
data = json.load(open(root / "data.json", encoding="utf-8"))
tpl = (root / "template.html").read_text(encoding="utf-8")
esc = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", r"<\/")
page = tpl.replace("/*DATA*/", esc(data["models"])).replace("/*ASOF*/", esc(data["asOf"]))
(root / "index.html").write_text(page, encoding="utf-8")

site = root / "site"
site.mkdir(exist_ok=True)
head = ('<!doctype html>\n<html lang="ja">\n<head>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="robots" content="noindex">\n'
        '<style>html{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n')
split = page.index("</style>") + len("</style>")
(site / "index.html").write_text(head + page[:split] + "\n</head>\n<body>\n" + page[split:] + "\n</body>\n</html>\n", encoding="utf-8")
# only ship images that the page uses
used = {Path(c).name for m in data["models"] for cw in m["cw"] for c in cw["imgs"]}
(site / "img").mkdir(exist_ok=True)
for f in (site / "img").iterdir():
    if f.name not in used:
        f.unlink()
for n in used:
    shutil.copy2(root / "img" / n, site / "img" / n)
print("built:", len(used), "images")
