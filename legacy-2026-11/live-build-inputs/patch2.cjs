const fs = require("fs"), path = require("path");
const f = path.join(__dirname, "src", "index.html");
let s = fs.readFileSync(f, "utf8");
const OV = {
  "img/ksoevo_deeplakeblack_M_0.jpg": "img/ksoevo_deeplakeblack_W_1.jpg",
  "img/ksoevo_deeplakeblack_W_0.jpg": "img/ksoevo_deeplakeblack_W_1.jpg",
  "img/vtrain20_limegreengray_M_0.jpg": "img/vtrain20_limegreengray_M_new.png"
};
let n = 0;
s = s.replace(/"imgs":\[("[^"]*")(?:,"[^"]*")*\]/g, (m, first) => {
  n++;
  const p = first.slice(1, -1);
  return '"imgs":["' + (OV[p] || p) + '"]';
});
fs.writeFileSync(f, s);
console.log("imgs arrays rewritten", n);
(async () => {
  const r = await fetch("https://makeshop-multi-images.akamaized.net/Barefootinc/shopimages/45/03/1_000000000345.png");
  if (!r.ok) throw new Error("image fetch failed " + r.status);
  fs.writeFileSync(path.join(__dirname, "src", "img", "vtrain20_limegreengray_M_new.png"), Buffer.from(await r.arrayBuffer()));
  console.log("new png saved");
})().catch(e => { console.error(e); process.exit(1); });
