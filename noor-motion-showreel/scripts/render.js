#!/usr/bin/env node
/* Render scene/index.html to numbered PNG frames with headless Chromium.
 *
 * usage:
 *   node scripts/render.js --clips <clips dir> --out <frames dir> [--fps 60] [--workers 4]
 *   node scripts/render.js --clips <clips dir> --out <dir> --times 0.5,2.2,9.6   (stills for review)
 *
 * The scene is a pure function of time, so frames can be split across
 * workers in any order; each worker takes one contiguous chunk.
 */
const path = require("path");
const fs = require("fs");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

function args() {
  const a = process.argv.slice(2), o = {};
  for (let i = 0; i < a.length; i += 2) o[a[i].replace(/^--/, "")] = a[i + 1];
  return o;
}

async function worker(id, jobs, opt) {
  const browser = await chromium.launch({ args: ["--force-color-profile=srgb", "--disable-lcd-text", "--font-render-hinting=none"] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on("pageerror", (e) => console.error(`[w${id}] page error:`, e.message));
  const url = pathToFileURL(path.join(__dirname, "..", "scene", "index.html")).href + "?clips=" + encodeURIComponent(pathToFileURL(opt.clips).href);
  await page.goto(url);
  let done = 0;
  for (const job of jobs) {
    await page.evaluate((t) => window.__render(t), job.t);
    await page.screenshot({ path: job.file, type: "png", animations: "disabled", caret: "initial" });
    done++;
    if (done % 50 === 0) console.log(`[w${id}] ${done}/${jobs.length}`);
  }
  await browser.close();
}

(async () => {
  const opt = args();
  if (!opt.out || !opt.clips) { console.error("need --out and --clips"); process.exit(1); }
  fs.mkdirSync(opt.out, { recursive: true });
  const fps = +(opt.fps || 60);
  const workers = +(opt.workers || 4);
  let jobs;
  if (opt.times) {
    jobs = opt.times.split(",").map((s) => ({ t: +s, file: path.join(opt.out, `t_${(+s).toFixed(2).padStart(5, "0")}.png`) }));
  } else {
    const duration = +(opt.duration || 25.05);
    const n = Math.round(duration * fps);
    const from = +(opt.from || 0), to = Math.min(n, +(opt.to || n));
    jobs = [];
    for (let f = from; f < to; f++) jobs.push({ t: f / fps, file: path.join(opt.out, `f_${String(f).padStart(5, "0")}.png`) });
    if (opt.skipExisting) jobs = jobs.filter((j) => !fs.existsSync(j.file));
  }
  const w = Math.max(1, Math.min(workers, jobs.length));
  const per = Math.ceil(jobs.length / w);
  const t0 = Date.now();
  await Promise.all(Array.from({ length: w }, (_, i) => worker(i, jobs.slice(i * per, (i + 1) * per), opt)));
  console.log(`rendered ${jobs.length} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
})();
