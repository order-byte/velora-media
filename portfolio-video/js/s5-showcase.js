// S5 · Work showcase (14.0–18.05s)
// "Promos [stack] that convert." — a card stack in the middle deals Aminur's projects
// one per beat (reference 4), then the stack bursts into a diagonal stream of work
// cards around a changing label (reference 3).
(() => {
  const { h, P, E, mix, kf, set, split, blurIn, blurOut, scene, clamp } = window.V;
  const { clip } = window.K;
  const root = document.getElementById('s5');
  root.style.background = '#fbfafc';

  const card = (id, w, hgt, r = 26) => {
    const c = clip(id);
    const el = h('div', { class: 'abs', style: { width: `${w}px`, height: `${hgt}px`, left: `${-w / 2}px`, top: `${-hgt / 2}px`, borderRadius: `${r}px`, overflow: 'hidden',
      background: '#111', boxShadow: '0 0 0 5px #fff, 0 24px 60px rgba(20,20,40,.22), 0 4px 14px rgba(20,20,40,.12)' } }, c.el);
    return { el, c };
  };

  // --- A: stack ---
  const STACK = ['csgo_pick', 'nano_orbit', 'fort_walls', 'quad_globe', 'flowly_glass', 'agent_boost', 'csgo_mines'];
  const stackWrap = h('div', { class: 'center' });
  const stack = STACK.map((id, i) => {
    const c = card(id, 600, 338);
    stackWrap.append(c.el);
    return { ...c, at: 14.18 + i * 0.25, rot: [-7, 6, -4, 8, -6, 4, 0][i] };
  });
  const left = h('div', { class: 'abs', style: { right: '1300px', top: '470px', font: '600 104px/1 Poppins', letterSpacing: '-0.04em', color: '#16161d', whiteSpace: 'nowrap' } }, 'Promos');
  const right = h('div', { class: 'abs', style: { left: '1300px', top: '470px', font: '600 104px/1 Poppins', letterSpacing: '-0.04em', color: '#16161d', whiteSpace: 'nowrap' } }, 'that convert.');
  const lw = split(left, 'chars'), rw = split(right, 'chars');

  // --- B: stream ---
  const FLOW = ['csgo_deposit', 'nano_science', 'fort_apps', 'quad_insight', 'flowly_phone', 'agent_glass', 'csgo_pick', 'nano_explore',
    'quad_globe', 'flowly_grass', 'fort_walls', 'agent_boost', 'csgo_mines', 'nano_orbit'];
  const streamWrap = h('div', { class: 'fill' });
  const stream = FLOW.map((id, i) => {
    const depth = [1, 0.7, 0.85, 1.1, 0.75, 0.95, 0.65, 1.05, 0.8, 0.9, 1.15, 0.7, 0.95, 0.8][i];
    const c = card(id, 420 * depth, 236 * depth, 22 * depth);
    streamWrap.append(c.el);
    return { ...c, depth, u0: 0.35 - i * 0.075, side: (i % 2 ? 1 : -1) * (120 + (i * 53) % 160), rot: ((i * 37) % 20) - 10 };
  });
  const labels = ['Launch films', 'Product demos', 'UI animation', 'Explainers'];
  const labelBox = h('div', { class: 'center', style: { width: '0', height: '0' } });
  const labelEls = labels.map(l => {
    const e = h('div', { class: 'abs', style: { left: '0', top: '0', transform: 'translate(-50%,-50%)', whiteSpace: 'nowrap', font: '600 92px/1 Poppins', letterSpacing: '-0.035em', color: '#16161d',
      padding: '18px 40px', borderRadius: '999px', background: 'rgba(255,255,255,.82)', boxShadow: '0 10px 40px rgba(20,20,40,.10)' } }, l);
    labelBox.append(e); return e;
  });

  root.append(left, right, stackWrap, streamWrap, labelBox);

  scene('s5', 14.0, 18.05, (lt, t) => {
    // ---------- A ----------
    const aOn = t < 16.1;
    stackWrap.style.display = left.style.display = right.style.display = aOn ? 'block' : 'none';
    if (aOn) {
      blurIn(lw, t, 14.02, { stagger: 0.025, dur: 0.45, blur: 18, dx: -30 });
      blurIn(rw, t, 14.12, { stagger: 0.025, dur: 0.45, blur: 18, dx: 30 });
      const push = kf(t, [[14.0, 0], [15.95, 0], [16.1, 1, E.inCubic]]);
      set(left, { x: -push * 500, blur: push * 20 });
      set(right, { x: push * 500, blur: push * 20 });
      left.style.opacity = right.style.opacity = (1 - push).toFixed(3);
      stack.forEach((s, i) => {
        const k = P(t, s.at, s.at + 0.32, E.outExpo);
        const seen = t >= s.at - 0.02;
        s.el.style.display = seen ? 'block' : 'none';
        if (!seen) return;
        const under = stack.filter(o => t >= o.at).length - 1 - i; // how many cards landed on top
        const sink = clamp(under, 0, 4);
        set(s.el, {
          o: P(t, s.at - 0.02, s.at + 0.08),
          y: mix(420, 0, k) + sink * -10, x: sink * (i % 2 ? 14 : -14),
          s: mix(1.25, 1, k) * (1 - sink * 0.04), r: mix(s.rot * 2.2, s.rot * (sink ? 1 : 0.35), k),
          blur: mix(8, 0, k) + sink * 0.6,
        });
        s.c.seek(t - s.at);
      });
      set(stackWrap, { s: kf(t, [[14.0, 0.9], [14.5, 1, E.outCubic], [15.95, 1.04], [16.1, 1.5, E.inCubic]]), o: 1 - P(t, 15.98, 16.1) });
    }

    // ---------- B ----------
    const bOn = t > 15.92;
    streamWrap.style.display = labelBox.style.display = bOn ? 'block' : 'none';
    if (bOn) {
      const speed = kf(t, [[15.92, 2.2], [16.35, 0.42, E.outCubic], [17.6, 0.5], [18.05, 2.0, E.inCubic]]);
      // integrate speed analytically enough: piecewise sum
      const travel = flowTravel(t);
      stream.forEach(s => {
        const u = s.u0 + travel;
        if (u < -0.2 || u > 1.25) { s.el.style.display = 'none'; return; }
        s.el.style.display = 'block';
        // gentle S-curve from bottom-left to top-right
        const x = mix(-250, 2170, u), y = mix(1250, -170, u) + Math.sin(u * Math.PI * 1.4) * 140;
        const nx = 0.53, ny = 0.85; // perpendicular-ish offset
        set(s.el, { x: x + s.side * nx, y: y + s.side * ny, s: s.depth, r: s.rot + (u - 0.5) * 10,
          blur: Math.max(0, (1 - s.depth) * 6) + speed * 2.2, o: 1 });
        s.el.style.zIndex = Math.round(s.depth * 10);
        s.c.seek(t - 15.9);
      });
      labelEls.forEach((e, i) => {
        const a = 16.12 + i * 0.45, last = i === labels.length - 1;
        const kin = P(t, a, a + 0.3, E.outExpo), kout = last ? P(t, 17.82, 18.02, E.inCubic) : P(t, a + 0.45, a + 0.6, E.inCubic);
        e.style.opacity = (kin * (1 - kout)).toFixed(3);
        e.style.filter = `blur(${((1 - kin) * 16 + kout * 16).toFixed(2)}px)`;
        e.style.transform = `translate(-50%,-50%) translateY(${(mix(50, 0, kin) - kout * 50).toFixed(1)}px) scale(${mix(0.9, 1, kin)})`;
      });
      labelBox.style.zIndex = 9;
    }
  });

  // distance travelled along the stream by time t (speed curve integrated numerically)
  function flowTravel(t) {
    let d = 0;
    for (let x = 15.92; x < t; x += 1 / 120) {
      const sp = kf(x, [[15.92, 2.2], [16.35, 0.42, E.outCubic], [17.6, 0.5], [18.05, 2.0, E.inCubic]]);
      d += sp / 120;
    }
    return d * 0.55;
  }
})();
