// S3 · Prompt (7.85–10.05s)
// Black stage, a glow breathing up from the bottom edge, a white prompt bar types the
// brief, the send orb is tapped and the glow floods the frame into the next scene.
(() => {
  const { h, P, E, mix, kf, set, split, typeIn, scene } = window.V;
  const { icon } = window.K;
  const root = document.getElementById('s3');
  root.style.background = '#050408';

  const glow = h('div', { class: 'abs', style: { left: '-192px', width: '2304px', top: '690px', height: '920px',
    background: 'radial-gradient(50% 50% at 50% 50%, #ffffff 0%, #f6c4ff 9%, #d64fff 26%, #7a2cff 48%, rgba(60,20,200,.0) 72%)', filter: 'blur(24px)', transformOrigin: '50% 50%' } });
  const flood = h('div', { class: 'fill', style: { background: 'linear-gradient(180deg, #ff7a3f 0%, #ff3a6e 42%, #e62cf0 78%, #b02cff 100%)', opacity: '0' } });

  const BW = 1240, BH = 128;
  const bar = h('div', { class: 'center', style: { width: `${BW}px`, height: `${BH}px`, marginLeft: `${-BW / 2}px`, marginTop: `${-BH / 2}px`,
    borderRadius: `${BH / 2}px`, background: '#fff', boxShadow: '0 0 0 1px rgba(255,255,255,.6), 0 20px 80px rgba(190,60,255,.35), 0 0 120px rgba(190,60,255,.25)' } });
  const plus = h('div', { class: 'abs', style: { left: '40px', top: '40px', width: '48px', height: '48px', color: '#6b6b78' }, html: icon.plus });
  const text = h('div', { class: 'abs', style: { left: '112px', top: '0', font: `500 44px/${BH}px Poppins`, color: '#16161d', whiteSpace: 'nowrap', letterSpacing: '-0.01em' } },
    'Make it smooth, bold & unforgettable');
  const caret = h('span', { style: { display: 'inline-block', width: '3px', height: '48px', marginLeft: '4px', verticalAlign: '-8px', background: '#c43cff', borderRadius: '2px' } });
  const chars = split(text, 'chars');
  text.append(caret);
  const orb = h('div', { class: 'abs', style: { right: '22px', top: '22px', width: '84px', height: '84px', borderRadius: '50%',
    background: 'radial-gradient(circle at 30% 28%, #ffd2f4 0%, #ff5fd2 30%, #b42cff 62%, #5a1cff 100%)', boxShadow: '0 8px 26px rgba(180,44,255,.55), inset 0 2px 0 rgba(255,255,255,.6)' } });
  const ripple = h('div', { class: 'abs', style: { right: '22px', top: '22px', width: '84px', height: '84px', borderRadius: '50%', border: '3px solid rgba(255,140,230,.9)', opacity: '0' } });
  bar.append(plus, text, ripple, orb);

  const cam = h('div', { class: 'fill' }, glow, bar);
  root.append(cam, flood);

  scene('s3', 7.85, 10.06, (lt, t) => {
    root.style.opacity = P(t, 7.85, 8.05, E.outCubic).toFixed(3);
    // bottom glow breathes in and climbs as the brief is typed
    const rise = kf(t, [[7.9, 0.0], [8.5, 0.55, E.outCubic], [9.3, 0.7], [9.85, 1.6, E.inCubic]]);
    set(glow, { y: mix(420, 0, Math.min(1, rise)) - Math.max(0, rise - 1) * 700, sy: 1 + Math.max(0, rise - 1) * 1.6, sx: 1 + Math.max(0, rise - 1) * 0.6, o: Math.min(1, rise * 1.6) });

    const bin = P(t, 7.95, 8.55, E.outExpo);
    const press = kf(t, [[9.32, 1], [9.42, 0.97, E.outCubic], [9.7, 1, E.outBack]]);
    set(bar, { o: bin, y: mix(60, 0, bin), s: mix(0.92, 1, bin) * press * kf(t, [[9.6, 1], [10.05, 1.25, E.inCubic]]), blur: mix(16, 0, bin) + P(t, 9.75, 10.05, E.inCubic) * 18 });
    bar.style.opacity = (bin * (1 - P(t, 9.82, 10.05))).toFixed(3);

    const shown = typeIn(chars, t, 8.32, 34, { accent: [196, 60, 255], base: [22, 22, 29], settle: 0.3 });
    caret.style.display = t > 8.1 && t < 9.32 && (shown < chars.length || Math.floor(t * 2.4) % 2 === 0) ? 'inline-block' : 'none';

    const tap = kf(t, [[9.3, 1], [9.38, 0.78, E.outCubic], [9.62, 1.08, E.outBack]]);
    set(orb, { s: tap * kf(t, [[9.62, 1.08], [9.75, 1]]), r: (t - 8) * 120 });
    const rk = P(t, 9.36, 9.9, E.outCubic);
    set(ripple, { o: rk > 0 && rk < 1 ? 1 - rk : 0, s: 1 + rk * 2.2 });

    flood.style.opacity = P(t, 9.72, 10.04, E.inOutCubic).toFixed(3);
  });
})();
