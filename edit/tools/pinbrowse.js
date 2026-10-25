const { chromium } = require('playwright');
const queries = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch({ proxy: { server: process.env.HTTPS_PROXY || 'http://127.0.0.1:46275' } });
  const ctx = await browser.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36', viewport: { width: 1280, height: 2000 }, ignoreHTTPSErrors: false });
  const found = {};
  for (const q of queries) {
    const page = await ctx.newPage();
    const vids = new Set();
    page.on('response', async (r) => {
      const u = r.url();
      if (u.includes('/resource/BaseSearchResource/get') || u.includes('SearchResource')) {
        try { const j = await r.json(); const res = j?.resource_response?.data?.results || [];
          for (const it of res) {
            const vl = it?.videos?.video_list || {}; let url = null, dur = null;
            for (const k of ['V_720P','V_EXP7','V_EXP6','V_EXP5','V_EXP4']) if (vl[k]) { url = vl[k].url; dur = vl[k].duration; break; }
            if (!url && it?.story_pin_data?.pages) for (const pg of it.story_pin_data.pages) for (const b of pg.blocks || []) { const v2 = b?.video?.video_list || {}; for (const k of ['V_EXP7','V_EXP6','V_EXP5','V_EXP4','V_720P']) if (!url && v2[k]) { url = v2[k].url; dur = v2[k].duration; } }
            if (url && url.endsWith('.mp4')) found[it.id] = { id: it.id, title: (it.title || it.grid_title || it.description || '').slice(0, 100), url, dur, q };
          }
        } catch (e) {}
      }
    });
    try {
      await page.goto('https://www.pinterest.com/search/videos/?q=' + encodeURIComponent(q), { waitUntil: 'domcontentloaded', timeout: 60000 });
      for (let i = 0; i < 6; i++) { await page.waitForTimeout(2500); await page.mouse.wheel(0, 3000); }
      const html = await page.content();
      for (const m of html.matchAll(/https:\/\/v1\.pinimg\.com\/videos\/[^"'\\ ]+?\.mp4/g)) vids.add(m[0]);
      console.error(`== ${q}: api ${Object.values(found).filter(x => x.q === q).length}, dom mp4 ${vids.size}, title "${await page.title()}"`);
      for (const v of vids) { const id = 'dom_' + v.split('/').pop(); if (!Object.values(found).some(x => x.url === v)) found[id] = { id, title: '', url: v, dur: null, q }; }
    } catch (e) { console.error('fail', q, e.message); }
    await page.close();
  }
  console.log(JSON.stringify(Object.values(found), null, 1));
  await browser.close();
})();
