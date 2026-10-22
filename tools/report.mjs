// Decodes every demo step from its Studio leader receipt: SUCCESS with the
// returned value, or ERROR with the [EXPECTED]/[REFUSED] code. node ops/report.mjs
import fs from "fs";
import { createRequire } from "module";
const require = createRequire("C:/Users/User/AppData/Roaming/npm/node_modules/genlayer/package.json");
const gl = require("genlayer-js");
const { studionet } = require("genlayer-js/chains");
const c = gl.createClient({ chain: studionet });
const st = JSON.parse(fs.readFileSync(process.argv[2] || "ops/state-studio.json", "utf8"));

const rows = [];
for (const [key, val] of Object.entries(st)) {
  const hash = String(val).split(" ")[0];
  if (!/^0x[0-9a-f]{64}$/i.test(hash)) continue;
  let r;
  for (let i = 0; i < 5; i++) { try { r = await c.getTransaction({ hash }); break; } catch { await new Promise(s => setTimeout(s, 4000)); } }
  const lr = r?.consensus_data?.leader_receipt, L = Array.isArray(lr) ? lr[0] : lr;
  const p = L?.result?.payload;
  const readable = typeof p === "string" ? p : (p?.readable ?? "");
  const votes = Object.values(r?.consensus_data?.votes || {});
  rows.push({ step: key, tx: hash, status: r?.statusName, consensus: r?.result_name, exec: L?.execution_result,
              out: String(readable).slice(0, 140), agree: votes.filter(v => v === "agree").length + "/" + votes.length });
}
for (const x of rows) console.log(`${x.step.padEnd(20)} ${String(x.exec).padEnd(8)} ${String(x.consensus).padEnd(15)} ${x.agree.padEnd(4)} ${x.out}`);
fs.writeFileSync("ops/report-studio.json", JSON.stringify(rows, null, 1));
