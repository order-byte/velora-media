// slides.js থেকে প্রতিটা স্লাইডের HTML আর 1920x1080 PNG বানায়, ভয়েসের লেখা আলাদা ফাইলে রাখে।
// ব্যবহার: node render.js <আউটপুট ফোল্ডার>
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const slides = require('./slides');

const out = path.resolve(process.argv[2] || 'build');
const fontDir = path.join(__dirname, 'fonts');
const bn = (n) => String(n).replace(/\d/g, (d) => '০১২৩৪৫৬৭৮৯'[d]);

const css = `
@font-face { font-family: Hind; font-weight: 400; src: url('file://${fontDir}/HindSiliguri-Regular.ttf'); }
@font-face { font-family: Hind; font-weight: 600; src: url('file://${fontDir}/HindSiliguri-SemiBold.ttf'); }
@font-face { font-family: Hind; font-weight: 700; src: url('file://${fontDir}/HindSiliguri-Bold.ttf'); }
:root { --g: #14532d; --g2: #166534; --leaf: #dcfce7; --amb: #f59e0b; --amb2: #fef3c7; --cream: #fefce8; --ink: #1f2937; --mut: #4b5563; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1920px; height: 1080px; }
body { background: var(--cream); color: var(--ink); font-family: Hind, 'Noto Color Emoji', sans-serif; position: relative; overflow: hidden; }
.frame { position: absolute; inset: 0; padding: 110px 130px 120px; }
.top { position: absolute; top: 40px; left: 130px; right: 130px; display: flex; justify-content: space-between; font-size: 28px; color: var(--mut); font-weight: 600; }
.bar { position: absolute; left: 0; bottom: 0; height: 14px; background: var(--g2); }
.bar-bg { position: absolute; left: 0; right: 0; bottom: 0; height: 14px; background: #e7e5c9; }
h1 { font-size: 76px; font-weight: 700; color: var(--g); line-height: 1.25; margin-bottom: 50px; }
h2 { font-size: 46px; font-weight: 700; color: var(--g); line-height: 1.3; }
ul { list-style: none; }
li { display: flex; align-items: center; gap: 30px; }
.ic { flex: none; width: 88px; height: 88px; border-radius: 24px; background: var(--leaf); display: grid; place-items: center; font-size: 48px; font-weight: 700; color: var(--g); }
.big li { font-size: 54px; font-weight: 600; margin-bottom: 34px; }
.mid li { font-size: 44px; font-weight: 600; margin-bottom: 24px; }
.mid .ic { width: 74px; height: 74px; font-size: 40px; border-radius: 20px; }
.cols { display: grid; grid-template-columns: 1fr 1fr; column-gap: 70px; }
.note { margin-top: 46px; font-size: 38px; color: var(--mut); background: var(--amb2); border-left: 10px solid var(--amb); padding: 22px 34px; border-radius: 12px; }
.note.friend { margin-top: 24px; background: var(--leaf); border-left-color: var(--g2); color: var(--g); font-weight: 600; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; }
.card, .pay-c, .pr, .ms, .step { background: #fff; border-radius: 32px; box-shadow: 0 10px 34px rgba(20,83,45,.12); padding: 50px; }
.card-ic { font-size: 96px; margin-bottom: 18px; }
.card p, .pay-c p, .pr p, .ms p, .step p { font-size: 40px; color: var(--mut); line-height: 1.4; margin-top: 12px; }
/* title slides */
.hero { height: 100%; display: flex; flex-direction: column; justify-content: center; }
.hero-tag { font-size: 40px; font-weight: 600; color: var(--g2); background: var(--leaf); padding: 10px 34px; border-radius: 999px; align-self: flex-start; margin-bottom: 40px; }
.hero-title { font-size: 104px; margin-bottom: 36px; }
.hero-sub { font-size: 52px; color: var(--mut); font-weight: 600; }
.hero-by { margin-top: 70px; font-size: 56px; font-weight: 700; color: var(--amb); }
.hero-ic { font-size: 130px; margin-bottom: 20px; }
/* phone mockup */
.with-phone { display: grid; grid-template-columns: 1fr 560px; gap: 60px; align-items: start; margin-top: -10px; }
.phone { background: #fff; border: 14px solid #1f2937; border-radius: 56px; padding: 34px 28px; height: 760px; position: relative; margin-top: -40px; }
.ph-top { font-size: 36px; font-weight: 700; color: #fff; background: var(--g2); border-radius: 18px; padding: 12px 22px; }
.ph-search { margin: 18px 0; font-size: 28px; color: #6b7280; background: #f3f4f6; border-radius: 14px; padding: 12px 18px; }
.ph-item { display: flex; justify-content: space-between; align-items: center; font-size: 28px; padding: 16px 6px; border-bottom: 2px solid #f1f1f1; }
.ph-item b { font-size: 24px; color: var(--g2); background: var(--leaf); border-radius: 10px; padding: 4px 12px; white-space: nowrap; }
.ph-btn { margin-top: 26px; font-size: 30px; font-weight: 700; text-align: center; background: var(--amb); color: #fff; border-radius: 18px; padding: 16px; }
.ph-cart { margin-top: 16px; font-size: 28px; font-weight: 600; text-align: center; color: var(--g2); border: 3px solid var(--g2); border-radius: 18px; padding: 12px; }
.ph-cap { position: absolute; bottom: -62px; left: 0; right: 0; text-align: center; font-size: 26px; color: var(--mut); }
/* AI flow */
.ai-flow { display: grid; grid-template-columns: 1fr 220px 1fr; align-items: center; gap: 30px; }
.paper, .cart { background: #fff; border-radius: 28px; box-shadow: 0 10px 34px rgba(20,83,45,.12); padding: 40px 46px; min-height: 380px; }
.paper { background: #fffdf2; border: 3px dashed #d6c98f; transform: rotate(-1.5deg); }
.paper-h { font-size: 36px; font-weight: 700; color: var(--g); margin-bottom: 20px; }
.hand { font-size: 46px; line-height: 1.65; color: #1e3a8a; font-style: italic; }
.arrow { text-align: center; font-size: 56px; color: var(--amb); font-weight: 700; line-height: 1.3; }
.arrow small { font-size: 44px; color: var(--g); }
.cart-row { display: flex; justify-content: space-between; font-size: 40px; padding: 12px 0; border-bottom: 2px solid #eee; font-weight: 600; }
.cart-row b { color: var(--g2); }
.cart-ok { margin-top: 22px; font-size: 32px; color: #fff; background: var(--g2); border-radius: 14px; padding: 10px 20px; text-align: center; }
.later { display: flex; gap: 26px; margin-top: 50px; flex-wrap: wrap; }
.later span { font-size: 34px; font-weight: 600; background: var(--amb2); border-radius: 999px; padding: 12px 30px; }
/* payments */
.pay { display: grid; grid-template-columns: repeat(4, 1fr); gap: 36px; margin-top: 20px; }
.pay-c { text-align: center; padding: 50px 30px; }
.pay-c.good { border-top: 14px solid #22c55e; }
.pay-c.opt { border-top: 14px solid #9ca3af; opacity: .9; }
/* steps */
.steps { display: grid; grid-template-columns: 1.3fr 1fr 1fr; gap: 36px; }
.step { padding: 44px; }
.steps p { font-size: 42px; }
.step.s1 { border: 6px solid var(--g2); }
.step-n { font-size: 40px; font-weight: 700; color: var(--g); }
.step-x { color: var(--amb) !important; font-weight: 700; }
.timeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 60px; }
.timeline span { font-size: 32px; background: var(--leaf); border-radius: 20px; padding: 20px 26px; line-height: 1.45; }
.timeline b { display: block; color: var(--g); font-size: 34px; }
/* prices */
.price { display: grid; grid-template-columns: 1fr 1.15fr 1fr; gap: 40px; align-items: center; }
.pr { text-align: center; position: relative; padding: 50px 30px; }
.pr.best { border: 8px solid var(--amb); padding: 70px 40px; }
.amt { font-size: 54px; font-weight: 700; color: var(--ink); margin: 16px 0 8px; white-space: nowrap; }
.badge { position: absolute; top: -34px; left: 50%; transform: translateX(-50%); background: var(--amb); color: #fff; font-size: 32px; font-weight: 700; padding: 8px 30px; border-radius: 999px; white-space: nowrap; }
/* table */
.tbl { width: 100%; border-collapse: collapse; font-size: 42px; background: #fff; border-radius: 28px; overflow: hidden; box-shadow: 0 10px 34px rgba(20,83,45,.12); margin-top: -14px; }
.tbl td { padding: 16px 40px; border-bottom: 2px solid #f1f1e6; font-weight: 600; }
.tbl td:last-child { text-align: right; color: var(--g2); }
.tbl .sum td { background: var(--g2); color: #fff; font-weight: 700; font-size: 46px; }
/* milestones */
.miles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 36px; margin-top: 30px; }
.ms { text-align: center; padding: 60px 30px; }
.pct { font-size: 110px; font-weight: 700; color: var(--g2); line-height: 1.1; }
`;

