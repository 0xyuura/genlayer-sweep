import fs from "fs"; import crypto from "crypto";
import { createRequire } from "module";
const require = createRequire("C:/Users/User/AppData/Roaming/npm/node_modules/genlayer/package.json");
const gl = require("genlayer-js"); const { studionet } = require("genlayer-js/chains");
const c = gl.createClient({ chain: studionet });
const st = JSON.parse(fs.readFileSync(process.argv[2] || "ops/state-studio.json", "utf8"));
const sha = b => crypto.createHash("sha256").update(b).digest("hex").slice(0, 16);
for (const [name, file] of [["sweep", "sweep.py"], ["listing", "listing.py"], ["bounty", "bounty.py"]]) {
  const r = await c.getTransaction({ hash: st[name + "_deploy"].split(" ")[0] });
  const onchain = Buffer.from(r.data.contract_code, "base64"), local = fs.readFileSync("contracts/" + file);
  console.log(name.padEnd(9), st[name], "onchain", sha(onchain), "local", sha(local), onchain.equals(local) ? "IDENTICAL" : "DIFFERENT");
}
