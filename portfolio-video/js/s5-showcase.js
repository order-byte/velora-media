// S5 · Selected work (16.0–25.05s)
// One project at a time, big: a 3D carousel deals each film to the centre of the frame,
// where it plays with its name and what it was, then slides away for the next.
(() => {
  const { h, P, E, mix, kf, set, split, blurIn, scene, clamp } = window.V;
  const { clip } = window.K;
  const root = document.getElementById('s5');
  root.style.background = '#f3f3f6';

  const WORK = [
    { id: 'csgo_pick', name: 'CSGOGem', kind: 'Gaming platform launch', tint: '#8b5cff' },
    { id: 'nano_science', name: 'NanoSyllabus', kind: 'EdTech product promo', tint: '#3d5afe' },
    { id: 'fort_walls', name: 'OfflineIQ · Fort Knox', kind: 'AI hardware film', tint: '#19c2a8' },
    { id: 'quad_globe', name: 'Quadrant', kind: 'IT services brand film', tint: '#0fb39a' },
    { id: 'flowly_glass', name: 'Flowly', kind: 'AI app launch', tint: '#4aa8ff' },
    { id: 'agent_glass', name: 'AI Agent', kind: 'SaaS motion promo', tint: '#c03cff' },
  ];
  const T0 = 16.0, STEP = 1.5, SLIDE = 0.5;

  const glow = h('div', { class: 'fill' });
  const header = h('div', { class: 'abs', style: { left: '120px', top: '64px', display: 'flex', alignItems: 'center', gap: '22px', font: '600 34px/1 Poppins', color: '#16161d', letterSpacing: '-0.01em' } });
  const dot = h('span', { style: { width: '16px', height: '16px', borderRadius: '50%', background: '#c8ff00', boxShadow: '0 0 0 6px rgba(200,255,0,.3)' } });
  const hTitle = h('span', {}, 'Selected work');
  header.append(dot, hTitle);
  const counter = h('div', { class: 'abs', style: { right: '120px', top: '60px', font: '600 40px/1 Poppins', color: '#16161d', fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.02em' } });
  const cNow = h('span', {}, '01'), cAll = h('span', { style: { color: '#9a9aa6' } }, ' / 06');
  counter.append(cNow, cAll);

  const stage = h('div', { class: 'center', style: { width: '0', height: '0', perspective: '1800px' } });
  const CW = 1280, CH = 720;
  const cards = WORK.map(w => {
    const c = clip(w.id);
    const el = h('div', { class: 'abs', style: { width: `${CW}px`, height: `${CH}px`, left: `${-CW / 2}px`, top: `${-CH / 2 - 40}px`, borderRadius: '34px', overflow: 'hidden',
      background: '#111', boxShadow: '0 0 0 8px #fff, 0 50px 120px rgba(20,20,40,.28), 0 10px 30px rgba(20,20,40,.14)' } }, c.el);
    const sheen = h('div', { class: 'fill', style: { background: 'linear-gradient(115deg, rgba(255,255,255,0) 40%, rgba(255,255,255,.28) 48%, rgba(255,255,255,0) 56%)', backgroundSize: '260% 100%', mixBlendMode: 'screen' } });
    el.append(sheen);
    stage.append(el);
    return { ...w, el, c, sheen };
  });

  // caption under the card
  const caps = WORK.map(w => {
    const box = h('div', { class: 'abs', style: { left: '0', right: '0', top: '900px', textAlign: 'center', whiteSpace: 'nowrap' } });
    const name = h('div', { style: { font: '700 68px/1.05 Poppins', color: '#16161d', letterSpacing: '-0.035em' } }, w.name);
    const kind = h('div', { style: { font: '500 32px/1.3 Poppins', color: '#6c6c78', marginTop: '6px' } }, w.kind);
    box.append(name, kind);
    return { box, nameS: split(name, 'chars'), kind };
  });

  root.append(glow, stage, header, counter, ...caps.map(c => c.box));

  scene('s5', 15.98, 25.05, (lt, t) => {
    // fade up from the designer scene's white flash
    root.style.opacity = '1';
    const enter = P(t, 15.98, 16.4, E.outCubic);
    const f = (t - T0) / STEP;                         // which project we are on (fractional)
    const idx = clamp(Math.floor(f), 0, WORK.length - 1);
    const cur = WORK[idx];
    glow.style.background = `radial-gradient(55% 60% at 50% 45%, ${cur.tint}33, rgba(243,243,246,0) 70%)`;
    set(header, { o: P(t, 16.05, 16.4), x: mix(-30, 0, P(t, 16.05, 16.5, E.outCubic)) });
    set(counter, { o: P(t, 16.1, 16.45) });
    cNow.textContent = String(idx + 1).padStart(2, '0');

    // carousel position: g counts how many projects have been dealt (eased between steps)
    let g = 0;
    for (let k = 1; k < WORK.length; k++) g += P(t, T0 + k * STEP - SLIDE, T0 + k * STEP, E.outExpo);
    const exitAll = P(t, 24.55, 25.05, E.inCubic);
    cards.forEach((c, i) => {
      const pos = i - g;                     // 0 = centre, -1 = parked left, +1 = waiting right
      const a = Math.abs(pos);
      if (a > 1.6) { c.el.style.display = 'none'; return; }
      c.el.style.display = 'block';
      const first = i === 0 ? enter : 1;
      set(c.el, { x: pos * 1180, y: (i === 0 ? mix(260, 0, enter) : 0) - exitAll * 80,
        s: mix(1, 0.62, Math.min(1, a)) * (1 - exitAll * 0.1) * (i === 0 ? mix(0.85, 1, enter) : 1), ry: -pos * 28, persp: 1800,
        o: (1 - clamp(a - 1, 0, 0.5) * 2) * (i === 1 ? enter : first) * (1 - exitAll), blur: Math.min(1, a) * 6 + exitAll * 10 });
      c.el.style.zIndex = String(100 - Math.round(a * 10));
      const start = T0 + i * STEP;
      c.sheen.style.backgroundPosition = `${kf(t, [[start - 0.05, 130], [start + 0.6, -30, E.inOutCubic]])}% 0`;
      c.c.seek(t - (start - SLIDE), true);
    });

    caps.forEach((cp, i) => {
      const start = T0 + i * STEP;
      const on = t > start - SLIDE * 0.6 && t < start + STEP - SLIDE * 0.4;
      cp.box.style.display = on ? 'block' : 'none';
      if (!on) return;
      blurIn(cp.nameS, t, start - SLIDE * 0.5, { stagger: 0.018, dur: 0.4, blur: 16, dy: 30 });
      const kk = P(t, start - 0.1, start + 0.3, E.outCubic);
      set(cp.kind, { o: kk, y: mix(14, 0, kk) });
      cp.box.style.opacity = (1 - P(t, start + STEP - SLIDE - 0.1, start + STEP - SLIDE * 0.4)).toFixed(3);
    });
  });
})();
