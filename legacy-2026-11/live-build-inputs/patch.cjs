const fs = require("fs"), path = require("path");
const dir = path.join(__dirname, "src");
let s = fs.readFileSync(path.join(dir, "index.orig.html"), "utf8").replace(/\r\n/g, "\n");
const spec = JSON.parse(fs.readFileSync(path.join(__dirname, "spec.json"), "utf8"));
for (const { old, new: nw } of spec) {
  const n = s.split(old).length - 1;
  if (n !== 1) throw new Error("patch target not unique/found (" + n + "): " + old.slice(0, 60));
  s = s.replace(old, () => nw);
}
fs.writeFileSync(path.join(dir, "index.html"), s);
fs.unlinkSync(path.join(dir, "index.orig.html"));
console.log("patched", s.length);
