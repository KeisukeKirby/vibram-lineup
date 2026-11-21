// Runs after patch3.cjs: unify card photos to the Drive pair shots and drop Performa Jane Evo.
const fs = require("fs"), path = require("path");
const BASE = "https://raw.githubusercontent.com/KeisukeKirby/vibram-lineup/49837e60c1c70093bc266bd774ecb7a16da7de57/pairs/";
const PAIRS = ["breezandal_black_MW", "breezandal_ivorygreen_MW", "breezandal_mustardblack_M", "cvthemp_black_MW", "cvthemp_khaki_MW", "cvtleather_brown_M", "elxknit_gray_M", "graspifier_black_M", "graspifier_ivoryfuchsia_W", "groundsplay_black_M", "groundsplayls_blacklime_M", "groundsplayls_ivorydeeplake_MW", "groundsplayls_totalblack_MW", "kso_blackblack_M", "ksoeco_beige_W", "ksoeco_gray_MW", "ksoevo_black_MW", "ksoevo_deeplakeblack_MW", "ksoevo_figagreen_MW", "ksoevo_yellowwhite_MW", "scramkey_black_U", "scramkey_deeplakeblack_U", "spidrwalk_brownblack_M", "spidrwalk_fuchsia_W", "spidrwalk_limegreen_M", "spidrwalk_totalblack_MW", "trailope_black_M", "trailope_deeplake_M", "trailopewp_brownblack_M", "valpha_black_MW", "valpha_deeplake_MW", "valpha_limegreenblack_M", "vaqua_black_MW", "vrun_blackblue_M", "vrun_blackfig_W", "vrun_blacklimeblack_M", "vrun_blackyellow_M", "vrun_brownivoryblack_M", "vrun_dustypink_W", "vrun_figivoryagreen_M", "vrun_goldenyellowblack_M", "vrun_ivoryyellow_M", "vrun_totalblack_M", "vrun_totalivory_MW", "vsoul_babyblue_W", "vsoul_black_W", "vsoul_brown_W", "vsoul_figagreen_W", "vsoul_fuchsia_W", "vsoul_ivorydustypink_W", "vsoul_limegreen_W", "vsoul_nude_W", "vsoul_purple_W", "vsoul_silver_W", "vtrain20_blackblack_MW", "vtrain20_limegreengray_M", "vtrek_blackblack_MW"];
const f = path.join(__dirname, "src", "index.html");
let s = fs.readFileSync(f, "utf8");
const a = s.indexOf("const DATA = [");
const b = s.indexOf("];\nconst ASOF", a);
if (a < 0 || b < 0) throw new Error("DATA not found");
let D = JSON.parse(s.slice(a + 13, b + 1));
D = D.filter(m => m.name !== "Performa Jane Evo");
const k = x => x.toLowerCase().replace(/[^a-z0-9]/g, "");
const want = [];
for (const m of D) for (const c of m.cw) {
  const key = `${k(m.name)}_${k(c.colour)}_${c.g}`;
  if (!PAIRS.includes(key)) continue;
  c.imgs = [`img/pair_${key}.jpg`];
  c.img_src = "drive";
  delete c.ref;
  want.push(key);
}
if (want.length !== PAIRS.length) throw new Error(`matched ${want.length} of ${PAIRS.length}: ` + PAIRS.filter(p => !want.includes(p)).join(","));
s = s.slice(0, a + 13) + JSON.stringify(D).replace(/<\//g, "<\\/") + s.slice(b + 1);
fs.writeFileSync(f, s);
(async () => {
  fs.mkdirSync(path.join(__dirname, "src", "img"), { recursive: true });
  for (const key of want) {
    const r = await fetch(BASE + key + ".jpg");
    if (!r.ok) throw new Error(`download ${key}: ${r.status}`);
    fs.writeFileSync(path.join(__dirname, "src", "img", `pair_${key}.jpg`), Buffer.from(await r.arrayBuffer()));
  }
  console.log(`patch4: ${want.length} pair photos, Jane Evo removed`);
})().catch(e => { console.error(e); process.exit(1); });
