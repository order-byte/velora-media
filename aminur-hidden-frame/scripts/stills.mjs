// Render review stills: node scripts/stills.mjs <outDir> <frame> [frame...]
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";
import fs from "node:fs";

const [outDir, ...frames] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const browserExecutable = process.env.REMOTION_BROWSER || null;
const composition = await selectComposition({ serveUrl, id: "Reel", browserExecutable });
for (const f of frames.map(Number)) {
  const output = path.join(outDir, `f${String(f).padStart(4, "0")}.jpg`);
  await renderStill({ composition, serveUrl, frame: f, output, imageFormat: "jpeg", jpegQuality: 85, browserExecutable });
  console.log("rendered", output);
}
