// Renders comp.html frame by frame. assets/raw (SDR frames of the raw take), assets/cut (person cutouts)
// and assets/w1..w6 (work-clip frames) are generated from the source footage and are not kept in git.
// usage: node render.js stills t1,t2,...  |  node render.js range start end worker nworkers outdir
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const mode = process.argv[2];
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-web-security', '--force-color-profile=srgb'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.log('PAGEERR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await page.goto('file://' + path.resolve(__dirname, 'comp.html'));
  await page.evaluate(() => window.ready);
  if (mode === 'stills') {
    fs.mkdirSync('stills', { recursive: true });
    for (const s of process.argv[3].split(',')) {
      const t = parseFloat(s);
      await page.evaluate(t => window.renderAt(t), t);
      await page.screenshot({ path: `stills/t_${t.toFixed(2).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 90 });
    }
  } else {
    const [a, b, w, n, out] = [parseInt(process.argv[3]), parseInt(process.argv[4]), parseInt(process.argv[5]), parseInt(process.argv[6]), process.argv[7]];
    fs.mkdirSync(out, { recursive: true });
    for (let f = a; f < b; f++) {
      if (f % n !== w) continue;
      await page.evaluate(t => window.renderAt(t), f / 30);
      await page.screenshot({ path: `${out}/f_${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 95 });
    }
  }
  await browser.close();
})();
