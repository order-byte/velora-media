// Bundles the Lucide icons used by video.html into icons.js (window.ICONS).
const fs = require('fs');
const path = require('path');
const names = ['message-circle','music','tag','clock','shield-check','triangle-alert','check','x','mic','pause','users','sparkles','list-checks','target','quote','lightbulb','circle-help','send','hand','book-open','file-text','arrow-right','star','hand-heart','key-round','timer','search','badge-check'];
const dir = path.join(__dirname, 'node_modules/lucide-static/icons');
const out = {};
for (const n of names) {
  const f = path.join(dir, n + '.svg');
  if (!fs.existsSync(f)) { console.error('missing', n); continue; }
  out[n] = fs.readFileSync(f, 'utf8').replace(/<!--.*?-->/gs, '').replace(/\s*class="[^"]*"/, '').trim();
}
fs.writeFileSync(path.join(__dirname, 'icons.js'), 'window.ICONS = ' + JSON.stringify(out) + ';\n');
console.log(Object.keys(out).length, 'icons');
