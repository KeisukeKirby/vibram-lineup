"""Add the phone-layout CSS (tools/mobile_fix.css) on top of a lineup page that is already live.

The live pages are sometimes updated from other working copies, so this starts from what is
deployed right now (index.html + img/*), injects <style id="mobile-fix"> if it is not there yet,
and only then deploys. Nothing in the live content is changed apart from that style block.

  python tools/apply_mobile_fix.py <name> <base-url> <path-to-.vercel/project.json> [--deploy]
  e.g. python tools/apply_mobile_fix.py vibram https://vibram-lineup.vercel.app site/.vercel/project.json --deploy
"""
import hashlib, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

name, base, link = sys.argv[1], sys.argv[2].rstrip("/"), Path(sys.argv[3])
deploy = "--deploy" in sys.argv
css = (Path(__file__).parent / "mobile_fix.css").read_text(encoding="utf-8")
work = Path(tempfile.mkdtemp(prefix=f"mirror_{name}_")); (work / "img").mkdir()


def fetch_index():
    subprocess.run(["curl", "-s", "-H", "Cache-Control: no-cache", f"{base}/?mirror={os.getpid()}", "-o", str(work / "index.html")], check=True)
    return (work / "index.html").read_bytes()


raw = fetch_index()
html = raw.decode("utf-8")
if 'id="mobile-fix"' in html:
    print("already patched, nothing to do"); sys.exit(0)
paths = sorted(set(re.findall(r'img/[A-Za-z0-9_.\-]+\.(?:jpg|jpeg|png|webp|gif|svg)', html)))
def get(p):
    subprocess.run(["curl", "-s", "-f", f"{base}/{p}", "-o", str(work / p)])
    return (work / p).exists() and (work / p).stat().st_size > 0
with ThreadPoolExecutor(10) as ex:
    missing = [p for p, ok in zip(paths, ex.map(get, paths)) if not ok]
assert not missing, f"could not fetch {missing[:5]}"
patched = html.replace("</head>", '<style id="mobile-fix">\n' + css + "</style>\n</head>", 1)
assert patched != html
(work / "index.html").write_bytes(patched.encode("utf-8"))
(work / ".vercel").mkdir(); shutil.copy(link, work / ".vercel" / "project.json")
print(f"patched {len(paths)} images + index.html in {work}")
if deploy:
    if hashlib.sha1(fetch_index() if False else raw).hexdigest() != hashlib.sha1(subprocess.run(["curl", "-s", "-H", "Cache-Control: no-cache", f"{base}/?chk={os.getpid()}"], capture_output=True).stdout).hexdigest():
        sys.exit("live page changed while patching; run again")
    r = subprocess.run(["vercel", "deploy", "--prod", "--yes", "--scope", "barefootinc-th"], cwd=work, capture_output=True, text=True, shell=(os.name == "nt"))
    print((r.stdout + r.stderr)[-600:])
