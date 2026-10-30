// S6 · Work grid (24.98–28.05s)
// Four projects play at once in a 2x2 grid (references 2–4). The cells fly in, carry
// a project tag, swap to four more projects on the beat, then the camera dives into
// one cell to hand over to the services scene.
(() => {
  const { h, P, E, mix, kf, set, scene, clamp } = window.V;
  const { clip, CLIPS } = window.K;
  const root = document.getElementById('s6');
  root.style.background = '#0b0b10';

  const A = ['csgo_mines', 'nano_explore', 'fort_apps', 'flowly_grass'];
  const B = ['quad_insight', 'csgo_deposit', 'agent_boost', 'flowly_phone'];
  const GAP = 10, CW = (1920 - GAP) / 2, CH = (1080 - GAP) / 2;
  const cam = h('div', { class: 'fill', style: { transformOrigin: '0 0' } });
  root.append(cam);

  const cells = [0, 1, 2, 3].map(i => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = col * (CW + GAP), y = row * (CH + GAP);
    const el = h('div', { class: 'abs', style: { left: `${x}px`, top: `${y}px`, width: `${CW}px`, height: `${CH}px`, overflow: 'hidden', borderRadius: '18px', background: '#15151c' } });
    const a = clip(A[i]), b = clip(B[i]);
    const layA = h('div', { class: 'fill' }, a.el), layB = h('div', { class: 'fill' }, b.el);
    const tag = (id) => {
      const label = (CLIPS[id] && CLIPS[id].label) || id;
      return h('div', { class: 'abs', style: { left: '26px', bottom: '24px', padding: '12px 20px', borderRadius: '999px', font: '600 26px/1 Poppins', color: '#fff',
        background: 'rgba(15,15,20,.55)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', boxShadow: 'inset 0 0 0 1px rgba(255,255,255,.18)', whiteSpace: 'nowrap' } }, label);
    };
    const tagA = tag(A[i]), tagB = tag(B[i]);
    layA.append(tagA); layB.append(tagB);
    el.append(layA, layB);
    cam.append(el);
    const from = [[-1, 0], [0, -1], [0, 1], [1, 0]][i];
    return { el, a, b, layA, layB, tagA, tagB, from, cx: x + CW / 2, cy: y + CH / 2 };
  });

  scene('s6', 24.98, 28.05, (lt, t) => {
    cells.forEach((c, i) => {
      const k = P(t, 25.0 + i * 0.06, 25.55 + i * 0.06, E.outExpo);
      set(c.el, { x: c.from[0] * 1100 * (1 - k), y: c.from[1] * 700 * (1 - k), s: mix(0.8, 1, k), o: P(t, 25.0 + i * 0.06, 25.15 + i * 0.06),
        blur: (1 - k) * 18 });
      // swap to the second set with a staggered vertical wipe
      const sw = P(t, 26.35 + i * 0.07, 26.77 + i * 0.07, E.inOutQuart);
      set(c.layA, { y: -sw * CH * 0.35, s: 1 + sw * 0.08, blur: sw * 10 });
      c.layA.style.opacity = (1 - P(t, 26.47 + i * 0.07, 26.77 + i * 0.07)).toFixed(3);
      c.layB.style.clipPath = `inset(${((1 - sw) * 100).toFixed(2)}% 0 0 0 round 18px)`;
      set(c.layB, { y: (1 - sw) * CH * 0.25, s: 1 + (1 - sw) * 0.08 });
      c.layB.style.display = sw > 0 ? 'block' : 'none';
      c.layA.style.display = sw < 1 ? 'block' : 'none';
      if (sw < 1) c.a.seek(t - 25.0, true);
      if (sw > 0) c.b.seek(t - 26.35, true);
      const ta = P(t, 25.55 + i * 0.08, 25.95 + i * 0.08, E.outBack);
      set(c.tagA, { o: ta, x: mix(-30, 0, ta) });
      const tb = P(t, 26.8 + i * 0.08, 27.2 + i * 0.08, E.outBack);
      set(c.tagB, { o: tb, x: mix(-30, 0, tb) });
    });
    // dive into the bottom-right cell, then hand over
    const dive = P(t, 27.45, 28.05, E.inQuint);
    const target = cells[3];
    const s = mix(1, 2.6, dive);
    cam.style.transform = `translate(${mix(target.cx, 960, dive) - target.cx * s}px, ${mix(target.cy, 540, dive) - target.cy * s}px) scale(${s})`;
    cam.style.filter = dive > 0.02 ? `blur(${(dive * 14).toFixed(2)}px)` : 'none';
    root.style.opacity = (P(t, 24.98, 25.1) * (1 - P(t, 27.88, 28.05))).toFixed(3);
  });
})();
