// AMINUR_REX lime-green logo animation renderer (runs in Chromium page).
// Two passes per frame: SOLID (transparent bg, normal "over") and LIGHT (black bg, additive).
(function () {
  const W = 1440, H = 1140;           // screen-space at 2x
  const CX = 672, CY = 560;           // logo centre (2x screen space)
  const P = 64.5 / 30;                // loop period (s) – matches the original AE loop
  const TEXT = 'AMINUR_REX';

  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, t) => a + (b - a) * t;
  const easeOutCubic = t => 1 - Math.pow(1 - clamp(t), 3);
  const easeInCubic = t => Math.pow(clamp(t), 3);
  const easeOutBack = (t, s = 2.2) => { t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1; };
  const spring = (t, f = 3.2, d = 5.5) => (t <= 0 ? 0 : 1 - Math.exp(-d * t) * Math.cos(2 * Math.PI * f * t));
  function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

  let L = null; // layout

  function mkCanvas(w = W, h = H) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

  window.setupLogo = function (fontB64, opts) {
    opts = opts || {};
    const bin = Uint8Array.from(atob(fontB64), c => c.charCodeAt(0));
    const font = opentype.parse(bin.buffer);
    const targetW = opts.targetW || 1060;
    // measure at size 100
    let size = 100;
    const adv = (s) => { let x = 0; const gl = font.stringToGlyphs(TEXT); gl.forEach((g, i) => { x += g.advanceWidth * s / font.unitsPerEm; if (i < gl.length - 1) x += font.getKerningValue(g, gl[i + 1]) * s / font.unitsPerEm; }); return x; };
    size = 100 * targetW / adv(100);
    const glyphs = font.stringToGlyphs(TEXT);
    const totalW = adv(size);
    const r = rng(7);
    let x = CX - totalW / 2;
    const letters = [];
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg'); document.body.appendChild(svg);
    glyphs.forEach((g, i) => {
      const path = g.getPath(0, 0, size);
      const bb = path.getBoundingBox();
      const d = path.toPathData(2);
      const contours = d.split(/(?=M)/).filter(s => s.trim().length);
      const cinfo = contours.map(cd => { const p = document.createElementNS(svgNS, 'path'); p.setAttribute('d', cd); svg.appendChild(p); return { d: cd, p, len: p.getTotalLength(), p2d: new Path2D(cd) }; });
      const ch = TEXT[i];
      const isUnd = ch === '_';
      const jitterY = isUnd ? 6 : (r() - 0.5) * 26;
      const rot = isUnd ? -0.05 : (r() - 0.5) * 0.12;
      const sc = isUnd ? 1.0 : 0.96 + r() * 0.12;
      letters.push({ ch, x, bb, d, p2d: new Path2D(d), contours: cinfo, jitterY, rot, sc,
        cx: (bb.x1 + bb.x2) / 2, cy: (bb.y1 + bb.y2) / 2 });
      x += g.advanceWidth * size / font.unitsPerEm;
      if (i < glyphs.length - 1) x += font.getKerningValue(g, glyphs[i + 1]) * size / font.unitsPerEm;
    });
    // vertical centring
    let y1 = 1e9, y2 = -1e9; letters.forEach(l => { y1 = Math.min(y1, l.bb.y1); y2 = Math.max(y2, l.bb.y2); });
    const baseY = CY - (y1 + y2) / 2;
    letters.forEach(l => { l.baseY = baseY; });
    const thick = opts.thick != null ? opts.thick : 7;
    L = { font, size, letters, baseY, thick, capTop: baseY + y1, capBot: baseY + y2, left: CX - totalW / 2, right: CX + totalW / 2 };
    // drips: pick letters + x positions, find bottom edge via isPointInPath
    const tmp = mkCanvas(10, 10).getContext('2d');
    const dripPlan = [[0, 0.22, 46], [1, 0.75, 70], [3, 0.5, 38], [5, 0.3, 58], [7, 0.62, 80], [8, 0.4, 44], [9, 0.8, 52], [2, 0.5, 30]];
    L.drips = [];
    dripPlan.forEach(([li, fx, len], k) => {
      const l = letters[li]; if (!l) return;
      const px = l.bb.x1 + (l.bb.x2 - l.bb.x1) * fx;
      let found = null;
      tmp.lineWidth = thick;
      for (let yy = l.bb.y2 + thick; yy > l.bb.y1; yy -= 0.5) {
        if (tmp.isPointInPath(l.p2d, px, yy) || tmp.isPointInStroke(l.p2d, px, yy)) { found = yy; break; }
      }
      if (found != null) L.drips.push({ li, px, py: found - 3, len, w: 9 + (k % 3) * 3, delay: k * 0.045 });
    });
    // particles (deterministic)
    const pr = rng(42);
    L.sparks = [];
    for (let i = 0; i < 90; i++) {
      const sx = lerp(L.left, L.right, pr()); const sy = lerp(L.capTop, L.capBot, pr());
      let ang = Math.atan2(sy - CY, (sx - CX) * 0.35) + (pr() - 0.5) * 1.2;
      const sp = 500 + pr() * 1300;
      L.sparks.push({ x: sx, y: sy, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp - 250, life: 0.35 + pr() * 0.55, w: 1.5 + pr() * 3, hue: pr() });
    }
    L.embers = [];
    for (let i = 0; i < 34; i++) L.embers.push({ x: lerp(L.left - 60, L.right + 60, pr()), y: lerp(L.capTop - 40, L.capBot + 60, pr()), v: 30 + pr() * 70, ph: pr() * 6.28, r: 1.5 + pr() * 2.5, t0: 1.0 + pr() * 0.5 });
    return { size, letters: letters.length, drips: L.drips.length };
  };

  // ---------- per-letter state over local loop time u ----------
  function strokeT(i, u) { const s = 0.08 + 0.034 * i; return clamp((u - s) / 0.34); }
  function popT(i, u) { const s = 0.36 + 0.048 * i; return (u - s) / 0.24; }
  function globalScale(u) {
    if (u < 0.93) return 1;
    if (u < 0.99) return lerp(1, 0.93, easeOutCubic((u - 0.93) / 0.06));
    return 1 + 0.13 * (1 - spring(u - 0.99, 2.6, 6.0));
  }
  function exitT(u) { return clamp((u - 2.035) / 0.075); }

  function letterTransform(ctx, l, extraScale) {
    const gs = L.gs;
    ctx.translate(CX, CY); ctx.scale(gs * L.exSX, gs * L.exSY); ctx.translate(-CX, -CY);
    ctx.translate(l.x + l.cx, l.baseY + l.cy + l.jitterY);
    ctx.rotate(l.rot);
    ctx.scale(l.sc * extraScale, l.sc * extraScale);
    ctx.translate(-l.cx, -l.cy);
  }

  function faceGradient(ctx) {
    const g = ctx.createLinearGradient(0, L.capTop - L.baseY - 10, 0, L.capBot - L.baseY + 10);
    g.addColorStop(0, '#F6FFD0'); g.addColorStop(0.28, '#D4FF3A'); g.addColorStop(0.62, '#A8F000'); g.addColorStop(1, '#58B800');
    return g;
  }

  function drawLetterSolid(ctx, l, k, flash, u) {
    // extrusion
    const depth = 16;
    ctx.save(); letterTransform(ctx, l, k);
    ctx.lineJoin = 'miter'; ctx.miterLimit = 6;
    for (let d = depth; d >= 1; d--) {
      const t = d / depth;
      ctx.save(); ctx.translate(d * 0.8, d * 1.15);
      const c = `rgb(${Math.round(lerp(28, 6, t))},${Math.round(lerp(92, 34, t))},${Math.round(lerp(6, 2, t))})`;
      ctx.fillStyle = c; ctx.strokeStyle = c; ctx.lineWidth = L.thick + 6;
      ctx.fill(l.p2d); ctx.stroke(l.p2d); ctx.restore();
    }
    // dark outline
    ctx.strokeStyle = '#0B2400'; ctx.lineWidth = L.thick + 9; ctx.stroke(l.p2d);
    // face
    const fg = faceGradient(ctx);
    ctx.fillStyle = fg; ctx.strokeStyle = fg; ctx.lineWidth = L.thick;
    ctx.fill(l.p2d); ctx.stroke(l.p2d);
    // bevel: top-left rim light & bottom-right rim shade (clipped to face)
    ctx.save();
    ctx.beginPath(); ctx.lineWidth = L.thick;
    ctx.clip(l.p2d);
    ctx.globalAlpha = 0.38; ctx.strokeStyle = 'rgba(255,255,235,1)'; ctx.lineWidth = 3;
    ctx.translate(1.6, 2.2); ctx.stroke(l.p2d); ctx.translate(-1.6, -2.2);
    ctx.globalAlpha = 0.5; ctx.strokeStyle = 'rgba(40,110,0,1)'; ctx.lineWidth = 8;
    ctx.translate(-3.5, -4.5); ctx.stroke(l.p2d); ctx.translate(3.5, 4.5);
    // glossy top band
    ctx.globalAlpha = 1;
    const gb = ctx.createLinearGradient(0, L.capTop - L.baseY, 0, L.capBot - L.baseY);
    gb.addColorStop(0, 'rgba(255,255,255,0.45)'); gb.addColorStop(0.38, 'rgba(255,255,255,0.12)'); gb.addColorStop(0.42, 'rgba(255,255,255,0)'); gb.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = gb; ctx.fillRect(l.bb.x1 - 20, l.bb.y1 - 40, l.bb.x2 - l.bb.x1 + 40, l.bb.y2 - l.bb.y1 + 80);
    ctx.restore();
    // pop flash (white)
    if (flash > 0) {
      ctx.globalAlpha = flash; ctx.fillStyle = '#FFFFFF'; ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = L.thick + 2;
      ctx.fill(l.p2d); ctx.stroke(l.p2d); ctx.globalAlpha = 1;
    }
    ctx.restore();
  }

  function drawDrips(ctx, u, alpha) {
    const fg0 = null;
    L.drips.forEach(dp => {
      const t = easeOutCubic((u - 1.02 - dp.delay) / 0.75);
      if (t <= 0) return;
      const l = L.letters[dp.li];
      ctx.save(); letterTransform(ctx, l, 1);
      const len = dp.len * t; const w = dp.w;
      const x = dp.px, y = dp.py;
      const g = ctx.createLinearGradient(x - w, 0, x + w, 0);
      g.addColorStop(0, '#7BD400'); g.addColorStop(0.35, '#E4FF7A'); g.addColorStop(0.6, '#B6F500'); g.addColorStop(1, '#4E9E00');
      // outline/extrusion
      const shape = (pad) => {
        ctx.beginPath();
        ctx.moveTo(x - w / 2 - pad - 4, y - 6);
        ctx.quadraticCurveTo(x - w / 2 - pad, y + 2, x - w * 0.32 - pad, y + len);
        ctx.arc(x, y + len + w * 0.25, w * 0.62 + pad, Math.PI * 1.05, Math.PI * -0.05, true);
        ctx.quadraticCurveTo(x + w / 2 + pad, y + 2, x + w / 2 + pad + 4, y - 6);
        ctx.closePath();
      };
      ctx.globalAlpha = alpha;
      ctx.save(); ctx.translate(5, 7); shape(3); ctx.fillStyle = '#123A00'; ctx.fill(); ctx.restore();
      shape(4.5); ctx.fillStyle = '#0B2400'; ctx.fill();
      shape(0); ctx.fillStyle = g; ctx.fill();
      // specular dot
      ctx.beginPath(); ctx.ellipse(x - w * 0.18, y + len + w * 0.05, w * 0.16, w * 0.24, 0, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,240,0.9)'; ctx.fill();
      ctx.restore();
    });
  }

  const solidC = mkCanvas(), lightC = mkCanvas(), tmpC = mkCanvas();
  window.solidCanvas = solidC; window.lightCanvas = lightC;

  window.renderLogo = function (u) {
    const s = solidC.getContext('2d'), li = lightC.getContext('2d'), tc = tmpC.getContext('2d');
    s.setTransform(1, 0, 0, 1, 0, 0); s.clearRect(0, 0, W, H);
    li.setTransform(1, 0, 0, 1, 0, 0); li.globalCompositeOperation = 'source-over'; li.globalAlpha = 1; li.filter = 'none';
    li.fillStyle = '#000'; li.fillRect(0, 0, W, H);
    tc.setTransform(1, 0, 0, 1, 0, 0); tc.clearRect(0, 0, W, H);
    if (u < 0.06 || u >= 2.115) return;

    const ex = exitT(u);
    L.gs = globalScale(u);
    L.exSX = 1 + 0.35 * easeInCubic(ex);
    L.exSY = Math.max(0.015, 1 - easeInCubic(ex) * 1.0);

    // ---------- SOLID PASS ----------
    let anyFilled = false;
    L.letters.forEach((l, i) => {
      const pt = popT(i, u);
      if (pt <= 0) return;
      anyFilled = true;
      const k = pt >= 1 ? 1 : Math.max(0.001, easeOutBack(pt, 2.6) * 1.0);
      const kk = lerp(0.25, 1, k);
      const flash = clamp(1 - pt / 0.55) * 0.95;
      drawLetterSolid(s, l, kk, flash, u);
    });
    if (anyFilled) drawDrips(s, u, 1);
    // shine sweep (source-atop on the solid layer)
    const sh = (u - 1.22) / 0.42;
    if (sh > 0 && sh < 1 && ex === 0) {
      s.save(); s.globalCompositeOperation = 'source-atop';
      const bx = lerp(L.left - 200, L.right + 200, easeOutCubic(sh) * 0.6 + sh * 0.4);
      const g = s.createLinearGradient(bx - 70, 0, bx + 70, 0);
      g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.45, 'rgba(255,255,240,0.42)'); g.addColorStop(0.55, 'rgba(255,255,240,0.42)'); g.addColorStop(1, 'rgba(255,255,255,0)');
      s.translate(bx, CY); s.transform(1, 0, -0.45, 1, 0, 0); s.translate(-bx, -CY);
      s.fillStyle = g; s.fillRect(bx - 120, 0, 240, H);
      s.restore();
    }
    // exit: brighten to white as it collapses
    if (ex > 0) {
      s.save(); s.globalCompositeOperation = 'source-atop'; s.globalAlpha = clamp(ex * 1.3); s.fillStyle = '#F2FFD6'; s.fillRect(0, 0, W, H); s.restore();
    }

    // ---------- LIGHT PASS (additive on black) ----------
    li.globalCompositeOperation = 'lighter';
    // bloom of the solid layer
    if (anyFilled) {
      const pulse = 0.85 + 0.15 * Math.sin(u * 2 * Math.PI * 1.6);
      li.globalAlpha = 0.42 * pulse; li.filter = 'blur(14px)'; li.drawImage(solidC, 0, 0);
      li.globalAlpha = 0.32 * pulse; li.filter = 'blur(42px)'; li.drawImage(solidC, 0, 0);
      li.filter = 'none'; li.globalAlpha = 1;
    }
    // write-on neon strokes with spark heads
    L.letters.forEach((l, i) => {
      const st = strokeT(i, u);
      if (st <= 0) return;
      const pt = popT(i, u);
      const fade = clamp(1 - (pt - 0.15) / 0.5);
      if (fade <= 0) return;
      tc.save(); tc.clearRect(0, 0, W, H);
      letterTransform(tc, l, 1);
      tc.lineCap = 'round'; tc.lineJoin = 'round';
      const e = easeOutCubic(st);
      l.contours.forEach((c, ci) => {
        const dl = c.len * e;
        tc.setLineDash([dl, c.len + 10]); tc.lineDashOffset = 0;
        tc.strokeStyle = '#D9FF6A'; tc.lineWidth = 4.5; tc.stroke(c.p2d);
      });
      tc.setLineDash([]);
      // heads
      if (st < 1) l.contours.forEach(c => {
        const pnt = c.p.getPointAtLength(c.len * e);
        const g = tc.createRadialGradient(pnt.x, pnt.y, 0, pnt.x, pnt.y, 22);
        g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.25, 'rgba(225,255,120,0.9)'); g.addColorStop(1, 'rgba(120,255,0,0)');
        tc.fillStyle = g; tc.beginPath(); tc.arc(pnt.x, pnt.y, 22, 0, Math.PI * 2); tc.fill();
      });
      tc.restore();
      li.globalAlpha = fade; li.filter = 'blur(6px)'; li.drawImage(tmpC, 0, 0); li.drawImage(tmpC, 0, 0);
      li.filter = 'none'; li.drawImage(tmpC, 0, 0); li.globalAlpha = 1;
    });
    // impact: flash + shockwave + sparks
    const it = u - 0.99;
    if (it > 0) {
      const fa = clamp(1 - it / 0.22);
      if (fa > 0) {
        const g = li.createRadialGradient(CX, CY, 0, CX, CY, 700);
        g.addColorStop(0, `rgba(240,255,200,${0.75 * fa})`); g.addColorStop(0.35, `rgba(150,255,30,${0.35 * fa})`); g.addColorStop(1, 'rgba(0,0,0,0)');
        li.fillStyle = g; li.fillRect(0, 0, W, H);
      }
      L.sparks.forEach(p => {
        const t = it; if (t > p.life) return;
        const drag = 2.2;
        const k = (1 - Math.exp(-drag * t)) / drag;
        const x = p.x + p.vx * k, y = p.y + p.vy * k + 900 * t * t * 0.5;
        const vx = p.vx * Math.exp(-drag * t), vy = p.vy * Math.exp(-drag * t) + 900 * t;
        const a = 1 - t / p.life;
        li.strokeStyle = p.hue > 0.6 ? `rgba(255,255,230,${a})` : `rgba(170,255,40,${a})`;
        li.lineWidth = p.w * (0.5 + a * 0.5); li.lineCap = 'round';
        li.beginPath(); li.moveTo(x, y); li.lineTo(x - vx * 0.03, y - vy * 0.03); li.stroke();
      });
    }
    // embers during hold
    L.embers.forEach(e => {
      const t = u - e.t0; if (t < 0 || ex > 0) return;
      const a = clamp(t / 0.3) * clamp((2.03 - u) / 0.2) * (0.5 + 0.5 * Math.sin(e.ph + u * 9));
      const x = e.x + Math.sin(e.ph + u * 2) * 12, y = e.y - e.v * t;
      const g = li.createRadialGradient(x, y, 0, x, y, e.r * 4);
      g.addColorStop(0, `rgba(230,255,150,${a})`); g.addColorStop(1, 'rgba(100,255,0,0)');
      li.fillStyle = g; li.beginPath(); li.arc(x, y, e.r * 4, 0, Math.PI * 2); li.fill();
    });
    // exit: bright horizontal line flash
    if (ex > 0) {
      const a = Math.sin(Math.PI * clamp(ex * 1.0));
      const w = lerp(L.right - L.left, (L.right - L.left) * 1.5, ex);
      const g = li.createLinearGradient(CX - w / 2, 0, CX + w / 2, 0);
      g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.5, `rgba(235,255,180,${a})`); g.addColorStop(1, 'rgba(0,0,0,0)');
      li.fillStyle = g; li.filter = 'blur(4px)'; li.fillRect(CX - w / 2, CY - 6, w, 12); li.filter = 'none';
    }
  };
  window.LOOP_P = P;
})();
