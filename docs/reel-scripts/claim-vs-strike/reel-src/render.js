// Renders reel.html frame by frame (served from http://127.0.0.1:8765).
//   node render.js stills 3,12.5        -> stills/t_<sec>.jpg
//   node render.js frames <workers>      -> frames/f_00000.jpg ...   (+ events.json)
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');

const URL = 'http://127.0.0.1:8765/reel.html';
const LIVE = '/tmp/claude-0/-home-user-velora-media/66ff1a82-31ea-5c05-a6ba-b6463a076dc9/scratchpad/live/live.py';
const live = (...a) => { try { execFileSync('python3', [LIVE, ...a.map(String)]); } catch {} };

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('pageerror', e.message));
  await page.goto(URL, { waitUntil: 'load' });
  await page.waitForFunction(() => window.READY && window.seek, null, { timeout: 120000 });
  await page.evaluate(() => window.READY);
  return page;
}

(async () => {
  const [mode, arg] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  if (mode === 'stills') {
    fs.mkdirSync(path.join(__dirname, 'stills'), { recursive: true });
    const page = await openPage(browser);
    for (const t of arg.split(',').map(Number)) {
      await page.evaluate(t => window.seek(t), t);
      const f = path.join(__dirname, 'stills', `t_${t.toFixed(1)}.jpg`);
      await page.screenshot({ path: f, type: 'jpeg', quality: 90 });
      live('frame', f, `Preview at ${t.toFixed(1)}s`);
    }
  } else {
    const workers = Number(arg || 4);
    const dir = path.join(__dirname, 'frames');
    fs.mkdirSync(dir, { recursive: true });
    const probe = await openPage(browser);
    const info = await probe.evaluate(() => ({ duration: window.DURATION, fps: window.FPS, events: window.EVENTS }));
    fs.writeFileSync(path.join(__dirname, 'events.json'), JSON.stringify(info.events, null, 1));
    await probe.close();
    const total = Math.ceil(info.duration * info.fps);
    let done = fs.readdirSync(dir).length;
    const started = Date.now();
    console.log('frames', total);
    // interleaved split so the live preview walks through the whole film
    await Promise.all(Array.from({ length: workers }, async (_, w) => {
      const page = await openPage(browser);
      for (let f = w; f < total; f += workers) {
        const file = path.join(dir, `f_${String(f).padStart(5, '0')}.jpg`);
        if (fs.existsSync(file)) continue;
        await page.evaluate(t => window.seek(t), f / info.fps);
        await page.screenshot({ path: file, type: 'jpeg', quality: 92 });
        done++;
        if (w === 0 && done % 24 < workers) {
          const el = (Date.now() - started) / 1000, eta = el / done * (total - done);
          live('status', 'Rendering the reel', `Frame ${done} of ${total}, about ${Math.ceil(eta / 60)} min left`, done / total);
          live('frame', file, `Frame ${f} (${(f / info.fps).toFixed(1)}s)`);
        }
      }
    }));
    live('status', 'Frames rendered', `${total} frames in ${Math.round((Date.now() - started) / 60000)} min`, 1);
    console.log('done in', ((Date.now() - started) / 1000).toFixed(0), 's');
  }
  await browser.close();
})();
