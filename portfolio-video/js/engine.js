// Tiny deterministic animation engine. Everything is a pure function of time:
// window.__seek(t) puts every element exactly where it belongs at t seconds.
(() => {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const mix = (a, b, k) => a + (b - a) * k;

  const E = {
    lin: x => x,
    inQuad: x => x * x,
    outQuad: x => 1 - (1 - x) * (1 - x),
    inCubic: x => x * x * x,
    outCubic: x => 1 - (1 - x) ** 3,
    inOutCubic: x => (x < 0.5 ? 4 * x ** 3 : 1 - (-2 * x + 2) ** 3 / 2),
    outQuart: x => 1 - (1 - x) ** 4,
    inOutQuart: x => (x < 0.5 ? 8 * x ** 4 : 1 - (-2 * x + 2) ** 4 / 2),
    inQuint: x => x ** 5,
    outQuint: x => 1 - (1 - x) ** 5,
    inOutQuint: x => (x < 0.5 ? 16 * x ** 5 : 1 - (-2 * x + 2) ** 5 / 2),
    inExpo: x => (x === 0 ? 0 : 2 ** (10 * x - 10)),
    outExpo: x => (x === 1 ? 1 : 1 - 2 ** (-10 * x)),
    inOutExpo: x => (x === 0 ? 0 : x === 1 ? 1 : x < 0.5 ? 2 ** (20 * x - 10) / 2 : (2 - 2 ** (-20 * x + 10)) / 2),
    outBack: x => { const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2; },
    outBackSoft: x => { const c1 = 0.9, c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2; },
    smooth: x => x * x * (3 - 2 * x),
  };

  // progress of t through [a, b], eased
  const P = (t, a, b, ease = E.outCubic) => ease(clamp((t - a) / (b - a)));

  // keyframes: [[time, value, easeIntoThisKey?], ...]
  function kf(t, keys) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const [t1, v1, e = E.inOutCubic] = keys[i];
      const [t0, v0] = keys[i - 1];
      if (t <= t1) return mix(v0, v1, e((t - t0) / (t1 - t0)));
    }
    return keys[keys.length - 1][1];
  }

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  function h(tag, attrs = {}, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
      else if (k === 'html') el.innerHTML = v;
      else el.setAttribute(k, v);
    }
    for (const kid of kids.flat()) if (kid != null) el.append(kid.nodeType ? kid : document.createTextNode(kid));
    return el;
  }

  // transform string from a compact description
  function tf({ x = 0, y = 0, z = 0, s = 1, sx = 1, sy = 1, r = 0, rx = 0, ry = 0, persp = 0 } = {}) {
    let out = '';
    if (persp) out += `perspective(${persp}px) `;
    out += `translate3d(${x}px,${y}px,${z}px)`;
    if (rx) out += ` rotateX(${rx}deg)`;
    if (ry) out += ` rotateY(${ry}deg)`;
    if (r) out += ` rotate(${r}deg)`;
    if (s !== 1 || sx !== 1 || sy !== 1) out += ` scale(${s * sx},${s * sy})`;
    return out;
  }

  // set the usual animated properties in one go
  function set(el, { o, x, y, z, s, sx, sy, r, rx, ry, persp, blur, bright, sat, extraFilter, ...rest }) {
    if (o !== undefined) el.style.opacity = clamp(o).toFixed(4);
    if ([x, y, z, s, sx, sy, r, rx, ry].some(v => v !== undefined)) el.style.transform = tf({ x, y, z, s, sx, sy, r, rx, ry, persp });
    if (blur !== undefined || bright !== undefined || sat !== undefined || extraFilter) {
      let f = '';
      if (blur !== undefined && blur > 0.05) f += `blur(${blur.toFixed(2)}px) `;
      if (bright !== undefined) f += `brightness(${bright}) `;
      if (sat !== undefined) f += `saturate(${sat}) `;
      if (extraFilter) f += extraFilter;
      el.style.filter = f.trim() || 'none';
    }
    for (const [k, v] of Object.entries(rest)) el.style[k] = v;
  }

  // split text into per-char (or per-word) spans, keeping spaces intact
  function split(el, mode = 'chars') {
    const text = el.textContent;
    el.textContent = '';
    const parts = mode === 'words' ? text.split(/(\s+)/) : [...text];
    const spans = [];
    for (const part of parts) {
      if (/^\s+$/.test(part)) { el.append(document.createTextNode(part)); continue; }
      if (!part) continue;
      const s = h('span', { class: 'sp' }, part);
      el.append(s);
      spans.push(s);
    }
    return spans;
  }

  // the signature "blur in": each piece rises/slides in out of a soft blur
  function blurIn(spans, t, start, { stagger = 0.03, dur = 0.55, blur = 14, dy = 0, dx = 0, ds = 0, ease = E.outQuint } = {}) {
    spans.forEach((sp, i) => {
      const k = P(t, start + i * stagger, start + i * stagger + dur, ease);
      set(sp, { o: k, x: dx * (1 - k), y: dy * (1 - k), s: 1 + ds * (1 - k), blur: blur * (1 - k) });
    });
  }
  function blurOut(spans, t, start, { stagger = 0.02, dur = 0.4, blur = 14, dy = 0, dx = 0, ds = 0, ease = E.inCubic } = {}) {
    spans.forEach((sp, i) => {
      const k = P(t, start + i * stagger, start + i * stagger + dur, ease);
      if (k <= 0) return;
      set(sp, { o: 1 - k, x: dx * k, y: dy * k, s: 1 + ds * k, blur: blur * k });
    });
  }

  // typewriter where freshly typed letters glow in an accent colour and settle
  function typeIn(spans, t, start, cps, { accent = [214, 60, 255], base = [20, 20, 28], settle = 0.35, blur = 6 } = {}) {
    let shown = 0;
    spans.forEach((sp, i) => {
      const at = start + i / cps;
      if (t < at) { sp.style.display = 'none'; return; }
      sp.style.display = '';
      shown++;
      const k = P(t, at, at + settle, E.outCubic);
      const c = accent.map((a, j) => Math.round(mix(a, base[j], k)));
      sp.style.opacity = 1;
      sp.style.color = `rgb(${c})`;
      sp.style.filter = k < 0.4 ? `blur(${(blur * (0.4 - k)).toFixed(2)}px)` : 'none';
    });
    return shown;
  }

  const scenes = [];
  function scene(id, start, end, render) {
    const root = document.getElementById(id);
    scenes.push({ root, start, end, render });
  }

  window.V = { clamp, mix, E, P, kf, $, $$, h, tf, set, split, blurIn, blurOut, typeIn, scene, scenes };

  // returns a promise that settles once any frame images requested for t have decoded
  window.__pending = [];
  window.__seek = t => {
    window.__pending = [];
    for (const s of scenes) {
      const on = t >= s.start && t < s.end;
      if (s.root.style.display !== (on ? 'block' : 'none')) s.root.style.display = on ? 'block' : 'none';
      if (on) s.render(t - s.start, t);
    }
    return Promise.all(window.__pending);
  };
})();
