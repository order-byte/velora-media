// Builds the two rate-card PDFs for the Hindi Facts channel client.
// Change the numbers below and run:  node rate-cards/build.js
const path = require('path');
const { chromium } = require('playwright');

const LONG = 2000;          // Long video, 5-6 min
const SHORT = 500;          // Short, 30-40 sec
const MONTHLY_COUNT = 8;    // long + short pairs per month
const DISCOUNT = 16;        // % off on monthly

const BUNDLE = LONG + SHORT;
const monthlyLong = LONG * MONTHLY_COUNT;
const monthlyShort = SHORT * MONTHLY_COUNT;
const monthlyTotal = monthlyLong + monthlyShort;
const monthlyOff = Math.round(monthlyTotal * DISCOUNT / 100);
const monthlyFinal = monthlyTotal - monthlyOff;
const perBundleMonthly = Math.round(monthlyFinal / MONTHLY_COUNT);

const rs = n => '₹' + n.toLocaleString('en-IN');

const css = `
@page { size: A4; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Inter, 'DejaVu Sans', sans-serif; color: #1b1b1b; background: #fff; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { width: 210mm; height: 297mm; position: relative; overflow: hidden; }
.top { background: #141414; color: #fff; padding: 13mm 16mm 11mm; display: flex; justify-content: space-between; align-items: flex-end; }
.brand { font-size: 15pt; font-weight: 800; letter-spacing: .16em; }
.brand-sub { font-size: 9.5pt; color: #a9a9a9; margin-top: 5px; letter-spacing: .02em; }
.tag { background: #e0262b; color: #fff; font-size: 8.5pt; font-weight: 700; letter-spacing: .12em; padding: 6px 12px; border-radius: 3px; }
.body { padding: 13mm 16mm 0; }
h1 { font-size: 25pt; font-weight: 800; letter-spacing: -.01em; }
.sub { font-size: 11pt; color: #6b6b6b; margin-top: 4px; }
.intro { font-size: 11pt; line-height: 1.6; margin-top: 9mm; color: #333; }
.label { font-size: 8.5pt; font-weight: 700; letter-spacing: .14em; color: #8a8a8a; margin: 9mm 0 3mm; }
.item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #e7e7e7; }
.item:first-of-type { border-top: 1px solid #e7e7e7; }
.item .name { font-size: 12.5pt; font-weight: 700; }
.item .name span { font-weight: 500; color: #8a8a8a; font-size: 10.5pt; margin-left: 6px; }
.item .desc { font-size: 9.8pt; color: #5c5c5c; margin-top: 4px; line-height: 1.45; }
.item .price { font-size: 17pt; font-weight: 800; white-space: nowrap; margin-left: 20px; }
.item.hl { background: #fff2f2; border-left: 4px solid #e0262b; padding-left: 12px; padding-right: 12px; border-bottom-color: #f3d6d6; }
.item.hl .price { color: #e0262b; }
.free { margin-top: 6mm; border: 1.5px dashed #e0262b; border-radius: 6px; padding: 11px 14px; font-size: 10.5pt; color: #444; }
.free b { color: #e0262b; font-size: 11.5pt; margin-right: 6px; }
.steps { display: flex; gap: 12px; }
.step { flex: 1; border: 1px solid #e2e2e2; border-radius: 6px; padding: 12px 14px; }
.step .pct { font-size: 20pt; font-weight: 800; color: #e0262b; }
.step .what { font-size: 10.5pt; font-weight: 600; margin-top: 2px; }
.step .when { font-size: 9.6pt; color: #666; margin-top: 3px; line-height: 1.45; }
.small { font-size: 9.8pt; color: #555; margin-top: 3.5mm; line-height: 1.5; }
.note { margin-top: 8mm; background: #f4f4f4; border-radius: 6px; padding: 12px 14px; font-size: 10.5pt; line-height: 1.55; color: #333; }
.foot { position: absolute; left: 16mm; right: 16mm; bottom: 13mm; display: flex; justify-content: space-between; align-items: flex-end; border-top: 2px solid #141414; padding-top: 9px; }
.foot .thanks { font-size: 12pt; font-weight: 700; }
.foot .who { font-size: 9.5pt; color: #777; }
table { width: 100%; border-collapse: collapse; font-size: 11pt; }
td { padding: 9px 0; border-bottom: 1px solid #ececec; }
td.r { text-align: right; font-weight: 600; white-space: nowrap; }
tr.total td { font-weight: 700; border-bottom: 1px solid #cfcfcf; }
tr.off td { color: #e0262b; font-weight: 600; }
.final { margin-top: 4mm; background: #141414; color: #fff; border-radius: 6px; padding: 13px 16px; display: flex; justify-content: space-between; align-items: center; }
.final .t { font-size: 11pt; font-weight: 600; }
.final .t span { display: block; font-size: 9pt; color: #a9a9a9; font-weight: 500; margin-top: 3px; }
.final .p { font-size: 22pt; font-weight: 800; }
.pill { display: inline-block; background: #e0262b; color: #fff; font-size: 9pt; font-weight: 700; padding: 3px 9px; border-radius: 20px; margin-left: 8px; vertical-align: middle; }
.incl { font-size: 10pt; color: #444; line-height: 1.7; }
`;

const header = tag => `
  <div class="top">
    <div>
      <div class="brand">TEAM AMINUR REX</div>
      <div class="brand-sub">Video Editing &nbsp;|&nbsp; Long Videos + Shorts</div>
    </div>
    <div class="tag">${tag}</div>
  </div>`;

