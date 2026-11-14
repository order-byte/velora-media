// Prints how many sub-frames each frame would need (for planning the render).
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.resolve(__dirname, 'index.html'));
  await page.waitForFunction(() => window.__ready === true);
  const res = await page.evaluate(() => { const o = []; for (let f = 0; f < 660; f++) { const t = f / 30, h = 0.5 / 60; o.push(Math.max(1, Math.min(24, Math.ceil(window.__motion(t - h, t + h) / 4.5)))); } return o; });
  const tot = res.reduce((a, b) => a + b, 0);
  if (process.argv[2]) { const W = +process.argv[2]; let acc = 0, k = 1, cuts = [0]; res.forEach((n, f) => { acc += n; if (acc >= tot * k / W && k < W) { cuts.push(f + 1); k++; } }); cuts.push(660); console.log('CUTS', cuts.join(' ')); await browser.close(); return; }
  console.log('total shots', tot);
  let line = ''; res.forEach((n, f) => { line += n > 9 ? '#' : n; if (f % 30 === 29) { console.log(String((f + 1) / 30 - 1).padStart(4), line); line = ''; } });
  await browser.close();
})();
