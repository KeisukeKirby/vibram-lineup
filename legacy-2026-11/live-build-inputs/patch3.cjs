const fs = require("fs"), path = require("path");
const f = path.join(__dirname, "src", "index.html");
let s = fs.readFileSync(f, "utf8");
const a = s.indexOf("const DATA = [");
const b = s.indexOf("];\nconst ASOF", a);
if (a < 0 || b < 0) throw new Error("DATA not found");
const D = JSON.parse(s.slice(a + 13, b + 1));
const UP = {
  "TieraLite": {"Red Clay":"tieraredclay","Total Black":"tieratotalblack","Triple/Brown":"tieratriplebrown","Ivory/Black":"tieraivoryblack"},
  "Vi-B X": {"Charcoal/Black":"vibxcharcoalblack","Basil":"vibxbasil","Ivory/Grey":"vibxivorygrey","Basil/Honey":"vibxssbasilhoney","Ivory/Honey":"vibxssivoryhoney"},
  "Trailope 2": {"Black":"trailope2black","Brown/Black":"trailope2brownblack","Basil/Black":"trailope2basilblack","Lunar Grey/Black":"trailope2lunargreyblack"},
  "LiteBeat WP": {"Total Black":"litebeattotalblack","Brown/Black":"litebeatbrownblack"}
};
let merged = 0;
for (const m of D) {
  const out = [], seen = new Map();
  for (const c of m.cw) {
    const k = c.colour;
    const prev = seen.get(k);
    if (prev && ((prev.g === "M" && c.g === "W") || (prev.g === "W" && c.g === "M"))) {
      const M = prev.g === "M" ? prev : c, W = prev.g === "M" ? c : prev;
      prev.g = "MW";
      prev.regular = !!(M.regular || W.regular);
      if (M.up || W.up) prev.up = true;
      if (!prev.imgs.length) prev.imgs = (W.imgs || []).slice();
      if (M.code !== W.code && W.code) {
        const [mn, ...mr] = M.code.split(" · "), [wn, ...wr] = W.code.split(" · ");
        prev.code = mr.join(" · ") === wr.join(" · ") ? mn + "/" + wn + (mr.length ? " · " + mr.join(" · ") : "") : M.code + " / " + W.code;
      }
      merged++;
    } else { seen.set(k, c); out.push(c); }
  }
  m.cw = out;
  if (m.name === "Vi-B X") { const x = out.find(c => c.colour === "Basil/Honey"); if (x) x.g = "MW"; }
  const map = UP[m.name];
  if (map) for (const c of m.cw) if (map[c.colour]) { c.imgs = ["img/up_" + map[c.colour] + ".webp"]; c.ref = ""; delete c.ref; c.img_src = "VFF CATALOGUE"; }
}
s = s.slice(0, a) + "const DATA = " + JSON.stringify(D) + s.slice(b + 1);
s = s.replace(/g:\{W:"([^"]*)",M:"([^"]*)",U:/g, 'g:{W:"$1",M:"$2",MW:"MW",U:');
fs.writeFileSync(f, s);
console.log("merged colourways", merged);
