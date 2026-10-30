// S9 · Logo end (25.98–30.0s)
// Clean light frame: the play-mark drops in, "aminur_rex" writes itself letter by letter
// (reference 1's sign-off), then the tagline and the booking call to action.
(() => {
  const { h, P, E, mix, kf, set, split, blurIn, scene } = window.V;
  const C = window.CFG;
  const root = document.getElementById('s9');
  root.style.background = '#f6f7f1';

  const glow = h('div', { class: 'fill', style: { background:
    'radial-gradient(38% 46% at 30% 40%, rgba(200,255,0,.55), rgba(200,255,0,0) 70%),' +
    'radial-gradient(40% 50% at 72% 62%, rgba(165,107,255,.35), rgba(165,107,255,0) 70%)', filter: 'blur(20px)' } });

  const mark = h('div', { class: 'abs', style: { left: '0', right: '0', top: '330px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '40px', whiteSpace: 'nowrap' } });
  const logo = h('div', { style: { width: '180px', height: '180px', borderRadius: '52px', background: '#c8ff00', display: 'grid', placeItems: 'center', flex: '0 0 auto',
    boxShadow: '0 24px 60px rgba(120,160,0,.35), inset 0 2px 0 rgba(255,255,255,.8)' },
    html: '<svg viewBox="0 0 24 24" width="84" height="84"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.4-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5Z" fill="#12160a"/></svg>' });
  const word = h('div', { style: { font: '700 200px/1 Poppins', letterSpacing: '-0.05em', color: '#12131a' } });
  const wA = h('span', {}, C.handle.replace('@', '').split('_')[0]);
  const wB = h('span', { style: { color: '#9bc400' } }, '_' + (C.handle.split('_')[1] || ''));
  word.append(wA, wB);
  mark.append(logo, word);
  const chars = [...split(wA, 'chars'), ...split(wB, 'chars')];

  const tag = h('div', { class: 'abs', style: { left: '0', right: '0', top: '600px', textAlign: 'center', font: '500 56px/1.2 Poppins', color: '#3a3d33', letterSpacing: '-0.02em', whiteSpace: 'nowrap' } }, C.tagline);
  const tagW = split(tag, 'words');

  const cta = h('div', { class: 'abs', style: { left: '50%', top: '730px', transform: 'translateX(-50%)', display: 'flex', alignItems: 'center', gap: '22px', padding: '26px 46px 26px 30px',
    borderRadius: '999px', background: '#12131a', color: '#fff', font: '600 40px/1 Poppins', whiteSpace: 'nowrap', boxShadow: '0 24px 60px rgba(18,19,26,.25)' } });
  const dot = h('span', { style: { width: '22px', height: '22px', borderRadius: '50%', background: '#c8ff00', boxShadow: '0 0 0 8px rgba(200,255,0,.25)' } });
  cta.append(dot, h('span', {}, C.cta));
  const url = h('div', { class: 'abs', style: { left: '0', right: '0', top: '860px', textAlign: 'center', font: '500 30px/1 Poppins', color: '#6b6f62', whiteSpace: 'nowrap' } }, C.booking);

  const cam = h('div', { class: 'fill' }, glow, mark, tag, cta, url);
  root.append(cam);

  scene('s9', 25.98, 30.01, (lt, t) => {
    root.style.opacity = P(t, 25.98, 26.2).toFixed(3);
    set(cam, { s: kf(t, [[26.0, 1.06], [27.2, 1.0, E.outCubic], [30, 0.985]]) });
    glow.style.transform = `translateX(${Math.sin(t * 0.9) * 40}px) scale(${1 + Math.sin(t * 0.7) * 0.04})`;

    const lk = P(t, 26.1, 26.6, E.outBack);
    set(logo, { o: P(t, 26.1, 26.22), s: mix(0.2, 1, lk), r: mix(-120, 0, lk) });
    // letters rise in a wave out of a blur
    chars.forEach((c, i) => {
      const a = 26.28 + i * 0.045;
      const k = P(t, a, a + 0.55, E.outQuint);
      set(c, { o: P(t, a, a + 0.18), y: mix(70, 0, k), blur: (1 - k) * 22, s: mix(0.8, 1, k) });
    });
    const shift = kf(t, [[26.1, 110], [26.95, 0, E.outQuint]]); // logo slides left as the word arrives
    set(mark, { x: shift });
    blurIn(tagW, t, 27.0, { stagger: 0.06, dur: 0.5, blur: 16, dy: 26 });
    const ck = P(t, 27.55, 28.0, E.outBack);
    cta.style.opacity = P(t, 27.55, 27.7).toFixed(3);
    cta.style.transform = `translateX(-50%) translateY(${mix(40, 0, ck)}px) scale(${mix(0.85, 1, ck)})`;
    dot.style.boxShadow = `0 0 0 ${(6 + 6 * (0.5 + 0.5 * Math.sin(t * 6))).toFixed(1)}px rgba(200,255,0,.25)`;
    const uk = P(t, 27.85, 28.25, E.outCubic);
    set(url, { o: uk, y: mix(16, 0, uk) });
  });
})();
