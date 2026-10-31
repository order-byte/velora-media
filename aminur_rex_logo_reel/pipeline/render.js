// usage: node render.js <fontfile> <outdir> <mode> [args]
// mode "stills": u values list -> composite preview on purple
// mode "frames": framesFile JSON [{name,u}] -> solid_*.png, light_*.png
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [fontFile, outDir, mode, arg, thick] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setContent('<html><body style="margin:0;background:#000"></body></html>');
  await page.addScriptTag({ path: path.join(__dirname, 'opentype.min.js') });
  await page.addScriptTag({ path: path.join(__dirname, 'logo.js') });
  const b64 = fs.readFileSync(fontFile).toString('base64');
  const info = await page.evaluate(([b, t]) => setupLogo(b, { thick: t }), [b64, thick ? Number(thick) : 7]);
  console.error('setup', JSON.stringify(info));
  if (mode === 'stills') {
    const us = arg.split(',').map(Number);
    for (const u of us) {
      const data = await page.evaluate((u) => {
        renderLogo(u);
        const c = document.createElement('canvas'); c.width = 1440; c.height = 1140; const x = c.getContext('2d');
        const g = x.createRadialGradient(672, 600, 50, 672, 600, 900); g.addColorStop(0, '#3a1450'); g.addColorStop(1, '#12061a');
        x.fillStyle = g; x.fillRect(0, 0, 1440, 1140);
        x.drawImage(solidCanvas, 0, 0); x.globalCompositeOperation = 'lighter'; x.drawImage(lightCanvas, 0, 0);
        return c.toDataURL('image/png');
      }, u);
      fs.writeFileSync(path.join(outDir, `still_${u.toFixed(3)}.png`), Buffer.from(data.split(',')[1], 'base64'));
    }
  } else {
    const list = JSON.parse(fs.readFileSync(arg));
    for (const it of list) {
      const [a, b] = await page.evaluate((u) => { renderLogo(u); return [solidCanvas.toDataURL('image/png'), lightCanvas.toDataURL('image/png')]; }, it.u);
      fs.writeFileSync(path.join(outDir, `solid_${it.name}.png`), Buffer.from(a.split(',')[1], 'base64'));
      fs.writeFileSync(path.join(outDir, `light_${it.name}.png`), Buffer.from(b.split(',')[1], 'base64'));
    }
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
