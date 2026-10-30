// Deterministic frame renderer: loads index.html, calls window.__seek(t) for every
// frame, screenshots it and pipes the frames into ffmpeg. Work is split across
// several browser processes, each writing its own segment, then concatenated.
//
//   node render.mjs                         full video -> out/video.mp4
//   node render.mjs --from 4 --to 8         a slice (handy while iterating)
//   node render.mjs --stills 1.2,5,9.5      PNG stills -> out/stills/
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import os from 'node:os';

// require() so a globally installed playwright resolves too
const { chromium } = createRequire(import.meta.url)('playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(
  process.argv.slice(2).join(' ').split('--').filter(Boolean)
    .map(s => { const [k, ...v] = s.trim().split(/\s+/); return [k, v.join(' ') || true]; })
);

const W = 1920, H = 1080;
const fps = Number(args.fps ?? 60);
const outDir = path.join(here, 'out');
mkdirSync(outDir, { recursive: true });
const pageUrl = pathToFileURL(path.join(here, 'index.html')).href;

async function openPage() {
  const browser = await chromium.launch({ args: ['--force-color-profile=srgb', '--hide-scrollbars'] });
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('[page error]', e.message));
  await page.goto(pageUrl);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  const cdp = await page.context().newCDPSession(page);
  return { browser, page, cdp };
}

async function grab({ page, cdp }, t, format = 'jpeg') {
  await page.evaluate(tt => window.__seek(tt), t);
  const { data } = await cdp.send('Page.captureScreenshot', {
    format, quality: format === 'jpeg' ? 96 : undefined, captureBeyondViewport: false,
  });
  return Buffer.from(data, 'base64');
}

if (args.stills) {
  const dir = path.join(outDir, 'stills');
  mkdirSync(dir, { recursive: true });
  const p = await openPage();
  for (const t of String(args.stills).split(',').map(Number)) {
    writeFileSync(path.join(dir, `t${t.toFixed(2)}.png`), await grab(p, t, 'png'));
  }
  await p.browser.close();
  process.exit(0);
}

const duration = await (async () => {
  const p = await openPage();
  const d = await p.page.evaluate(() => window.__duration);
  await p.browser.close();
  return d;
})();
const from = Number(args.from ?? 0), to = Math.min(Number(args.to ?? duration), duration);
const first = Math.round(from * fps), last = Math.round(to * fps); // [first, last)
const workers = Number(args.workers ?? Math.max(1, os.cpus().length));
const out = path.join(outDir, args.out ?? (args.from || args.to ? `slice_${from}-${to}.mp4` : 'video.mp4'));
const segDir = path.join(outDir, 'segments');
rmSync(segDir, { recursive: true, force: true });
mkdirSync(segDir, { recursive: true });

const per = Math.ceil((last - first) / workers);
const started = Date.now();
let done = 0;

async function work(i) {
  const a = first + i * per, b = Math.min(last, a + per);
  if (a >= b) return null;
  const seg = path.join(segDir, `seg${String(i).padStart(2, '0')}.mp4`);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', String(fps), seg],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const finished = new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg ' + c)))));
  const p = await openPage();
  for (let f = a; f < b; f++) {
    const buf = await grab(p, f / fps);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    done++;
    if (i === 0 && done % 30 === 0) {
      const el = (Date.now() - started) / 1000;
      process.stdout.write(`\r${done}/${last - first} frames  ${(done / el).toFixed(1)} fps  eta ${((last - first - done) / (done / el)).toFixed(0)}s   `);
    }
  }
  ff.stdin.end();
  await finished;
  await p.browser.close();
  return seg;
}

const segs = (await Promise.all(Array.from({ length: workers }, (_, i) => work(i)))).filter(Boolean);
const list = path.join(segDir, 'list.txt');
writeFileSync(list, segs.map(s => `file '${s}'`).join('\n'));
await new Promise((res, rej) => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out],
  { stdio: 'inherit' }).on('close', c => (c === 0 ? res() : rej(new Error('concat failed')))));
console.log(`\nwrote ${out} (${((Date.now() - started) / 1000).toFixed(1)}s)`);
