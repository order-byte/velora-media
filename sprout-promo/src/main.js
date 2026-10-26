/* Sprout promo — a motion piece driven by one paused GSAP timeline.
 * 1920x1080 by default; ?format=portrait lays the same timeline out at 1080x1920
 * (Instagram Reels). window.PROMO.seek(t) renders the frame at time t; PROMO.cues
 * lists the sound effects (by name, from ../sfx) that the audio build places. */
(() => {
  const INK = '#12141c', GREY = '#8a8fa3', BLUE = '#3b4fe8', NAVY = '#0f1430';
  const YEL = '#f7c84a', GREEN = '#2dcb8a', PINK = '#ed93b1';
  const DUR = 55.5, FPS = 60;

  const qs = new URLSearchParams(location.search);
  const PORT = qs.get('format') === 'portrait';
  const SW = PORT ? 1080 : 1920, SH = PORT ? 1920 : 1080;
  const pv = (land, port) => (PORT ? port : land);   // pick a value per format

  const stage = document.getElementById('stage');
  Object.assign(stage.style, { width: `${SW}px`, height: `${SH}px` });
  const tl = gsap.timeline({ paused: true, defaults: { ease: 'power3.out' } });
  // Overshooting eases would drive blur() negative, which CSS rejects (the element
  // then keeps a stale blur). Run the filter part of such tweens on a plain ease.
  const rawFromTo = tl.fromTo.bind(tl);
  tl.fromTo = (targets, from, to, pos) => {
    if (to.filter && /back|elastic/.test(String(to.ease || ''))) {
      const { filter: f0, ...from2 } = from;
      const { filter: f1, ...to2 } = to;
      rawFromTo(targets, { filter: f0 }, { filter: f1, duration: to.duration, stagger: to.stagger, ease: 'power2.out' }, pos);
      return rawFromTo(targets, from2, to2, pos);
    }
    return rawFromTo(targets, from, to, pos);
  };
  const hooks = [];   // per-frame functions of absolute time (drift, counters, scrolling)
  const deferred = []; // layout-dependent setup, run once fonts are loaded
  const cues = [];    // { name, t, gain }
  const sfx = (name, t, gain = 1) => cues.push({ name, t: +t.toFixed(3), gain });

  // ---------- helpers ----------
  function h(tag, cls, html, parent, style) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    if (style) Object.assign(e.style, style);
    (parent || stage).appendChild(e);
    return e;
  }
  const icon = (name, size = 32, color = 'currentColor', sw = 2) =>
    `<svg class="ico" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round">${ICONS[name]}</svg>`;
  const place = (e, x = 0, y = 0, extra = {}) => gsap.set(e, { xPercent: -50, yPercent: -50, x, y, ...extra });
  // centre of `el` relative to the centre of its positioned ancestor `anc` (layout px, no transforms)
  const relCenter = (el, anc) => {
    let x = el.offsetWidth / 2, y = el.offsetHeight / 2, n = el;
    while (n && n !== anc) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }
    return [x - anc.offsetWidth / 2, y - anc.offsetHeight / 2];
  };
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const ease = (k) => gsap.parseEase('power2.inOut')(clamp(k, 0, 1));
  const lerpColor = (a, b, k) => {
    const pa = a.match(/\w\w/g).map((x) => parseInt(x, 16));
    const pb = b.match(/\w\w/g).map((x) => parseInt(x, 16));
    return `rgb(${pa.map((v, i) => Math.round(v + (pb[i] - v) * k)).join(',')})`;
  };

  function scene(start, end, parent) {
    const s = h('div', 'layer', null, parent);
    gsap.set(s, { autoAlpha: 0 });
    tl.set(s, { autoAlpha: 1 }, start);
    if (end != null) tl.set(s, { autoAlpha: 0 }, end);
    return s;
  }

  // Text with [accent] runs, split into per-character spans for blur reveals.
  // "|" starts a new line.
  function text(spec, parent, o = {}) {
    const d = h('div', 'txt', null, parent);
    Object.assign(d.style, {
      fontSize: `${o.size || 64}px`, fontWeight: o.weight || 500,
      color: o.color || INK, letterSpacing: o.ls || '-0.035em',
    });
    const chars = [], accents = [];
    const lines = spec.split('|');
    const runs = lines.flatMap((line) => {
      const host = lines.length > 1 ? h('div', 'line', null, d) : d;
      return line.split(/(\[[^\]]*\])/).filter(Boolean).map((part) => [host, part]);
    });
    runs.forEach(([host, part]) => {
      const acc = part.startsWith('[');
      const s = acc ? part.slice(1, -1) : part;
      const span = h('span', acc ? 'acc' : 'plain', null, host);
      const mine = [];
      s.split(/( )/).forEach((tok) => {
        if (tok === ' ') { span.appendChild(document.createTextNode(' ')); return; }
        if (!tok) return;
        const w = h('span', 'w', null, span);
        [...tok].forEach((c) => { const ch = h('span', 'ch', null, w); ch.textContent = c; chars.push(ch); mine.push(ch); });
      });
      if (acc) {
        const [c1, c2] = o.accent || ['3b4fe8', '6a8dff'];
        mine.forEach((ch, i) => { ch.style.color = lerpColor(c1, c2, mine.length > 1 ? i / (mine.length - 1) : 0); });
        accents.push({ span, chars: mine });
      }
    });
    if (o.align === 'left') gsap.set(d, { xPercent: 0, yPercent: -50, x: o.x || 0, y: o.y || 0 });
    else place(d, o.x || 0, o.y || 0);
    return { el: d, chars, accents };
  }

  function reveal(T, t, o = {}) {
    const st = o.stagger ?? 0.03, dur = o.dur ?? 0.55;
    const chars = o.chars || T.chars;
    tl.fromTo(chars, { opacity: 0, filter: `blur(${o.blur ?? 16}px)`, x: o.dx ?? 18, y: o.dy ?? 0 },
      { opacity: 1, filter: 'blur(0px)', x: 0, y: 0, duration: dur, ease: 'power3.out', stagger: st }, t);
    return t + st * (chars.length - 1) + dur;
  }
  function conceal(T, t, o = {}) {
    tl.to(o.chars || T.chars, {
      opacity: 0, filter: `blur(${o.blur ?? 16}px)`, x: o.dx ?? -16, duration: o.dur ?? 0.38,
      ease: 'power2.in', stagger: o.stagger ?? 0.008, immediateRender: false,
    }, t);
  }
  // enter/leave keep whatever base scale place() gave the element
  function enter(e, t, o = {}) {
    const x = gsap.getProperty(e, 'x'), y = gsap.getProperty(e, 'y');
    const s0 = e._base ?? (e._base = gsap.getProperty(e, 'scaleX'));
    tl.fromTo(e, { autoAlpha: 0, x: x + (o.dx ?? 0), y: y + (o.dy ?? 70), scale: (o.scale ?? 0.94) * s0, filter: `blur(${o.blur ?? 14}px)` },
      { autoAlpha: 1, x, y, scale: s0, filter: 'blur(0px)', duration: o.dur ?? 0.7, ease: o.ease || 'power3.out' }, t);
  }
  function leave(e, t, o = {}) {
    tl.to(e, { autoAlpha: 0, y: `+=${o.dy ?? 0}`, x: `+=${o.dx ?? 0}`, scale: (o.scale ?? 1.04) * (e._base ?? 1), filter: `blur(${o.blur ?? 14}px)`, duration: o.dur ?? 0.4, ease: 'power2.in', immediateRender: false }, t);
  }

  // ---------- reusable art ----------
  const LOGO_SVG = `
    <svg viewBox="128 120 256 296" width="100%" height="100%" overflow="visible">
      <g class="lg-leafL" style="transform-origin:250px 290px"><path d="M248 294 C226 274 178 248 154 218 C140 200 142 182 158 179 C180 175 222 207 248 260 Z" fill="#3B4FE8"/></g>
      <g class="lg-leafR" style="transform-origin:262px 270px"><path d="M264 272 C286 252 334 226 358 196 C372 178 370 160 354 157 C332 153 290 185 264 238 Z" fill="#3B4FE8"/></g>
      <g class="lg-stem" style="transform-origin:256px 402px"><rect x="246" y="205" width="20" height="197" rx="10" fill="#3B4FE8"/></g>
      <g class="lg-sun" style="transform-origin:256px 172px"><circle cx="256" cy="172" r="38" fill="#F7C84A"/><circle cx="265" cy="162" r="12" fill="#F0B820" opacity="0.4"/></g>
    </svg>`;
  function logo(parent, size) {
    const e = h('div', 'logo', LOGO_SVG, parent, { width: `${size}px`, height: `${size * 296 / 256}px` });
    const q = (c) => e.querySelector(c);
    const L = { el: e, stem: q('.lg-stem'), leafL: q('.lg-leafL'), leafR: q('.lg-leafR'), sun: q('.lg-sun') };
    gsap.set(L.stem, { svgOrigin: '256 402' });
    gsap.set(L.leafL, { svgOrigin: '250 290' });
    gsap.set(L.leafR, { svgOrigin: '262 270' });
    gsap.set(L.sun, { svgOrigin: '256 172' });
    return L;
  }
  function growLogo(L, t) {
    tl.fromTo(L.stem, { scaleY: 0 }, { scaleY: 1, duration: 0.45, ease: 'power3.out' }, t);
    tl.fromTo(L.leafL, { scale: 0, rotation: 40 }, { scale: 1, rotation: 0, duration: 0.55, ease: 'back.out(1.6)' }, t + 0.18);
    tl.fromTo(L.leafR, { scale: 0, rotation: -40 }, { scale: 1, rotation: 0, duration: 0.55, ease: 'back.out(1.6)' }, t + 0.26);
    tl.fromTo(L.sun, { scale: 0 }, { scale: 1, duration: 0.5, ease: 'back.out(2.4)' }, t + 0.4);
  }
  const CURSOR = `<svg viewBox="0 0 24 24" width="44" height="44"><path d="M4 2.5 L4 19 L8.6 14.9 L11.7 21.5 L14.6 20.2 L11.6 13.8 L18 13.6 Z" fill="#111" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/></svg>`;
  const bars = (vals, color, w = 22, gap = 12, hmax = 120) =>
    `<div style="display:flex;align-items:flex-end;gap:${gap}px;height:${hmax}px">${vals.map((v) => `<b class="bar-v" style="display:block;width:${w}px;height:${Math.round(v * hmax)}px;border-radius:${w / 2}px;background:${color};transform-origin:50% 100%"></b>`).join('')}</div>`;

  // ---------- backgrounds ----------
  const bgLight = h('div', 'layer', null, stage); bgLight.id = 'bg-light';
  const blobs = [
    { c: 'rgba(150,178,255,0.55)', s: 1100, x: pv(-260, -420), y: pv(-380, -320) },  // blue, top-left
    { c: 'rgba(160,160,250,0.55)', s: 1100, x: pv(1500, 520), y: pv(-420, -260) },   // violet, top-right
    { c: 'rgba(220,240,150,0.55)', s: 1200, x: pv(-380, -560), y: pv(520, 1180) },   // soft lime, bottom-left
    { c: 'rgba(247,200,74,0.18)', s: 900, x: pv(1300, 460), y: pv(700, 1400) },      // sprout yellow, bottom-right
  ].map((b) => {
    const e = h('div', 'blob', null, bgLight, {
      width: `${b.s}px`, height: `${b.s}px`, left: `${b.x}px`, top: `${b.y}px`,
      background: `radial-gradient(circle, ${b.c} 0%, rgba(255,255,255,0) 68%)`,
    });
    return { e, ...b };
  });
  hooks.push((t) => blobs.forEach((b, i) => {
    b.e.style.transform = `translate(${Math.sin(t * 0.21 + i * 1.7) * 70}px, ${Math.cos(t * 0.17 + i) * 50}px)`;
  }));
  const bgDark = h('div', 'layer', null, stage); bgDark.id = 'bg-dark';
  h('div', 'vignette', null, bgDark);
  gsap.set(bgDark, { autoAlpha: 0 });
  const darkOn = (a, b) => { tl.set(bgDark, { autoAlpha: 1 }, a); tl.set(bgDark, { autoAlpha: 0 }, b); };

  const content = h('div', 'layer', null, stage);
  const barTop = h('div', 'bar top'), barBot = h('div', 'bar bottom');

  // =====================================================================
  // S1 · intro — app tiles orbit a glowing sprout orb (0.0 – 2.2)
  // =====================================================================
  {
    const s = scene(0, 2.25, content);
    const ring = h('div', 'abs', null, s); place(ring);
    const tiles = [
      [`<div style="color:#fff;text-align:center">${icon('moon', 48, '#9fb0ff')}<div style="font-size:30px;font-weight:700;margin-top:6px">7h 42m</div></div>`, NAVY],
      [`<div style="width:170px"><div style="font-size:26px;font-weight:700;color:#3d2c00">Nursing</div><div style="font-size:16px;color:#6b5510;margin-top:2px">Left · 12 min</div><div style="height:12px;border-radius:6px;background:rgba(0,0,0,.12);margin-top:22px"><div style="width:62%;height:100%;border-radius:6px;background:#1a1f36"></div></div></div>`, 'linear-gradient(145deg,#ffe08a,#f7c84a)'],
      [`<svg width="170" height="80" viewBox="0 0 170 80"><path d="M5 60 C25 60 30 18 50 18 S75 62 95 62 S120 20 140 20 S160 50 165 50" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round"/></svg>`, 'linear-gradient(145deg,#5b6cff,#3343da)'],
      [`<div style="text-align:center;color:${INK}">${icon('milk', 46, BLUE)}<div style="font-size:28px;font-weight:700;margin-top:6px">120 ml</div></div>`, '#fff'],
      [`<div style="text-align:center;color:#5a1530">${icon('droplets', 46, '#8e2a4c')}<div style="font-size:26px;font-weight:700;margin-top:6px">Nappy</div></div>`, 'linear-gradient(145deg,#f6b3c9,#ed93b1)'],
      [`<div style="text-align:center;color:#06402a">${icon('soup', 46, '#06402a')}<div style="font-size:26px;font-weight:700;margin-top:6px">Banana</div></div>`, 'linear-gradient(145deg,#4fe0a6,#2dcb8a)'],
      [`<div style="color:#fff;text-align:center"><div style="font-size:16px;letter-spacing:.14em;color:#8d96c8;font-weight:600">NAP</div><div style="font-size:40px;font-weight:700;margin-top:4px">13:20</div></div>`, '#161a2b'],
      [`<div style="text-align:left;width:170px">${bars([0.5, 0.8, 0.6, 1, 0.7], BLUE, 20, 14, 70)}<div style="font-size:18px;font-weight:600;color:${INK};margin-top:10px">Reports</div></div>`, '#faf7ef'],
    ].map(([html, bg], i) => {
      const e = h('div', 'tile', html, ring, { background: bg });
      const a = (i / 8) * Math.PI * 2 - Math.PI / 2;
      return { e, a };
    });
    const orb = h('div', 'orb', icon('sprout', 120, '#fff', 2.2), s); place(orb);
    const R = pv(400, 330), RY = pv(330, 560);
    const [cx, cy] = pv([-470, -330], [-300, -640]);
    tiles.forEach(({ e, a }, i) => {
      const fx = Math.cos(a) * R, fy = Math.sin(a) * RY;
      const rot = (a * 180) / Math.PI + 90 + (i % 2 ? 8 : -8);
      // start as a tight cluster above-left, then fan out into the ring
      tl.fromTo(e, { xPercent: -50, yPercent: -50, x: cx + (i % 3) * 40, y: cy + Math.floor(i / 3) * 34, scale: 0.22, rotation: rot - 60, autoAlpha: 0, filter: 'blur(6px)' },
        { autoAlpha: 1, duration: 0.18, ease: 'none' }, 0.05 + i * 0.02);
      tl.to(e, { x: fx, y: fy, scale: 1, rotation: rot, filter: 'blur(0px)', duration: 0.9, ease: 'expo.out' }, 0.32 + i * 0.045);
      tl.to(e, { x: fx * 1.9, y: fy * 1.9, rotation: rot + 30, scale: 0.8, autoAlpha: 0, filter: 'blur(18px)', duration: 0.5, ease: 'power3.in' }, 1.72 + (i % 4) * 0.02);
    });
    tl.fromTo(ring, { rotation: -24 }, { rotation: 18, duration: 2.2, ease: 'power1.inOut' }, 0.2);
    tl.fromTo(orb, { scale: 0, filter: 'blur(10px)' }, { scale: 1, filter: 'blur(0px)', duration: 0.7, ease: 'back.out(1.7)' }, 0.42);
    tl.to(orb, { scale: 0.2, autoAlpha: 0, filter: 'blur(20px)', duration: 0.45, ease: 'power3.in' }, 1.8);
    sfx('open_hit', 0.0, 0.9);
    sfx('swell_zips', 0.12, 0.85);
  }

  // =====================================================================
  // S2 · "For too long, baby tracking has worked the same way." (2.05 – 4.42)
  // =====================================================================
  {
    const s = scene(2.05, 4.42, content);
    pv([[-640, -250, -6], [620, -260, 5], [-660, 250, 4], [640, 270, -5]],
      [[-300, -600, -6], [300, -540, 5], [-300, 560, 4], [300, 620, -5]]).forEach(([x, y, r], i) => {
      const n = h('div', 'note', '<b style="width:88%"></b><b style="width:70%"></b><b style="width:92%"></b><b style="width:60%"></b><b style="width:80%"></b>', s);
      place(n, x, y, { rotation: r });
      tl.fromTo(n, { autoAlpha: 0, filter: 'blur(12px)', scale: 0.9 }, { autoAlpha: 0.75, filter: 'blur(1.5px)', scale: 1, duration: 0.8 }, 2.1 + i * 0.08);
      tl.to(n, { x: x * 1.06, y: y * 1.06, rotation: r * 1.3, duration: 2.4, ease: 'none' }, 2.1);
    });
    const a = text('For too long,', s, { size: pv(66, 80), color: '#6b7085', y: pv(-46, -140) });
    const b = text(pv('baby tracking has worked the [same way.]', 'baby tracking has|worked the [same way.]'), s, { size: pv(66, 80), y: pv(40, 40) });
    reveal(a, 2.18, { stagger: 0.035 });
    reveal(b, 2.72, { stagger: 0.028 });
    sfx('swell_e', 2.0, 0.75);
    sfx('swell_short', 3.0, 0.6);
  }

  // =====================================================================
  // S3 · colour montage of the old way (4.42 – 6.55)
  // =====================================================================
  {
    const cuts = [
      { t: 4.42, bg: '#2b3bd1', bar: '#3c4ee6', pill: { bg: '#4b5df2', fg: '#fff', ic: 'pencil', label: 'Scribble it down', border: 'rgba(255,255,255,.25)' } },
      { t: 4.94, bg: '#14171f', bar: '#20242e', pill: { bg: 'transparent', fg: GREEN, ic: 'timer', label: 'Time it on your phone', border: GREEN } },
      { t: 5.46, bg: '#fcf0bf', bar: '#f8e08f', pill: { bg: YEL, fg: '#4a3600', ic: 'baby', label: 'Which side was it?', border: 'transparent' }, ring: true },
      { t: 6.02, bg: '#8e2a4c', bar: '#a43a61', pill: { bg: PINK, fg: '#4a0f26', ic: 'droplets', label: 'Count the nappies', border: 'transparent' } },
    ];
    cuts.forEach((c, i) => {
      const end = i < cuts.length - 1 ? cuts[i + 1].t : 6.55;
      const s = scene(c.t, end, content);
      h('div', 'layer', null, s, { background: c.bg });
      pv([-262, 0, 262], [-786, -524, -262, 0, 262, 524, 786]).forEach((y, r) => {
        const row = h('div', 'mrow', '<b></b>'.repeat(9), s, { top: `${SH / 2 + y - 60}px` });
        row.querySelectorAll('b').forEach((b) => { b.style.background = c.bar; });
        const dir = r % 2 ? 1 : -1, base = dir > 0 ? -1400 : -300 - r * 150;
        hooks.push((t) => { row.style.transform = `translateX(${base + dir * (t - 4.4) * 420}px)`; });
      });
      // clear a gap around the pill in the middle row
      const ps = pv(1, 1.3);   // pill scale
      const gap = h('div', 'abs', null, s, { width: '760px', height: '150px', background: c.bg, borderRadius: '30px' }); place(gap, 0, 0, { scale: ps });
      if (c.ring) {
        [1, 2].forEach((k) => {
          const r = h('div', 'ring', null, s, { width: `${560 + k * 90}px`, height: `${150 + k * 90}px`, borderRadius: `${75 + k * 45}px` }); place(r);
          tl.fromTo(r, { scale: 0.7 * ps, autoAlpha: 0 }, { scale: ps, autoAlpha: 1, duration: 0.45, ease: 'power2.out' }, c.t + 0.04 * k);
        });
      }
      const p = c.pill;
      const pill = h('div', 'mpill', `${icon(p.ic, 40, p.fg, 2.4)}<span>${p.label}</span>`, s, { background: p.bg, color: p.fg, border: `3px solid ${p.border}` });
      place(pill);
      tl.fromTo(pill, { scale: 0.86 * ps, filter: 'blur(8px)' }, { scale: ps, filter: 'blur(0px)', duration: 0.28, ease: 'back.out(2)' }, c.t);
      tl.fromTo(s, { scale: 1.06 }, { scale: 1, duration: end - c.t, ease: 'power2.out' }, c.t);
    });
    sfx('glitch_hit', 4.42 - 0.09, 1.0);
    sfx('rattle', 4.94 - 0.05, 0.9);
    sfx('click_ping2', 5.46 - 0.04, 0.9);
    sfx('glitch_hit', 6.02 - 0.09, 1.0);
  }

  // =====================================================================
  // S4 · "But caring for them shouldn't mean remembering everything." (6.55 – 9.4)
  // =====================================================================
  {
    const s = scene(6.55, 9.42, content);
    const a = text(pv("But looking after them shouldn't be about", "But looking after them|shouldn't be about"), s, { size: pv(66, 80), y: pv(-28, -76) });
    const b = text('remembering everything.', s, { size: pv(50, 60), color: GREY, y: pv(52, 78) });
    reveal(a, 6.62, { stagger: 0.026 });
    reveal(b, 7.95, { stagger: 0.03 });
    conceal(a, 8.85, { stagger: 0.006 });
    conceal(b, 8.95, { stagger: 0.008 });
    sfx('swell_zips2', 6.45, 0.7);
    sfx('swell_short', 8.6, 0.6);
  }

  // =====================================================================
  // S5 · "It should be about [understanding] them." (9.4 – 11.3)
  // =====================================================================
  {
    const s = scene(9.4, 11.32, content);
    const a = text(pv('It should be about [understanding] them.', 'It should be about|[understanding] them.'), s, { size: pv(72, 88), accent: ['ffffff', 'ffffff'] });
    const acc = a.accents[0].span;
    const box = h('div', 'hl-box', null, acc, { width: 'calc(100% + 12px)', transformOrigin: '0 50%' });
    acc.classList.add('hl-wrap');
    const pre = a.chars.length - a.accents[0].chars.length - 'them.'.length;
    const plain1 = a.chars.slice(0, pre), accC = a.accents[0].chars, tail = a.chars.slice(pre + accC.length);
    reveal(a, 9.48, { chars: plain1, stagger: 0.03 });
    const t0 = 9.48 + 0.03 * plain1.length;
    reveal(a, t0, { chars: accC, stagger: 0.035 });
    tl.fromTo(box, { scaleX: 0 }, { scaleX: 1, duration: 0.035 * accC.length + 0.25, ease: 'power2.out' }, t0 - 0.05);
    reveal(a, t0 + 0.035 * accC.length + 0.05, { chars: tail, stagger: 0.03 });
    tl.to(a.el, { scale: 1.04, duration: 1.6, ease: 'none' }, 9.6);
    conceal(a, 11.0, { stagger: 0.004, dur: 0.3 });
    tl.to(box, { autoAlpha: 0, filter: 'blur(10px)', duration: 0.3, ease: 'power2.in' }, 11.05);
    sfx('swell_short', 9.25, 0.5);
    sfx('click_ping', t0 - 0.08, 1.0);
    sfx('sparkle_zip', t0 + 0.3, 0.6);
  }

  // =====================================================================
  // S6 · "What if every feed and nap was…" + feature cards (11.3 – 16.6)
  // =====================================================================
  {
    const s = scene(11.3, 16.75, content);
    tl.fromTo([barTop, barBot], { height: 0 }, { height: pv(112, 190), duration: 0.45, ease: 'power3.inOut' }, 11.22);
    tl.to([barTop, barBot], { height: 0, duration: 0.5, ease: 'power3.inOut' }, 16.4);

    const q = text(pv('What if every [feed and nap] was', 'What if every|[feed and nap] was'), s, { size: pv(72, 88), y: 0 });
    const br = h('div', 'bracket', '<i class="tl"></i><i class="tr"></i><i class="bl"></i><i class="br"></i>', s);
    const qEnd = reveal(q, 11.5, { stagger: 0.032 });
    // bracket hugs the text as it types on (measured after layout, see init())
    tl.fromTo(br, { autoAlpha: 0, scale: 1.25 }, { autoAlpha: 1, scale: 1, duration: 0.35, ease: 'power3.out' }, 11.42);
    deferred.push(() => {
      const padX = 26, padY = 16;
      const full = q.el.offsetWidth + padX * 2, start = 150;
      gsap.set(br, { xPercent: 0, yPercent: -50, x: -full / 2, y: 0, width: full, height: q.el.offsetHeight + padY * 2 });
      // two centred lines don't type on left-to-right, so the portrait frame stays full size
      if (!PORT) tl.fromTo(br, { width: start }, { width: full, duration: qEnd - 11.5 - 0.25, ease: 'none' }, 11.5);
    });
    conceal(q, 13.02, { stagger: 0.005 });
    tl.to(br, { autoAlpha: 0, scale: 0.9, filter: 'blur(10px)', duration: 0.3, ease: 'power2.in' }, 13.05);
    sfx('swell_e', 11.2, 0.6);

    // top line swaps
    const lines = [
      ['logged in [one tap,]', 13.3], ['[easy] to understand,', 14.2], ['even [predictable,]', 15.1], ['one day [at a time?]', 15.98],
    ].map(([spec, t], i, arr) => {
      const T = text(spec, s, { size: pv(62, 76), y: pv(-290, -620) });
      reveal(T, t, { stagger: 0.026 });
      if (i < arr.length - 1) conceal(T, arr[i + 1][0] ? arr[i + 1][1] - 0.24 : t + 1, { stagger: 0.004, dur: 0.24 });
      else conceal(T, 16.45, { stagger: 0.004, dur: 0.28 });
      return T;
    });

    // card A — quick log
    const A = h('div', 'card', `
      <div style="padding:30px 32px">
        <div class="label" style="color:${BLUE}">Quick log</div>
        <div style="font-size:32px;font-weight:600;letter-spacing:-.02em;margin-top:8px;color:${INK}">Nappy change</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:22px">
          <div class="chip">${icon('droplets', 22, '#5b8cff')}Pee</div><div class="chip">Poo</div>
          <div class="chip" id="chip-mixed">Mixed</div><div class="chip">Dry</div>
        </div>
      </div>`, s, { width: '440px', height: '300px' });
    // landscape: three cards in a row; portrait: stacked, a little larger
    const sc = pv(1, 1.15);
    const [ax, ay] = pv([-520, 70], [0, -290]);
    place(A, ax, ay, { scale: sc });
    const mixed = A.querySelector('#chip-mixed');
    const cur = h('div', 'cursor', CURSOR, s); place(cur, -380, 330);
    enter(A, 13.35, { dy: 90 });
    // cursor tip sits ~18px left / 20px up from the element centre
    const tapA = ([tx, ty]) => {
      tl.fromTo(cur, { autoAlpha: 0, x: tx + 318, y: ty + 238 }, { autoAlpha: 1, x: tx + 18, y: ty + 20, duration: 0.5, ease: 'power3.out' }, 13.5);
      tl.to(cur, { scale: 0.82, duration: 0.08, yoyo: true, repeat: 1, ease: 'power1.inOut' }, 13.95);
      tl.to(cur, { autoAlpha: 0, x: tx + 58, y: ty + 78, duration: 0.3 }, 14.4);
    };
    if (PORT) deferred.push(() => { const [rx, ry] = relCenter(mixed, A); tapA([ax + rx * sc, ay + ry * sc]); });
    else tapA([-618, 142]);
    tl.to(mixed, { backgroundColor: BLUE, color: '#fff', duration: 0.12, ease: 'none' }, 13.97);
    sfx('ping1', 13.32, 0.8);
    sfx('dclick', 13.95 - 0.1, 0.8);

    // card B — sleep this week
    const B = h('div', 'card navy', `
      <div style="padding:30px 32px;height:100%;display:flex;flex-direction:column">
        <div style="display:flex;justify-content:space-between;align-items:baseline">
          <div class="label" style="color:#8d96c8">Sleep · this week</div>
          <div style="font-size:30px;font-weight:700">13h 20m</div>
        </div>
        <div style="margin-top:auto">${bars([0.55, 0.7, 0.62, 0.86, 0.74, 0.95, 0.82], 'linear-gradient(180deg,#f7c84a,#5b6cff)', 34, 22, 150)}</div>
        <div style="display:flex;gap:22px;margin-top:10px;color:#6f78a8;font-size:15px;font-weight:600">${'MTWTFSS'.split('').map((d) => `<span style="width:34px;text-align:center">${d}</span>`).join('')}</div>
      </div>`, s, { width: '440px', height: '300px' });
    place(B, 0, pv(70, 85), { scale: sc });
    enter(B, 14.25, { dy: 90 });
    tl.fromTo(B.querySelectorAll('.bar-v'), { scaleY: 0 }, { scaleY: 1, duration: 0.6, ease: 'power3.out', stagger: 0.05 }, 14.4);
    sfx('ping2', 14.22, 0.8);

    // card C — nap window
    const C = h('div', 'card yellow', `
      <div style="padding:30px 32px;color:#3d2c00">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div class="label" style="color:#6b5510">Nap window</div>${icon('moon-star', 30, '#3d2c00')}
        </div>
        <div style="font-size:84px;font-weight:700;letter-spacing:-.04em;margin-top:12px;line-height:1">13:20</div>
        <div style="font-size:22px;font-weight:600;margin-top:10px;color:#6b5510">Next nap in ~40 min</div>
        <div style="height:14px;border-radius:7px;background:rgba(0,0,0,.12);margin-top:22px"><div class="napfill" style="width:0;height:100%;border-radius:7px;background:#1a1f36"></div></div>
      </div>`, s, { width: '440px', height: '300px' });
    place(C, pv(520, 0), pv(70, 460), { scale: sc });
    enter(C, 15.15, { dy: 90 });
    tl.fromTo(C.querySelector('.napfill'), { width: '0%' }, { width: '72%', duration: 1.0, ease: 'power2.out' }, 15.3);
    sfx('ping3', 15.12, 0.75);

    // collapse into the yellow card, which melts into the logo glow
    leave(A, 15.85, pv({ dx: 140, blur: 16, scale: 0.85, dur: 0.45 }, { dy: 140, blur: 16, scale: 0.85, dur: 0.45 }));
    leave(B, 15.9, pv({ dx: 80, blur: 16, scale: 0.85, dur: 0.45 }, { dy: -60, blur: 16, scale: 0.85, dur: 0.45 }));
    tl.to(C, { x: 0, y: 40, scale: 1.08 * sc, duration: 0.6, ease: 'power3.inOut' }, 15.85);
    tl.to(C, { scale: 0.55 * sc, borderRadius: '50%', filter: 'blur(40px)', autoAlpha: 0, duration: 0.5, ease: 'power2.in' }, 16.42);
    sfx('swell_f', 15.6, 0.55);
  }

  // =====================================================================
  // S7 · logo reveal (16.6 – 18.7)
  // =====================================================================
  {
    const s = scene(16.55, 18.75, content);
    const glow = h('div', 'glow', null, s, { width: '900px', height: '900px', background: 'radial-gradient(circle, rgba(247,200,74,0.45) 0%, rgba(240,245,170,0.25) 35%, rgba(255,255,255,0) 68%)' });
    place(glow);
    tl.fromTo(glow, { scale: 0.4, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 0.8, ease: 'power2.out' }, 16.5);
    const wm = h('div', 'wordmark', 'Sprout', s, { fontSize: '190px' });
    const L = logo(s, 200); place(L.el, 0, -6);
    growLogo(L, 16.62);
    deferred.push(() => {
      const ww = wm.offsetWidth, gap = 40, lw = 200;
      const total = lw + gap + ww;
      place(wm, -total / 2 + lw + gap + ww / 2, 8);
      tl.to(L.el, { x: -total / 2 + lw / 2, duration: 0.7, ease: 'power3.inOut' }, 17.12);
      tl.fromTo(wm, { autoAlpha: 0, filter: 'blur(24px)', x: -total / 2 + lw + gap + ww / 2 - 120 }, { autoAlpha: 1, filter: 'blur(0px)', x: -total / 2 + lw + gap + ww / 2, duration: 0.75, ease: 'power3.out' }, 17.25);
    });
    tl.to(s, { scale: 1.05, duration: 2.1, ease: 'none' }, 16.6);
    tl.to([L.el, wm, glow], { autoAlpha: 0, filter: 'blur(18px)', duration: 0.38, ease: 'power2.in' }, 18.35);
    sfx('impact', 16.5, 0.85);
  }

  // =====================================================================
  // S8 · "We turn sleepless guesswork into calm, clear answers." (18.7 – 23.4)
  // =====================================================================
  {
    const s = scene(18.7, 20.75, content);
    const a = text(pv('We turn sleepless [guesswork]', 'We turn sleepless|[guesswork]'), s, { size: pv(66, 80), y: pv(-340, -600) });
    reveal(a, 18.85, { stagger: 0.03 });
    conceal(a, 20.3, { stagger: 0.005 });
    const ph = h('div', 'phone', `
      <div class="screen">
        <div class="app-head">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <div style="width:44px;height:44px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-weight:700">O</div>
            <div style="font-size:28px;font-weight:700">Sprout</div><div style="width:44px"></div>
          </div>
          <div style="margin-top:22px;background:rgba(255,255,255,.14);border-radius:20px;padding:18px 20px">
            <div style="font-size:16px;opacity:.85">${icon('moon', 16, '#fff')} Nap window</div>
            <div style="font-size:24px;font-weight:700;margin-top:4px">In ~40 min · 13:20</div>
          </div>
        </div>
        <div class="app-tiles">
          <div class="app-tile" style="background:${BLUE};color:#fff"><div class="k">Sleep</div><div class="v">7h 42m</div><div class="s">last night</div></div>
          <div class="app-tile" style="background:${YEL};color:#3d2c00"><div class="k">Nursing</div><div class="v">2h ago</div><div class="s">last session</div></div>
          <div class="app-tile" style="background:${GREEN};color:#fff"><div class="k">Solids</div><div class="v">12:00</div><div class="s">lunch</div></div>
          <div class="app-tile" style="background:${PINK};color:#5a1530"><div class="k">Nappy</div><div class="v">3h ago</div><div class="s">mixed</div></div>
        </div>
        <div style="padding:0 22px">
          <div style="font-size:18px;font-weight:700;color:${INK};margin:6px 0 12px">Today</div>
          ${['07:02 · Woke up', '07:30 · Nursing · L 12m', '09:15 · Nap · 1h 05m'].map((r) => `<div style="background:#fff;border-radius:16px;padding:14px 16px;margin-bottom:10px;font-size:17px;font-weight:500;color:#4a5070;box-shadow:0 2px 8px rgba(26,35,90,.06)">${r}</div>`).join('')}
        </div>
      </div>`, s);
    const phY = pv([400, 330], [330, 250]);
    gsap.set(ph, { xPercent: -50, yPercent: -50, x: pv(30, 0), y: phY[0], scale: pv(1.45, 1.4), transformPerspective: 2400, rotationX: pv(40, 32), rotationZ: pv(-18, -12), rotationY: 6 });
    tl.fromTo(ph, { y: pv(1100, 1500), autoAlpha: 0, filter: 'blur(14px)' }, { y: phY[0], autoAlpha: 1, filter: 'blur(0px)', duration: 1.1, ease: 'expo.out' }, 18.72);
    tl.to(ph, { y: phY[1], rotationX: pv(34, 26), rotationZ: pv(-14, -8), duration: 1.6, ease: 'none' }, 19.5);
    tl.to(ph, { y: -260, autoAlpha: 0, filter: 'blur(20px)', duration: 0.55, ease: 'power3.in' }, 20.2);
    sfx('swell_g', 18.55, 0.6);

    const s2 = scene(20.6, 23.45, content);
    // landscape: "into" sits left of the line; portrait: above it
    const pre = text('into', s2, { size: pv(56, 60), color: GREY, y: pv(0, -80) });
    const b = text('calm, clear [answers.]', s2, { size: pv(76, 84), weight: 600, y: pv(0, 20) });
    if (!PORT) deferred.push(() => {
      const wp = pre.el.offsetWidth, wb = b.el.offsetWidth, gap = 24;
      const total = wp + gap + wb;
      gsap.set(pre.el, { x: -total / 2 + wp / 2 }); gsap.set(b.el, { x: -total / 2 + wp + gap + wb / 2 });
    });
    reveal(pre, 20.66, { stagger: 0.04 });
    reveal(b, 20.85, { stagger: 0.03 });
    const spots = pv(
      [[-640, -250], [-300, -320], [330, -300], [640, -230], [-660, 240], [-270, 300], [310, 310], [660, 230]],
      [[-320, -600], [-60, -420], [300, -620], [330, -340], [-330, 340], [-60, 560], [300, 600], [320, 320]]);
    const minis = [
      ['moon', NAVY, '#9fb0ff', -8], ['milk', '#fff', BLUE, 6], ['chart-column', 'linear-gradient(145deg,#5b6cff,#3343da)', '#fff', -5],
      ['calendar-days', '#161a2b', YEL, 8], ['soup', 'linear-gradient(145deg,#4fe0a6,#2dcb8a)', '#06402a', 7], ['droplets', 'linear-gradient(145deg,#f6b3c9,#ed93b1)', '#8e2a4c', -6],
      ['sparkles', 'linear-gradient(145deg,#ffe08a,#f7c84a)', '#3d2c00', 5], ['timer', '#faf7ef', INK, -7],
    ].map((m, i) => [...spots[i], ...m]);
    // pops land on the pulses in "swell_pulses" (≈ every 0.105s from 1.0s into the clip)
    const pulse0 = 20.55 + 1.0;
    minis.forEach(([x, y, ic, bg, fg, r], i) => {
      const m = h('div', 'mini', `${icon(ic, 46, fg, 2.2)}<div class="badge">${icon('check', 18, '#fff', 3)}</div>`, s2, { background: bg });
      place(m, x, y, { rotation: r });
      tl.fromTo(m, { autoAlpha: 0, scale: 0.5, filter: 'blur(12px)', x: x * 0.7, y: y * 0.7 }, { autoAlpha: 1, scale: 1, filter: 'blur(0px)', x, y, duration: 0.5, ease: 'back.out(1.8)' }, pulse0 - 0.5 + i * 0.105);
      tl.to(m, { x: x * 1.04 + (i % 2 ? 10 : -10), y: y * 1.05, duration: 2, ease: 'none' }, 21.3);
      tl.to(m, { autoAlpha: 0, x: x * 1.5, y: y * 1.5, filter: 'blur(16px)', duration: 0.4, ease: 'power2.in' }, 23.0 + (i % 3) * 0.02);
    });
    conceal(pre, 23.0); conceal(b, 23.02, { stagger: 0.005 });
    sfx('swell_pulses', 20.55, 0.75);
  }

  // =====================================================================
  // S9 · dark — "Track everything": Sleep. Feeds. Nappies. All in one tap. (23.4 – 28.6)
  // =====================================================================
  {
    darkOn(23.42, 28.62);
    const s = scene(23.42, 28.62, content);
    const tag = h('div', 'tag', `${icon('moon', 34, '#3d2c00', 2.4)}Track everything`, s, { background: YEL, color: '#3d2c00' });
    place(tag);
    tl.fromTo(tag, { scale: 1.5, filter: 'blur(14px)', autoAlpha: 0 }, { scale: 1.3, filter: 'blur(0px)', autoAlpha: 1, duration: 0.45 }, 23.48);
    tl.to(tag, { y: pv(-360, -720), scale: 0.85, duration: 0.6, ease: 'power3.inOut' }, 24.0);
    const DA = ['6f80ff', 'a9b8ff'];
    const words = [['[Sleep.]', 24.35], ['[Feeds.]', 25.15], ['[Nappies.]', 25.95], ['All in [one tap.]', 26.75]].map(([spec, t], i, arr) => {
      const T = text(spec, s, { size: 92, weight: 600, color: '#fff', y: pv(-200, -520), accent: DA });
      reveal(T, t, { stagger: 0.04 });
      conceal(T, i < arr.length - 1 ? arr[i + 1][1] - 0.25 : 28.2, { stagger: 0.01, dur: 0.25 });
      return T;
    });
    const rowY = pv(150, -10), rowS = pv(1, 1.2);
    const row = h('div', 'abs', null, s, { width: '0px', height: '0px' }); place(row, 0, rowY, { scale: rowS });
    const W = [330, 330, 330, 330, 240], GAP = 30;
    const full = W.reduce((a, b) => a + b) + GAP * (W.length - 1);
    const xs = []; let acc = -full / 2;
    W.forEach((w) => { xs.push(acc + w / 2); acc += w + GAP; });
    // landscape: one row that re-centres as cards arrive; portrait: 2x2 grid + ring card below
    const pos = PORT ? [[-180, -140], [180, -140], [-180, 140], [180, 140], [0, 410]] : xs.map((x) => [x, 0]);
    const mk = (cls, html, i) => { const c = h('div', `card on-dark ${cls}`, html, row, { width: `${W[i]}px`, height: '240px' }); place(c, ...pos[i]); return c; };
    const c1 = mk('', `<div style="padding:26px 28px;color:${INK}">
        <div style="display:flex;justify-content:space-between;align-items:center"><div class="label" style="color:${BLUE}">Sleep · live</div>${icon('moon', 26, BLUE)}</div>
        <div id="sleep-timer" style="font-size:56px;font-weight:700;letter-spacing:-.03em;margin-top:22px;font-variant-numeric:tabular-nums">00:42:13</div>
        <div style="display:flex;gap:10px;margin-top:20px"><div class="chip" style="height:46px;flex:1;font-size:18px;background:${BLUE};color:#fff">Pause</div><div class="chip" style="height:46px;flex:1;font-size:18px">Night</div></div>
      </div>`, 0);
    const c2 = mk('navy', `<div style="padding:26px 28px">
        <div class="label" style="color:#8d96c8">Nursing</div>
        <div style="display:flex;gap:18px;margin-top:22px">
          <div style="flex:1;border-radius:20px;padding:16px;background:${BLUE};text-align:center"><div style="font-size:30px;font-weight:700">L</div><div style="font-size:20px;font-weight:600;opacity:.9" id="nurse-l">12:04</div></div>
          <div style="flex:1;border-radius:20px;padding:16px;background:#1e2550;text-align:center"><div style="font-size:30px;font-weight:700;color:#8d96c8">R</div><div style="font-size:20px;font-weight:600;color:#8d96c8">8:30</div></div>
        </div>
      </div>`, 1);
    const c3 = mk('cream', `<div style="padding:26px 28px;color:${INK}">
        <div style="display:flex;justify-content:space-between;align-items:center"><div class="label" style="color:#b0862a">Bottle</div>${icon('milk', 26, '#b0862a')}</div>
        <div style="font-size:56px;font-weight:700;letter-spacing:-.03em;margin-top:18px">120<span style="font-size:28px;color:${GREY}"> ml</span></div>
        <div style="height:14px;border-radius:7px;background:#ece5d2;margin-top:22px"><div class="bottlefill" style="width:0;height:100%;border-radius:7px;background:${YEL}"></div></div>
        <div style="font-size:17px;color:${GREY};margin-top:10px;font-weight:500">Formula · 15:40</div>
      </div>`, 2);
    const c4 = mk('', `<div style="padding:26px 28px;color:${INK}">
        <div class="label" style="color:#c2477a">Nappy</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:20px">
          <div class="chip" style="height:54px;font-size:19px">Pee</div><div class="chip" style="height:54px;font-size:19px">Poo</div>
          <div class="chip" id="nappy-mixed" style="height:54px;font-size:19px">Mixed</div><div class="chip" style="height:54px;font-size:19px">Dry</div>
        </div>
      </div>`, 3);
    const c5 = mk('', `<div style="padding:24px;display:flex;flex-direction:column;align-items:center;color:${INK}">
        <svg width="130" height="130" viewBox="0 0 130 130"><circle cx="65" cy="65" r="54" fill="none" stroke="#eceef6" stroke-width="13"/><circle id="ring-arc" cx="65" cy="65" r="54" fill="none" stroke="${GREEN}" stroke-width="13" stroke-linecap="round" stroke-dasharray="339.3" stroke-dashoffset="339.3" transform="rotate(-90 65 65)"/><text x="65" y="76" text-anchor="middle" font-family="Inter" font-weight="700" font-size="34" fill="${INK}" id="ring-num">0</text></svg>
        <div style="font-size:18px;font-weight:600;color:${GREY};margin-top:8px">logs today</div>
      </div>`, 4);
    const cards = [c1, c2, c3, c4, c5], times = [24.38, 25.18, 25.98, 26.78, 27.3];
    const widthOf = (k) => W.slice(0, k).reduce((a, b) => a + b) + GAP * (k - 1);
    cards.forEach((c, i) => {
      enter(c, times[i], { dy: 60, blur: 16, scale: 0.9, dur: 0.6 });
      if (!PORT) tl.to(row, { x: (full - widthOf(i + 1)) / 2, duration: 0.6, ease: 'power3.inOut' }, times[i] - 0.05);
    });
    if (!PORT) gsap.set(row, { x: (full - widthOf(1)) / 2 });
    tl.fromTo(c3.querySelector('.bottlefill'), { width: '0%' }, { width: '80%', duration: 0.8, ease: 'power2.out' }, 26.1);
    const chipMixed = c4.querySelector('#nappy-mixed');
    tl.to(chipMixed, { backgroundColor: PINK, color: '#4a0f26', duration: 0.12, ease: 'none' }, 27.0);
    const cur = h('div', 'cursor', CURSOR.replace('#111', '#fff').replace('stroke="#fff"', 'stroke="#111"'), s); place(cur);
    // point at the "Mixed" chip of the nappy card (landscape: once the row has re-centred for 4 cards)
    const tapMixed = ([tx, ty]) => {
      tl.fromTo(cur, { autoAlpha: 0, x: tx + 260, y: ty + 254 }, { autoAlpha: 1, x: tx + 18, y: ty + 20, duration: 0.45, ease: 'power3.out' }, 26.55);
      tl.to(cur, { scale: 0.82, duration: 0.07, yoyo: true, repeat: 1 }, 26.98);
      tl.to(cur, { autoAlpha: 0, duration: 0.3 }, 27.5);
    };
    if (PORT) {
      deferred.push(() => {
        const [rx, ry] = relCenter(chipMixed, c4);
        tapMixed([(pos[3][0] + rx) * rowS, rowY + (pos[3][1] + ry) * rowS]);
      });
    } else tapMixed([xs[3] + (full - widthOf(4)) / 2 - 72, 150 + 36]);
    const timerEl = c1.querySelector('#sleep-timer'), nl = c2.querySelector('#nurse-l');
    const arc = c5.querySelector('#ring-arc'), num = c5.querySelector('#ring-num');
    hooks.push((t) => {
      const sec = 42 * 60 + 13 + Math.max(0, Math.floor((t - 24.4) * 1));
      timerEl.textContent = `00:${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`;
      const ns = 12 * 60 + 4 + Math.max(0, Math.floor(t - 25.2));
      nl.textContent = `${Math.floor(ns / 60)}:${String(ns % 60).padStart(2, '0')}`;
      const k = ease((t - 27.4) / 0.9), n = Math.round(14 * k);
      num.textContent = n; arc.setAttribute('stroke-dashoffset', (339.3 * (1 - (n / 16))).toFixed(1));
    });
    tl.to(row, { autoAlpha: 0, filter: 'blur(18px)', scale: 0.95 * rowS, duration: 0.4, ease: 'power2.in' }, 28.18);
    tl.to(tag, { autoAlpha: 0, filter: 'blur(14px)', duration: 0.3, ease: 'power2.in' }, 28.2);
    sfx('open_hit', 23.42, 0.8);
    sfx('swell_h', 23.5, 0.55);
    sfx('ping4', 24.35, 0.7);
    sfx('ping1', 25.15, 0.7);
    sfx('ping2', 25.95, 0.7);
    sfx('dclick2', 26.98 - 0.07, 0.9);
    sfx('chime', 27.33 - 0.12, 0.7);
  }

  // =====================================================================
  // S10 · Reports — Spot the patterns. See the trends. Export in one tap. (28.6 – 34.4)
  // =====================================================================
  {
    const s = scene(28.62, 34.45, content);
    const tag = h('div', 'tag', `${icon('chart-column', 34, '#fff', 2.4)}Reports`, s, { background: BLUE, color: '#fff' });
    place(tag);
    tl.fromTo(tag, { scale: 1.6, filter: 'blur(14px)', autoAlpha: 0 }, { scale: 1.4, filter: 'blur(0px)', autoAlpha: 1, duration: 0.45 }, 28.66);
    tl.to(tag, { y: pv(-400, -740), scale: 0.8, duration: 0.6, ease: 'power3.inOut' }, 29.1);
    const heads = [['Spot the [patterns.]', 29.55], ['See the [trends.]', 30.95], ['Export in [one tap.]', 32.15]].map(([spec, t], i, arr) => {
      const T = text(spec, s, { size: 84, weight: 600, y: pv(-268, -580) });
      reveal(T, t, { stagger: 0.032 });
      conceal(T, i < arr.length - 1 ? arr[i + 1][1] - 0.25 : 33.95, { stagger: 0.006, dur: 0.25 });
      return T;
    });
    // landscape: three columns; portrait: the same three blocks stacked
    const panel = h('div', 'card', `
      <div style="display:flex;flex-direction:${pv('row', 'column')};gap:28px;padding:28px;height:100%">
        <div style="${pv('width:420px', 'height:290px;flex:none')};border-radius:22px;background:${NAVY};color:#fff;padding:28px;display:flex;flex-direction:column">
          <div style="display:flex;justify-content:space-between;align-items:center"><div class="label" style="color:#8d96c8">Last night</div><div style="display:flex;align-items:center;gap:8px;font-size:17px;font-weight:600;color:${YEL}"><span style="width:10px;height:10px;border-radius:50%;background:${YEL}"></span>Asleep</div></div>
          <div style="font-size:64px;font-weight:700;letter-spacing:-.03em;margin-top:18px">7h 42m</div>
          <div style="margin-top:auto;display:flex;gap:6px;height:44px;align-items:stretch">
            ${[[3, '#5b6cff'], [1, '#2b3270'], [4, '#5b6cff'], [0.6, YEL], [3, '#5b6cff'], [1, '#2b3270'], [2.5, '#5b6cff']].map(([f, c]) => `<b class="seg" style="flex:${f};border-radius:8px;background:${c};transform-origin:0 50%"></b>`).join('')}
          </div>
          <div style="display:flex;justify-content:space-between;margin-top:10px;font-size:15px;color:#6f78a8;font-weight:600"><span>19:00</span><span>01:00</span><span>06:42</span></div>
        </div>
        <div style="${pv('width:400px', 'height:390px;flex:none')};padding:12px 4px;display:flex;flex-direction:column">
          <div class="label" style="color:#a3a8c3">This week</div>
          ${[['moon', 'Sleep', '13h 20m', BLUE], ['milk', 'Feeds', '8 / day', '#b0862a'], ['droplets', 'Nappies', '6 / day', '#c2477a']].map(([ic, k, v, c]) => `
            <div class="rrow" style="display:flex;align-items:center;gap:16px;margin-top:16px;padding:16px 18px;border-radius:18px;background:#f4f5fa">
              <div style="width:44px;height:44px;border-radius:12px;background:#fff;display:flex;align-items:center;justify-content:center">${icon(ic, 24, c)}</div>
              <div style="font-size:22px;font-weight:600;color:${INK}">${k}</div><div style="margin-left:auto;font-size:22px;font-weight:700;color:${INK}">${v}</div>
            </div>`).join('')}
          <div id="export-btn" style="margin-top:auto;height:62px;border-radius:16px;background:#e8eaf3;color:#4a5070;display:flex;align-items:center;justify-content:center;gap:12px;font-size:22px;font-weight:600">${icon('download', 24, 'currentColor')}<span id="export-label">Export CSV</span></div>
        </div>
        <div style="flex:1;border-radius:22px;background:#f7f8fc;padding:28px;display:flex;flex-direction:column">
          <div class="label" style="color:#a3a8c3">Sleep consistency</div>
          <div style="font-size:84px;font-weight:700;letter-spacing:-.04em;color:${INK};margin-top:6px;line-height:1.1"><span id="pct">0</span><span style="color:${GREY}">%</span></div>
          <div style="margin-top:auto">${bars([0.35, 0.45, 0.42, 0.6, 0.7, 0.82, 1], BLUE, 38, 18, 150)}</div>
        </div>
      </div>`, s, pv({ width: '1400px', height: '540px' }, { width: '940px', height: '1110px' }));
    const [pX, pY, pS] = pv([0, 160, 1], [0, 115, 0.92]);
    place(panel, pX, pY, { scale: pS });
    enter(panel, 29.25, { dy: 120, blur: 18, scale: 0.96, dur: 0.8 });
    tl.fromTo(panel.querySelectorAll('.seg'), { scaleX: 0 }, { scaleX: 1, duration: 0.5, stagger: 0.07, ease: 'power2.out' }, 29.7);
    const rows = panel.querySelectorAll('.rrow');
    [30.0, 31.0, 31.6].forEach((t, i) => {
      tl.fromTo(rows[i], { backgroundColor: '#f4f5fa' }, { backgroundColor: '#e7eaff', duration: 0.2, yoyo: true, repeat: 1, repeatDelay: 0.4 }, t);
    });
    const vb = panel.querySelectorAll('.bar-v');
    tl.fromTo(vb, { scaleY: 0.05 }, { scaleY: 1, duration: 1.4, stagger: 0.12, ease: 'power2.out' }, 29.8);
    const pct = panel.querySelector('#pct');
    hooks.push((t) => {
      const k1 = ease((t - 29.8) / 1.2), k2 = ease((t - 31.0) / 1.0);
      pct.textContent = Math.round(64 * k1 + 28 * k2);
    });
    const btn = panel.querySelector('#export-btn'), lab = panel.querySelector('#export-label');
    const cur = h('div', 'cursor', CURSOR, s); place(cur);
    const tapExport = ([tx, ty]) => {
      tl.fromTo(cur, { autoAlpha: 0, x: tx + 372, y: ty + 138 }, { autoAlpha: 1, x: tx, y: ty, duration: 0.6, ease: 'power3.out' }, 32.3);
      tl.to(cur, { scale: 0.82, duration: 0.07, yoyo: true, repeat: 1 }, 32.95);
      tl.to(cur, { autoAlpha: 0, duration: 0.3 }, 33.6);
    };
    if (PORT) {
      deferred.push(() => {
        const [rx, ry] = relCenter(btn, panel);
        tapExport([pX + (rx + 30) * pS + 18, pY + ry * pS + 20]);
      });
    } else tapExport([8, 382]);
    tl.to(btn, { backgroundColor: BLUE, color: '#fff', scale: 0.97, duration: 0.1, ease: 'none' }, 32.97);
    tl.to(btn, { scale: 1, duration: 0.2 }, 33.08);
    hooks.push((t) => {
      const done = t >= 33.1;
      if (lab.dataset.done !== String(done)) {
        lab.dataset.done = String(done);
        lab.innerHTML = done ? `Exported ${icon('check', 22, 'currentColor', 3)}` : 'Export CSV';
      }
    });
    tl.to(panel, { autoAlpha: 0, y: '+=60', filter: 'blur(18px)', duration: 0.42, ease: 'power2.in' }, 33.95);
    tl.to(tag, { autoAlpha: 0, filter: 'blur(14px)', duration: 0.3 }, 33.98);
    sfx('swell_long', 28.45, 0.55);
    sfx('click_ping', 29.25 - 0.08, 0.8);
    sfx('click_ping2', 30.95 - 0.04, 0.7);
    sfx('dclick', 32.95 - 0.1, 0.9);
    sfx('ping3', 33.1, 0.55);
  }

  // =====================================================================
  // S11 · Premium — turn a week of logs into a tailored routine (34.4 – 39.3)
  // =====================================================================
  {
    const s = scene(34.42, 39.4, content);
    const ly = pv(-330, -600), lz = pv(64, 72);
    const l1 = text('With Sprout [Premium],', s, { size: lz, y: ly });
    const l2 = text('turn a week of [logs]', s, { size: lz, y: ly });
    const l3 = text(pv('into a [tailored daily routine.]', 'into a [tailored]|[daily routine.]'), s, { size: lz, y: pv(ly, ly + 40) });
    reveal(l1, 34.5, { stagger: 0.032 }); conceal(l1, 35.62, { stagger: 0.005 });
    reveal(l2, 35.85, { stagger: 0.03 }); conceal(l2, 36.75, { stagger: 0.005 });
    reveal(l3, 36.95, { stagger: 0.028 });
    conceal(l3, 38.95, { stagger: 0.005 });
    const doc = h('div', 'card', `
      <div style="padding:30px 34px">
        <div class="label" style="color:${BLUE}">Activity log</div>
        <div style="font-size:30px;font-weight:700;margin-top:6px;color:${INK}">Last 7 days</div>
        <div style="font-size:17px;color:${GREY};margin-top:2px">142 entries</div>
        ${['07:02  Woke up', '07:30  Nursing · L 12m', '09:15  Nap · 1h 05m', '12:00  Solids · banana', '13:20  Nap · 1h 30m', '19:00  Bedtime'].map((r) => `<div style="font-size:18px;color:#4a5070;font-weight:500;padding:9px 0;border-bottom:1px solid #eef0f6;font-variant-numeric:tabular-nums">${r}</div>`).join('')}
      </div>`, s, { width: '400px', height: '520px' });
    place(doc, 0, pv(90, 80), { scale: pv(1, 1.3) });
    enter(doc, 34.65, { dy: 120, dur: 0.8 });
    tl.to(doc, { rotation: -3, scale: 1.02 * doc._base, duration: 1.6, ease: 'none' }, 35.3);
    tl.to(doc, { scale: 0.6 * doc._base, autoAlpha: 0, filter: 'blur(22px)', rotation: 0, duration: 0.45, ease: 'power2.in' }, 36.65);
    // schedule grid
    const cols = ['Morning', 'Midday', 'Afternoon', 'Evening'];
    const cells = [
      [['Wake', '07:00', 'blue'], ['Feed', '07:30', 'yel'], ['Nap 1', '09:15', 'dark']],
      [['Solids', '12:00', 'yel'], ['Nap 2', '13:20', 'dark'], ['Feed', '15:00', 'blue']],
      [['Play', '15:40', 'out'], ['Nap 3', '16:30', 'dark'], ['Bottle', '17:30', 'yel']],
      [['Bath', '18:20', 'out'], ['Feed', '18:40', 'blue'], ['Bedtime', '19:00', 'dark']],
    ];
    const sty = { blue: `background:${BLUE};color:#fff`, yel: `background:${YEL};color:#3d2c00`, dark: `background:#161a2b;color:#fff`, out: `background:#fff;color:${INK};box-shadow:inset 0 0 0 2px #dfe2ee` };
    // landscape: four columns; portrait: two rows of two
    const grid = h('div', 'abs', `<div style="display:flex;flex-wrap:wrap;gap:${pv('30px', '34px 36px')};width:${pv('1250px', '880px')}">${cols.map((c, ci) => `
      <div style="width:${pv(290, 422)}px"><div class="gl" style="font-size:18px;font-weight:600;color:${GREY};margin-bottom:14px;letter-spacing:.02em">${c}</div>
      ${cells[ci].map(([k, v, st]) => `<div class="gcell" style="${sty[st]};height:74px;border-radius:18px;margin-bottom:14px;display:flex;align-items:center;gap:12px;padding:0 20px;font-size:22px;font-weight:600">${icon(st === 'dark' ? 'moon' : st === 'yel' ? 'milk' : st === 'blue' ? 'sun' : 'smile', 22, 'currentColor')}<span>${k}</span><span style="margin-left:auto;opacity:.75;font-variant-numeric:tabular-nums">${v}</span></div>`).join('')}</div>`).join('')}</div>`, s);
    place(grid, 0, pv(110, 130), { scale: pv(1.1, 1.08) });
    const gc = grid.querySelectorAll('.gcell');
    tl.fromTo(grid.querySelectorAll('.gl'), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.4, stagger: 0.08 }, 36.95);
    // pills drop in on the rhythmic pulses
    const order = [0, 3, 6, 9, 1, 4, 7, 10, 2, 5, 8, 11];
    order.forEach((idx, k) => {
      tl.fromTo(gc[idx], { autoAlpha: 0, scale: 0.7, y: -30, filter: 'blur(10px)' }, { autoAlpha: 1, scale: 1, y: 0, filter: 'blur(0px)', duration: 0.45, ease: 'back.out(1.8)' }, 37.0 + k * 0.075);
    });
    tl.to(grid, { scale: pv(1.03, 1.11), duration: 1.6, ease: 'none' }, 37.4);
    tl.to(grid, { autoAlpha: 0, filter: 'blur(18px)', y: '+=40', duration: 0.42, ease: 'power2.in' }, 38.98);
    sfx('swell_h', 34.3, 0.55);
    sfx('swell_zips', 36.3, 0.45);
    sfx('pulses', 36.97, 0.75);
    sfx('swell_short', 38.85, 0.5);
  }

  // =====================================================================
  // S12 · Predictions. Routines. All connected. (39.4 – 42.7)
  // =====================================================================
  {
    const s = scene(39.4, 42.75, content);
    const ty = pv(-300, -640);
    const l1 = text('Predictions.', s, { size: 72, weight: 600, align: 'left', x: -560, y: ty });
    const l2 = text('Routines.', s, { size: 72, weight: 600, align: 'left', x: -560, y: ty });
    const l3 = text('All [connected.]', s, { size: 84, weight: 600, y: ty });
    deferred.push(() => {
      // portrait centres the pair; landscape keeps it left-aligned
      const x0 = PORT ? -(l1.el.offsetWidth + 24 + l2.el.offsetWidth) / 2 : -560;
      gsap.set(l1.el, { x: x0 });
      gsap.set(l2.el, { x: x0 + l1.el.offsetWidth + 24 });
    });
    reveal(l1, 39.5, { stagger: 0.03 }); reveal(l2, 40.25, { stagger: 0.03 });
    conceal(l1, 40.95, { stagger: 0.005 }); conceal(l2, 41.0, { stagger: 0.005 });
    reveal(l3, 41.2, { stagger: 0.035 });
    // links first so the nodes sit on top of their ends
    const mkLink = (v) => {
      const k = h('div', `link${v ? ' v' : ''}`, '<div class="solid"></div>', s);
      gsap.set(k.firstChild, v ? { scaleY: 0, transformOrigin: '50% 0' } : { scaleX: 0 });
      return k;
    };
    // portrait links are all horizontal bars rotated between node centres
    const kL = mkLink(), kR = mkLink(), kB = mkLink(!PORT);
    const NX = 600, NY = 40, BY = 300;
    // portrait: predictions on top, Sprout in the middle, schedule + AI below
    const P = { L: [0, -380], C: [0, -40], R: [-250, 330], B: [250, 330] }, NS = pv(1, 1.2);
    const nodeL = h('div', 'node', `<div class="nico" style="background:${NAVY}">${icon('moon-star', 32, '#9fb0ff')}</div>Nap predictions`, s); place(nodeL, ...pv([-NX, NY], P.L), { scale: NS });
    const nodeR = h('div', 'node', `<div class="nico" style="background:${YEL}">${icon('calendar-days', 32, '#3d2c00')}</div>Schedule creator`, s); place(nodeR, ...pv([NX, NY], P.R), { scale: NS });
    const nodeB = h('div', 'node', `<div class="nico" style="background:${GREEN}">${icon('sparkles', 32, '#06402a')}</div>Ask Sprout AI`, s); place(nodeB, ...pv([0, BY], P.B), { scale: NS });
    const nodeC = h('div', 'node', `<div style="width:64px;height:74px">${LOGO_SVG}</div><span style="font-size:40px;font-weight:700;color:${BLUE};letter-spacing:-.04em">Sprout</span>`, s, { height: '120px' }); place(nodeC, ...pv([0, NY], P.C), { scale: NS });
    if (PORT) {
      // bar from a to b, pivoting on (and growing out of) a
      const span = (k, [ax, ay], [bx, by]) => {
        gsap.set(k, { width: Math.hypot(bx - ax, by - ay), transformOrigin: '0 50%', xPercent: 0, yPercent: -50, x: ax, y: ay, rotation: Math.atan2(by - ay, bx - ax) * 180 / Math.PI });
        gsap.set(k.firstChild, { transformOrigin: '0 50%' });
      };
      span(kL, P.L, P.C); span(kR, P.C, P.R); span(kB, P.C, P.B);
    } else deferred.push(() => {
      const cL = -nodeC.offsetWidth / 2, cR = nodeC.offsetWidth / 2;
      const lR = -NX + nodeL.offsetWidth / 2, rL = NX - nodeR.offsetWidth / 2;
      gsap.set(kL, { width: cL - lR, xPercent: -50, yPercent: -50, x: (cL + lR) / 2, y: NY });
      gsap.set(kR, { width: rL - cR, xPercent: -50, yPercent: -50, x: (rL + cR) / 2, y: NY });
      gsap.set(kL.firstChild, { transformOrigin: '0 50%' });
      gsap.set(kR.firstChild, { transformOrigin: '100% 50%' });
      const top = NY + nodeC.offsetHeight / 2, bot = BY - nodeB.offsetHeight / 2;
      gsap.set(kB, { height: bot - top, xPercent: -50, yPercent: -50, x: 0, y: (top + bot) / 2 });
    });
    enter(nodeC, 39.45, { dy: 0, scale: 0.7, dur: 0.6, ease: 'back.out(1.6)' });
    enter(nodeL, 39.6, pv({ dy: 0, dx: -80, dur: 0.6 }, { dy: -80, dur: 0.6 }));
    tl.fromTo(kL, { autoAlpha: 0, scaleX: 0, transformOrigin: '0 50%' }, { autoAlpha: 1, scaleX: 1, duration: 0.5, ease: 'power2.out' }, 39.8);
    enter(nodeR, 40.3, pv({ dy: 0, dx: 80, dur: 0.6 }, { dy: 60, dx: -60, dur: 0.6 }));
    tl.fromTo(kR, { autoAlpha: 0, scaleX: 0, transformOrigin: pv('100% 50%', '0 50%') }, { autoAlpha: 1, scaleX: 1, duration: 0.5, ease: 'power2.out' }, 40.5);
    // the "solid" fill replaces the dotted line once everything is connected
    enter(nodeB, 40.85, pv({ dy: 60, dur: 0.6, ease: 'back.out(1.5)' }, { dy: 60, dx: 60, dur: 0.6, ease: 'back.out(1.5)' }));
    if (PORT) tl.fromTo(kB, { autoAlpha: 0, scaleX: 0, transformOrigin: '0 50%' }, { autoAlpha: 1, scaleX: 1, duration: 0.4, ease: 'power2.out' }, 41.0);
    else tl.fromTo(kB, { autoAlpha: 0, scaleY: 0, transformOrigin: '50% 0' }, { autoAlpha: 1, scaleY: 1, duration: 0.4, ease: 'power2.out' }, 41.0);
    tl.to([kL.firstChild, kR.firstChild], { scaleX: 1, duration: 0.45, ease: 'power2.inOut' }, 41.35);
    tl.to(kB.firstChild, PORT ? { scaleX: 1, duration: 0.35, ease: 'power2.inOut' } : { scaleY: 1, duration: 0.35, ease: 'power2.inOut' }, 41.55);
    tl.to(nodeC, { boxShadow: '0 0 0 6px rgba(59,79,232,.18), 0 30px 60px -26px rgba(26,35,90,.3)', duration: 0.4 }, 41.6);
    tl.to(s, { scale: 1.04, duration: 3.2, ease: 'none' }, 39.5);
    tl.to([nodeL, nodeR, nodeB, nodeC, kL, kR, kB], { autoAlpha: 0, filter: 'blur(16px)', duration: 0.4, ease: 'power2.in' }, 42.32);
    conceal(l3, 42.3, { stagger: 0.006 });
    sfx('click_ping', 39.6 - 0.08, 0.8);
    sfx('click_ping2', 40.3 - 0.04, 0.7);
    sfx('pop', 40.85, 0.9);
    sfx('swell_f', 40.75, 0.4);
    sfx('sparkle_zip', 41.35 - 0.1, 0.7);
  }

  // =====================================================================
  // S13 · dark wall — From the first feed to the first steps. One day at a time. (42.7 – 46.7)
  // =====================================================================
  {
    darkOn(42.75, 46.72);
    const s = scene(42.75, 46.72, content);
    const wall = h('div', 'abs', null, s, { width: 0, height: 0 }); place(wall);
    const palette = [
      [NAVY, 'moon', '#9fb0ff'], ['#3343da', 'chart-column', '#fff'], [YEL, 'milk', '#3d2c00'], ['#faf7ef', 'baby', INK],
      [PINK, 'droplets', '#8e2a4c'], [GREEN, 'soup', '#06402a'], ['#1d2238', 'timer', '#c7cdea'], ['#e5e7f1', 'heart', '#c2477a'],
      ['#3b4fe8', 'sparkles', '#fff'], ['#161a2b', 'calendar-days', YEL], ['#ffe08a', 'sun', '#3d2c00'], ['#2a3150', 'footprints', '#c7cdea'],
    ];
    const tiles = [];
    const COLS = pv(11, 6), ROWS = pv(7, 13), SX = 196, SY = 150;
    for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
      const x = (c - (COLS - 1) / 2) * SX + (r % 2 ? 40 : -40), y = (r - (ROWS - 1) / 2) * SY;
      const [bg, ic, fg] = palette[(r * 5 + c * 7) % palette.length];
      const e = h('div', 'wt', icon(ic, 48, fg, 2.2), wall, { background: bg });
      place(e, x, y, { rotation: ((r * 7 + c * 3) % 9) - 4 });
      tiles.push({ e, x, y, d: Math.hypot(x, y * 1.4) });
    }
    gsap.set(tiles.map((o) => o.e), { autoAlpha: 0 });
    // a few tiles drift in behind the first line, then the whole wall floods in on the pulses
    tiles.forEach(({ e, x, y, d }, i) => {
      const early = d < 330;
      const t = early ? 42.95 + (i % 4) * 0.08 : 43.7 + (d / 1300) * 0.5;
      tl.fromTo(e, { autoAlpha: 0, scale: 0.6, filter: 'blur(14px)', x: x * 0.8, y: y * 0.8 }, { autoAlpha: early ? 0.55 : 0.5, scale: 1, filter: 'blur(1.5px)', x, y, duration: 0.6, ease: 'power3.out' }, t);
    });
    tl.fromTo(wall, { scale: 1.3 }, { scale: 1.0, duration: 2.0, ease: 'power2.out' }, 42.8);
    // dark pool behind the copy keeps it readable over the tiles
    const pool = h('div', 'glow', null, s, { width: pv('1500px', '1150px'), height: pv('700px', '760px'), background: 'radial-gradient(ellipse, rgba(9,11,18,0.92) 0%, rgba(9,11,18,0.7) 40%, rgba(9,11,18,0) 70%)' });
    place(pool, 0, 0);
    const t1 = text('From the first [feed]', s, { size: 84, weight: 600, color: '#fff', y: -40, accent: ['f7c84a', 'ffe08a'] });
    const t2 = text('to the first [steps,]', s, { size: 84, weight: 600, color: '#fff', y: 60, accent: ['6f80ff', 'a9b8ff'] });
    reveal(t1, 42.9, { stagger: 0.035 });
    reveal(t2, 43.75, { stagger: 0.035 });
    conceal(t1, 44.78, { stagger: 0.006 }); conceal(t2, 44.82, { stagger: 0.006 });
    // push in on the moon tile: one day at a time
    tl.to(wall, { scale: 2.3, duration: 0.9, ease: 'power3.inOut' }, 44.8);
    tl.to(tiles.map((o) => o.e), { autoAlpha: 0.32, filter: 'blur(3px)', duration: 0.6 }, 44.85);
    tl.to(pool, { y: -200, scale: 0.8, duration: 0.9, ease: 'power3.inOut' }, 44.8);
    const hero = h('div', 'wt', icon('moon', 96, '#9fb0ff', 2), s, { background: NAVY, width: '340px', height: '248px', borderRadius: '48px', boxShadow: '0 0 0 2px rgba(159,176,255,.25), 0 50px 100px -30px rgba(0,0,0,.8)' });
    place(hero, 0, 110);
    enter(hero, 45.1, { dy: 60, scale: 0.8, blur: 18, dur: 0.6 });
    const go = h('div', 'tag', `Start nap ${icon('play', 22, '#3d2c00', 2.6)}`, s, { background: YEL, color: '#3d2c00', height: '54px', fontSize: '24px', padding: '0 24px' });
    place(go, 0, 278);
    enter(go, 45.5, { dy: 20, scale: 0.8, dur: 0.45, ease: 'back.out(2)' });
    const t3 = text('One [day] at a time.', s, { size: 80, weight: 600, color: '#fff', y: pv(-230, -300), accent: ['6f80ff', 'a9b8ff'] });
    reveal(t3, 45.12, { stagger: 0.035 });
    tl.to([hero, go], { autoAlpha: 0, filter: 'blur(18px)', scale: 1.1, duration: 0.35, ease: 'power2.in' }, 46.35);
    conceal(t3, 46.3, { stagger: 0.005 });
    tl.to(wall, { autoAlpha: 0, duration: 0.35 }, 46.35);
    sfx('swell_zips2', 42.6, 0.55);
    sfx('pulses', 43.72, 0.7);
    sfx('swell_e', 44.65, 0.55);
    sfx('click_ping', 45.5 - 0.08, 0.7);
  }

  // =====================================================================
  // S14 · Making early parenthood easier to track / understand / enjoy (46.7 – 50.0)
  // =====================================================================
  {
    const s = scene(46.72, 50.05, content);
    const small = text('Making early parenthood', s, { size: pv(50, 54), color: GREY, y: pv(-150, -250) });
    reveal(small, 46.8, { stagger: 0.025 });
    // landscape: "Easier to <word>" on one line; portrait: the word drops to its own line
    const bigO = { size: pv(124, 128), weight: 700, ls: '-0.05em', align: pv('left', 'center') };
    const big = text('Easier to', s, { ...bigO, y: pv(10, -90) });
    const alts = ['track.', 'understand.', 'enjoy.'].map((w) => text(`[${w}]`, s, { ...bigO, y: pv(10, 60) }));
    // [reveal, hide] for each swapped word; "Easier to" re-centres before each swap
    const tw = [[47.55, 48.22], [48.42, 49.0], [49.18, 49.72]];
    if (!PORT) deferred.push(() => {
      const wb = big.el.offsetWidth, gap = 34;
      alts.forEach((a) => {
        const total = wb + gap + a.el.offsetWidth;
        a._x = -total / 2 + wb + gap; a._bx = -total / 2;
        gsap.set(a.el, { x: a._x });
      });
      gsap.set(big.el, { x: alts[0]._bx });
      tl.to(big.el, { x: alts[1]._bx, duration: 0.42, ease: 'power3.inOut' }, tw[0][1] + 0.02);
      tl.to(big.el, { x: alts[2]._bx, duration: 0.42, ease: 'power3.inOut' }, tw[1][1] + 0.02);
    });
    reveal(big, 47.22, { stagger: 0.035 });
    alts.forEach((a, i) => {
      reveal(a, tw[i][0], { stagger: 0.03, dy: -10 });
      conceal(a, tw[i][1], { stagger: 0.008, dur: 0.25, dx: 0 });
    });
    conceal(big, 49.7, { stagger: 0.008, dur: 0.3 });
    conceal(small, 49.7, { stagger: 0.005, dur: 0.3 });
    const flPos = pv([[-700, -300], [-720, 260], [700, -280], [700, 270]], [[-290, -560], [-300, 420], [300, -520], [290, 470]]);
    const fl = [
      ['moon', NAVY, '#9fb0ff', -8, 46.85], ['chart-column', 'linear-gradient(145deg,#5b6cff,#3343da)', '#fff', 7, 47.55],
      ['milk', '#fff', BLUE, 6, 48.42], ['sparkles', 'linear-gradient(145deg,#ffe08a,#f7c84a)', '#3d2c00', -7, 49.18],
    ].map((m, i) => [...flPos[i], ...m]);
    fl.forEach(([x, y, ic, bg, fg, r, t]) => {
      const m = h('div', 'mini', icon(ic, 50, fg, 2.2), s, { background: bg, width: '180px', height: '134px', borderRadius: '28px' });
      place(m, x, y, { rotation: r });
      tl.fromTo(m, { autoAlpha: 0, scale: 0.6, filter: 'blur(14px)', y: y + 40 }, { autoAlpha: 1, scale: 1, filter: 'blur(0px)', y, duration: 0.6, ease: 'back.out(1.6)' }, t);
      tl.to(m, { y: y - 24, rotation: r * 1.4, duration: 3, ease: 'none' }, t + 0.3);
      tl.to(m, { autoAlpha: 0, filter: 'blur(14px)', duration: 0.3, ease: 'power2.in' }, 49.7);
    });
    sfx('swell_glitch', 46.55, 0.55);
    sfx('sparkle_zip', tw[1][0] - 0.1, 0.8);
    sfx('sparkle_zip', tw[2][0] - 0.1, 0.8);
    sfx('pop', tw[2][0] + 0.05, 0.5);
  }

  // =====================================================================
  // S15 · end card — Sprout · Watch them sprout. · URL (50.0 – 55.5)
  // =====================================================================
  {
    const s = scene(50.0, DUR + 1, content);
    const glow = h('div', 'glow', null, s, { width: '1000px', height: '1000px', background: 'radial-gradient(circle, rgba(247,200,74,0.38) 0%, rgba(240,245,170,0.2) 35%, rgba(255,255,255,0) 68%)' });
    place(glow, 0, pv(-90, -170));
    tl.fromTo(glow, { scale: 0.3, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 1.2, ease: 'power2.out' }, 50.0);
    const wm = h('div', 'wordmark', 'Sprout', s, { fontSize: '186px' });
    const yo = pv(0, -80);   // portrait sits the lock-up a little higher
    const L = logo(s, 190); place(L.el, 0, -100 + yo);
    growLogo(L, 50.07);
    deferred.push(() => {
      const ww = wm.offsetWidth, gap = 40, lw = 190;
      const total = lw + gap + ww, wx = -total / 2 + lw + gap + ww / 2;
      place(wm, wx, -88 + yo);
      tl.to(L.el, { x: -total / 2 + lw / 2, duration: 0.75, ease: 'power3.inOut' }, 50.55);
      tl.fromTo(wm, { autoAlpha: 0, filter: 'blur(24px)', x: wx - 120 }, { autoAlpha: 1, filter: 'blur(0px)', x: wx, duration: 0.8, ease: 'power3.out' }, 50.67);
    });
    const tg = text('Watch them [sprout.]', s, { size: pv(62, 68), weight: 500, y: 92 + yo });
    reveal(tg, 51.45, { stagger: 0.035 });
    const pill = h('div', 'urlpill', `<span>sprout.velorynlabs.co.uk</span><span class="sep"></span><span style="color:${BLUE}">Download free</span><span class="go">${icon('arrow-right', 28, '#fff', 2.6)}</span>`, s);
    place(pill, 0, pv(222, 170));
    enter(pill, 52.25, { dy: 30, scale: 0.9, blur: 12, dur: 0.6 });
    const stores = h('div', 'abs', `<span style="display:flex;align-items:center;gap:10px">${icon('star', 22, YEL, 2.4)}Free on iOS &amp; Android</span>`, s, { fontSize: '24px', fontWeight: 500, color: GREY, whiteSpace: 'nowrap' });
    place(stores, 0, pv(316, 266));
    enter(stores, 52.65, { dy: 16, dur: 0.6 });
    tl.fromTo(s, { scale: pv(1.0, 1.1) }, { scale: pv(1.04, 1.14), duration: DUR - 50.0, ease: 'none' }, 50.0);
    sfx('chime', 50.07 + 0.3, 0.75);
    sfx('outro', 50.45, 0.75);
    sfx('click_ping2', 52.25, 0.55);
  }

  // =====================================================================
  const deferredDone = (async () => {
    await document.fonts.ready;
    await Promise.all(['400', '500', '600', '700'].map((w) => document.fonts.load(`${w} 64px Inter`)));
    deferred.forEach((f) => f());
    tl.seek(0, true);
  })();

  window.PROMO = {
    duration: DUR, fps: FPS, cues,
    ready: deferredDone,
    seek(t) { tl.seek(t, true); hooks.forEach((f) => f(t)); },
  };

  deferredDone.then(() => {
    if (qs.has('t')) window.PROMO.seek(parseFloat(qs.get('t')));
    if (qs.has('play')) {
      const t0 = performance.now() - (parseFloat(qs.get('play')) || 0) * 1000;
      const loop = () => { window.PROMO.seek(((performance.now() - t0) / 1000) % DUR); requestAnimationFrame(loop); };
      loop();
    }
  });
})();
