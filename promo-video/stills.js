// Usage: node stills.js outDir t1 t2 ...   — renders single-sample stills (no motion blur) for review
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const [outDir, ...times] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--font-render-hinting=none'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto('file://' + path.resolve(__dirname, 'index.html'));
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });
  for (const ts of times) {
    const t = parseFloat(ts);
    await page.evaluate(t => window.render(t), t);
    await page.screenshot({ path: path.join(outDir, `t_${t.toFixed(2).padStart(5, '0')}.png`) });
  }
  await browser.close();
})();
