// Frame-accurate render of src/index.html with Playwright + ffmpeg.
//
//   node scripts/render.js                       -> output/video.mp4 (silent, 60 fps)
//   node scripts/render.js --stills 1.2,5,10.5   -> output/stills/t_<t>.png
//   node scripts/render.js --cues                -> output/cues.json (SFX placements)
//
// Options: --workers N (parallel pages, default 4), --fps N, --from S --to S
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const OUT = path.join(ROOT, 'output');
const PAGE = `file://${path.join(ROOT, 'src', 'index.html')}`;

const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(`--${name}`);
  return i < 0 ? def : (args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true);
};

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => { console.error('page error:', e.message); process.exitCode = 1; });
  await page.goto(PAGE);
  await page.evaluate(() => window.PROMO.ready);
  const cdp = await page.context().newCDPSession(page);
  return { page, cdp };
}

async function grab({ page, cdp }, t, format = 'png') {
  await page.evaluate((tt) => window.PROMO.seek(tt), t);
  const { data } = await cdp.send('Page.captureScreenshot', { format, quality: format === 'jpeg' ? 95 : undefined, optimizeForSpeed: true, fromSurface: true });
  return Buffer.from(data, 'base64');
}

function encoder(file, fps) {
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', String(fps), file],
  { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error(`ffmpeg exited ${c}`)))));
  return { ff, done };
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ args: ['--font-render-hinting=none', '--disable-lcd-text'] });

  if (opt('cues')) {
    const { page } = await openPage(browser);
    const meta = await page.evaluate(() => ({ duration: window.PROMO.duration, fps: window.PROMO.fps, cues: window.PROMO.cues }));
    fs.writeFileSync(path.join(OUT, 'cues.json'), JSON.stringify(meta, null, 1));
    console.log(`wrote ${meta.cues.length} cues`);
    await browser.close();
    return;
  }

  const stills = opt('stills');
  if (stills) {
    const dir = path.join(OUT, 'stills');
    fs.mkdirSync(dir, { recursive: true });
    const p = await openPage(browser);
    for (const t of String(stills).split(',').map(Number)) {
      fs.writeFileSync(path.join(dir, `t_${t.toFixed(2)}.png`), await grab(p, t));
    }
    await browser.close();
    return;
  }

  const probe = await openPage(browser);
  const dur = await probe.page.evaluate(() => window.PROMO.duration);
  await probe.page.close();
  const fps = Number(opt('fps', 60));
  const from = Number(opt('from', 0)), to = Number(opt('to', dur));
  const f0 = Math.round(from * fps), f1 = Math.round(to * fps);
  const workers = Number(opt('workers', 4));
  const per = Math.ceil((f1 - f0) / workers);
  const segs = [];
  const t0 = Date.now();
  let doneFrames = 0;

  await Promise.all(Array.from({ length: workers }, async (_, w) => {
    const a = f0 + w * per, b = Math.min(f1, a + per);
    if (a >= b) return;
    const file = path.join(OUT, `seg_${w}.mp4`);
    segs[w] = file;
    const p = await openPage(browser);
    const enc = encoder(file, fps);
    for (let f = a; f < b; f++) {
      const buf = await grab(p, f / fps);
      if (!enc.ff.stdin.write(buf)) await new Promise((r) => enc.ff.stdin.once('drain', r));
      doneFrames++;
      if (doneFrames % 300 === 0) {
        const s = (Date.now() - t0) / 1000;
        console.log(`${doneFrames}/${f1 - f0} frames  ${(doneFrames / s).toFixed(1)} fps`);
      }
    }
    enc.ff.stdin.end();
    await enc.done;
    await p.page.close();
  }));
  await browser.close();

  const list = path.join(OUT, 'segments.txt');
  fs.writeFileSync(list, segs.filter(Boolean).map((f) => `file '${f}'`).join('\n'));
  await new Promise((res, rej) => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', path.join(OUT, 'video.mp4')], { stdio: 'inherit' })
    .on('close', (c) => (c === 0 ? res() : rej(new Error('concat failed')))));
  segs.filter(Boolean).forEach((f) => fs.unlinkSync(f));
  fs.unlinkSync(list);
  console.log(`rendered ${f1 - f0} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s -> output/video.mp4`);
})();
