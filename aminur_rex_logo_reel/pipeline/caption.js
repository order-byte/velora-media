const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const out = process.argv[2];
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setContent(`<html><body style="margin:0"><canvas id=c width=720 height=1280></canvas>
  <div style="font-family:Inter;font-weight:600">x</div></body></html>`);
  await page.evaluate(() => document.fonts.ready);
  const data = await page.evaluate(() => {
    const c = document.getElementById('c'), x = c.getContext('2d');
    const lines = ['POV: Client asked for', 'a demo logo animation \u{1F440}'];
    const fs = 44, H = 66, padX = 24, r = 16, CXX = 360, CYY = 978;
    x.font = `600 ${fs}px Inter, "Noto Color Emoji"`;
    const ws = lines.map(l => x.measureText(l).width);
    const top = CYY - H * lines.length / 2;
    const boxes = ws.map((w, i) => ({ x1: CXX - w / 2 - padX, x2: CXX + w / 2 + padX, y1: top + i * H, y2: top + (i + 1) * H }));
    const rr = (b) => { x.beginPath(); x.roundRect(b.x1, b.y1, b.x2 - b.x1, b.y2 - b.y1, r); x.fill(); };
    x.fillStyle = '#FFFFFF';
    boxes.forEach(rr);
    // fill seam between boxes (square inner corners) then concave fillets
    for (let i = 0; i < boxes.length - 1; i++) {
      const a = boxes[i], b = boxes[i + 1];
      const nx1 = Math.max(a.x1, b.x1), nx2 = Math.min(a.x2, b.x2);
      x.fillRect(nx1, a.y2 - r, nx2 - nx1, 2 * r);
      const narrow = (a.x2 - a.x1) < (b.x2 - b.x1) ? 'top' : 'bottom';
      const fr = Math.min(r, Math.abs((a.x1 - b.x1)) - 0.5);
      if (fr > 1) {
        const yJ = a.y2;
        [[nx1, -1], [nx2, 1]].forEach(([xe, s]) => {
          // square in the outer corner region then carve circle
          const sy = narrow === 'top' ? yJ - fr : yJ;
          const sx = s < 0 ? xe - fr : xe;
          x.fillRect(sx, sy, fr, fr);
          x.save(); x.globalCompositeOperation = 'destination-out';
          const ccx = s < 0 ? xe - fr : xe + fr, ccy = narrow === 'top' ? yJ - fr : yJ + fr;
          x.beginPath(); x.arc(ccx, ccy, fr, 0, Math.PI * 2); x.fill(); x.restore();
        });
      }
    }
    x.fillStyle = '#000';
    x.textAlign = 'center'; x.textBaseline = 'middle';
    lines.forEach((l, i) => x.fillText(l, CXX, top + i * H + H / 2 + 2));
    return { png: c.toDataURL('image/png'), boxes };
  });
  fs.writeFileSync(out, Buffer.from(data.png.split(',')[1], 'base64'));
  console.log(JSON.stringify(data.boxes));
  await browser.close();
})();
