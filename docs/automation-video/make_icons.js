// Bundles the Lucide icons used by video.html into icons.js (window.ICONS).
const fs = require('fs');
const path = require('path');
const names = ['message-circle','user-plus','wallet','shield-alert','clipboard-list','search','pen-line','palette',
  'badge-check','megaphone','camera','play','database','key-round','calendar-clock','gauge','users','check','x',
  'clock','timer','lock','ban','file-text','send','hand','image','shield-check','circle-check','circle-x','asterisk',
  'user-check','sheet','link','dollar-sign','mouse-pointer-2','messages-square','scale','hourglass','sparkles',
  'trending-up','receipt','bot','plug','zap','hand-coins','eye'];
const dir = path.join(__dirname, 'node_modules/lucide-static/icons');
const out = {};
for (const n of names) {
  const f = path.join(dir, n + '.svg');
  if (!fs.existsSync(f)) { console.error('missing', n); continue; }
  out[n] = fs.readFileSync(f, 'utf8').replace(/<!--.*?-->/gs, '').replace(/\s*class="[^"]*"/, '').trim();
}
fs.writeFileSync(path.join(__dirname, 'icons.js'), 'window.ICONS = ' + JSON.stringify(out) + ';\n');
console.log(Object.keys(out).length, 'icons');
