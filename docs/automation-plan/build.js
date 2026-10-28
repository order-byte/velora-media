// Renders plan.html to a PDF with headless Chromium.
// Usage: ./get-fonts.sh && node build.js
const path = require('path');
const { chromium } = require('playwright');

const src = path.join(__dirname, 'plan.html');
const out = path.join(__dirname, 'Agency-Automation-Plan.pdf');

const footer = `
  <div style="width:100%; margin:0 21mm; font-family:Arial, sans-serif; font-size:7.5pt; color:#6b737c;
              display:flex; justify-content:space-between;">
    <span>Running the agency on Claude agents · Draft 1</span>
    <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
  </div>`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + src, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: out,
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: footer,
  });
  await browser.close();
  console.log('wrote', out);
})();