const page = (s, i) => `<!doctype html><html lang="bn"><head><meta charset="utf-8"><style>${css}</style></head><body>
  ${s.kind === 'title' ? '' : `<div class="top"><span>বলয় কাকুর পাইকারি অ্যাপ · প্ল্যান</span><span>${bn(i + 1)} / ${bn(slides.length)}</span></div>`}
  <div class="frame">${s.html}</div>
  <div class="bar-bg"></div><div class="bar" style="width:${((i + 1) / slides.length) * 100}%"></div>
</body></html>`;

(async () => {
  for (const d of ['html', 'png', 'say']) fs.mkdirSync(path.join(out, d), { recursive: true });
  const browser = await chromium.launch();
  const tab = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const [i, s] of slides.entries()) {
    const n = String(i + 1).padStart(2, '0');
    const htmlFile = path.join(out, 'html', `${n}.html`);
    fs.writeFileSync(htmlFile, page(s, i));
    fs.writeFileSync(path.join(out, 'say', `${n}.txt`), s.say);
    await tab.goto('file://' + htmlFile);
    await tab.evaluate(() => document.fonts.ready);
    await tab.screenshot({ path: path.join(out, 'png', `${n}.png`) });
  }
  await browser.close();
  console.log(`${slides.length} slides -> ${out}`);
})();
