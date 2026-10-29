// Bundles the Lucide icons used by video.html into icons.js (window.ICONS).
const fs = require('fs');
const path = require('path');
const names = ['user-plus','mail','key-round','check','lock','calendar-clock','calendar','wallet','banknote','hand-coins','circle-check','list-checks','camera','message-circle','messages-square','file-text','sparkles','asterisk','clock','database','shield-check','send','arrow-right','footprints','circle-help','handshake','rocket','layers','user-check','info','square','square-check'];
const dir = path.join(__dirname, 'node_modules/lucide-static/icons');
const out = {};
for (const n of names) {
  const f = path.join(dir, n + '.svg');
  if (!fs.existsSync(f)) { console.error('missing', n); continue; }
  out[n] = fs.readFileSync(f, 'utf8').replace(/<!--.*?-->/gs, '').replace(/\s*class="[^"]*"/, '').trim();
}
fs.writeFileSync(path.join(__dirname, 'icons.js'), 'window.ICONS = ' + JSON.stringify(out) + ';\n');
console.log(Object.keys(out).length, 'icons');