const footer = `
  <div class="foot">
    <div class="thanks">Shukriya!</div>
    <div class="who">- Team Aminur Rex</div>
  </div>`;

const perVideo = `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body><div class="page">
  ${header('RATE CARD')}
  <div class="body">
    <h1>Per Video Charges</h1>
    <div class="sub">Hindi Facts channel ke liye (Long + Shorts)</div>

    <p class="intro">Hello! Aapki requirement padh li hai. Neeche har video ka rate alag-alag likh diya hai, taaki sab clear rahe.</p>

    <div class="label">HAR VIDEO KA RATE</div>
    <div class="item">
      <div>
        <div class="name">Long Video <span>5-6 min</span></div>
        <div class="desc">Fast pacing, heavy sound effects, stock footage, text pop-ups, background music</div>
      </div>
      <div class="price">${rs(LONG)}</div>
    </div>
    <div class="item">
      <div>
        <div class="name">Short Video <span>30-40 sec</span></div>
        <div class="desc">Usi long video me se best part nikal ke, 9:16 format me</div>
      </div>
      <div class="price">${rs(SHORT)}</div>
    </div>
    <div class="item hl">
      <div>
        <div class="name">Bundle <span>1 Long + 1 Short</span></div>
        <div class="desc">Dono ek saath</div>
      </div>
      <div class="price">${rs(BUNDLE)}</div>
    </div>

    <div class="free"><b>Thumbnail FREE</b> har video ke saath, koi extra charge nahi.</div>

    <div class="label">PAYMENT KAISE HOGA</div>
    <div class="steps">
      <div class="step">
        <div class="pct">50%</div>
        <div class="what">Advance</div>
        <div class="when">Kaam start karne se pehle</div>
      </div>
      <div class="step">
        <div class="pct">50%</div>
        <div class="what">Baaki payment</div>
        <div class="when">Video complete hone ke baad</div>
      </div>
    </div>
    <p class="small">Har video ke liye yahi process rahega. Jaise bundle ${rs(BUNDLE)} ka hai, toh ${rs(BUNDLE / 2)} pehle aur ${rs(BUNDLE / 2)} kaam ke baad.</p>

    <div class="note">Rate pe thodi baat ho sakti hai, <b>open to negotiation</b>. Kuch bhi poochna ho toh WhatsApp pe message kar dijiye.</div>
  </div>
  ${footer}
</div></body></html>`;

const monthly = `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body><div class="page">
  ${header('MONTHLY')}
  <div class="body">
    <h1>Monthly Package <span class="pill">${DISCOUNT}% OFF</span></h1>
    <div class="sub">Regular kaam ke liye, per video se sasta</div>

    <p class="intro">Agar aap har mahine regular videos banwana chahte ho, toh monthly package lena better rahega. Same quality, kam price.</p>

    <div class="label">HAR MAHINE MILEGA</div>
    <table>
      <tr><td>${MONTHLY_COUNT} Long Videos (5-6 min) &times; ${rs(LONG)}</td><td class="r">${rs(monthlyLong)}</td></tr>
      <tr><td>${MONTHLY_COUNT} Shorts (30-40 sec) &times; ${rs(SHORT)}</td><td class="r">${rs(monthlyShort)}</td></tr>
      <tr><td>${MONTHLY_COUNT} Thumbnails</td><td class="r">FREE</td></tr>
      <tr class="total"><td>Total</td><td class="r">${rs(monthlyTotal)}</td></tr>
      <tr class="off"><td>Monthly discount (${DISCOUNT}%)</td><td class="r">- ${rs(monthlyOff)}</td></tr>
    </table>
    <div class="final">
      <div class="t">Aapka monthly price<span>Matlab ek bundle sirf ${rs(perBundleMonthly)} ka pada</span></div>
      <div class="p">${rs(monthlyFinal)}</div>
    </div>

    <div class="label">EDITING ME KYA HOGA</div>
    <div class="incl">Fast pacing, heavy sound effects, stock footage, text pop-ups aur background music. Shorts usi long video me se nikale jayenge.</div>

    <div class="label">PAYMENT KAISE HOGA</div>
    <div class="steps">
      <div class="step">
        <div class="pct">50%</div>
        <div class="what">${rs(monthlyFinal / 2)} advance</div>
        <div class="when">Mahine ki shuruaat me, kaam start hone se pehle</div>
      </div>
      <div class="step">
        <div class="pct">50%</div>
        <div class="what">${rs(monthlyFinal / 2)} baaki</div>
        <div class="when">Mahine ke saare videos complete hone ke baad</div>
      </div>
    </div>

    <div class="note">Videos kam ya zyada chahiye? Bata dijiye, package usi hisaab se set kar denge. Price pe bhi baat ho sakti hai, <b>open to negotiation</b>.</div>
  </div>
  ${footer}
</div></body></html>`;

(async () => {
  const outDir = __dirname;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const jobs = [
    [perVideo, 'Team-Aminur-Rex_Per-Video-Rates.pdf'],
    [monthly, 'Team-Aminur-Rex_Monthly-Package.pdf'],
  ];
  for (const [html, name] of jobs) {
    await page.setContent(html, { waitUntil: 'load' });
    await page.pdf({ path: path.join(outDir, name), format: 'A4', printBackground: true, preferCSSPageSize: true });
    console.log('wrote', name);
  }
  await browser.close();
})();
