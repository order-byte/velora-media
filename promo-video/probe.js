// Plans the render: how many motion-blur sub-frames each frame needs, and balanced frame ranges per worker.
// Usage: node probe.js [workers=3] [fps=60] [shutter=0.6]   → prints "CUTS a b c ..." and the total shot count
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const W = +(process.argv[2] || 3), fps = +(process.argv[3] || 60), shutter = +(process.argv[4] || 0.6);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.resolve(__dirname, 'index.html'));
  await page.waitForFunction(() => window.__ready === true);
  const res = await page.evaluate(([fps, shutter]) => {
    const o = [], N = Math.round(window.CONFIG.duration * fps);
    for (let f = 0; f < N; f++) { const t = f / fps, h = shutter / fps / 2; o.push(Math.max(1, Math.min(24, Math.ceil(window.__motion(t - h, t + h) / 4.5)))); }
    return o;
  }, [fps, shutter]);
  const tot = res.reduce((a, b) => a + b, 0);
  let acc = 0, k = 1; const cuts = [0];
  res.forEach((n, f) => { acc += n; if (acc >= tot * k / W && k < W) { cuts.push(f + 1); k++; } });
  cuts.push(res.length);
  console.error('frames', res.length, 'total shots', tot);
  console.log('CUTS ' + cuts.join(' '));
  await browser.close();
})();
