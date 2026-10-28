// Renders video.html frame by frame.
//   node render.js stills 3.5,20,40        -> stills/t_<sec>.png
//   node render.js frames <workers>         -> frames/f_00000.jpg ...
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

const url = 'file://' + path.join(__dirname, 'video.html');

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.error('pageerror', e.message));
  await page.goto(url, { waitUntil: 'load' });
  await page.evaluate(() => window.READY);
  return page;
}

async function warm(page, t) {
  // walk the timeline forward so every tween records its start values in order
  await page.evaluate(t => { for (let x = 0; x < t; x += 0.2) window.seek(x); window.seek(t); }, t);
}

(async () => {
  const [mode, arg] = process.argv.slice(2);
  const browser = await chromium.launch();
  if (mode === 'stills') {
    fs.mkdirSync(path.join(__dirname, 'stills'), { recursive: true });
    const page = await openPage(browser);
    const times = arg.split(',').map(Number).sort((a, b) => a - b);
    for (const t of times) {
      await warm(page, t);
      await page.screenshot({ path: path.join(__dirname, 'stills', `t_${t.toFixed(1)}.png`) });
    }
  } else {
    const workers = Number(arg || 4);
    const dir = path.join(__dirname, 'frames');
    fs.mkdirSync(dir, { recursive: true });
    const probe = await openPage(browser);
    const { duration, fps } = await probe.evaluate(() => ({ duration: window.DURATION, fps: window.FPS }));
    await probe.close();
    const total = Math.ceil(duration * fps);
    const per = Math.ceil(total / workers);
    console.log('frames', total);
    const started = Date.now();
    await Promise.all(Array.from({ length: workers }, async (_, w) => {
      const page = await openPage(browser);
      const a = w * per, b = Math.min(total, a + per);
      await warm(page, a / fps);
      for (let f = a; f < b; f++) {
        const file = path.join(dir, `f_${String(f).padStart(5, '0')}.jpg`);
        if (fs.existsSync(file)) continue;
        await page.evaluate(t => window.seek(t), f / fps);
        await page.screenshot({ path: file, type: 'jpeg', quality: 93 });
        if (w === 0 && (f - a) % 300 === 0) console.log(`worker0 ${f - a}/${b - a}  ${((Date.now() - started) / 1000).toFixed(0)}s`);
      }
    }));
    console.log('done in', ((Date.now() - started) / 1000).toFixed(0), 's');
  }
  await browser.close();
})();
