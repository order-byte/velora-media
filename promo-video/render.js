// Renders index.html to sub-frame images for motion blur.
// Usage: node render.js <outDir> <fromFrame> <toFrame> [fps=30] [shutter=0.5]
// Writes <outDir>/f<frame>_<sub>.jpg (or .png for single-sample frames).
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const [outDir, from, to, fpsArg, shutterArg] = process.argv.slice(2);
  const fps = parseFloat(fpsArg || '30'), shutter = parseFloat(shutterArg || '0.5');
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--font-render-hinting=none'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto('file://' + path.resolve(__dirname, 'index.html'));
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });
  const t0 = Date.now(); let shots = 0;
  for (let f = +from; f < +to; f++) {
    const t = f / fps, half = shutter / fps / 2;
    const m = await page.evaluate(([a, b]) => window.__motion(a, b), [t - half, t + half]);
    const n = Math.max(1, Math.min(24, Math.ceil(m / 4.5)));
    for (let i = 0; i < n; i++) {
      const ts = n === 1 ? t : t - half + (2 * half) * (i + 0.5) / n;
      await page.evaluate(ts => window.render(ts), ts);
      const name = `f${String(f).padStart(5, '0')}_${String(i).padStart(2, '0')}.` + (n === 1 ? 'png' : 'jpg');
      await page.screenshot({ path: path.join(outDir, name), type: n === 1 ? 'png' : 'jpeg', ...(n === 1 ? {} : { quality: 97 }) });
      shots++;
    }
    fs.writeFileSync(path.join(outDir, `done_${String(f).padStart(5, '0')}`), String(n));
  }
  console.log(`frames ${from}-${to}: ${shots} shots in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  await browser.close();
})();
