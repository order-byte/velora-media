// S10 · Motion Designer (12.0–16.05s)
// Aminur's banner, animated: on the drop "DESIGNER" slams in, Aminur rises in front of
// it, the brushed "MOTION" wipes on, the Pr / Ae / spark tool icons fly in and float,
// and his signature writes itself under it all on a burning orange stage.
(() => {
  const { h, P, E, mix, kf, set, scene, clamp } = window.V;
  const root = document.getElementById('s10');
  root.style.background = '#ff6a00';

  const bg = h('div', { class: 'fill', style: { background:
    'radial-gradient(60% 70% at 52% 46%, #ffb21f 0%, #ff8a00 32%, #ff5e00 62%, #c22700 100%)' } });
  const flare = h('div', { class: 'abs', style: { left: '-300px', top: '-360px', width: '1400px', height: '1000px', borderRadius: '50%',
    background: 'radial-gradient(closest-side, rgba(255,250,220,.95), rgba(255,210,90,.55) 35%, rgba(255,140,0,0) 75%)', mixBlendMode: 'screen' } });

  // speed streaks
  const streakBox = h('div', { class: 'fill', style: { transform: 'rotate(-16deg) scale(1.4)' } });
  const streaks = Array.from({ length: 16 }, (_, i) => {
    const e = h('div', { class: 'abs', style: { left: '0', top: `${(i * 97) % 1080}px`, width: `${500 + (i * 131) % 700}px`, height: `${2 + (i % 3) * 2}px`, borderRadius: '4px',
      background: 'linear-gradient(90deg, rgba(255,255,255,0), rgba(255,246,210,.85), rgba(255,255,255,0))', filter: 'blur(1px)' } });
    streakBox.append(e); return { e, speed: 2600 + (i * 373) % 1800, off: (i * 523) % 2600 };
  });
  // sparks
  const sparks = Array.from({ length: 34 }, (_, i) => {
    const sz = 3 + (i % 4) * 2;
    const e = h('div', { class: 'abs', style: { width: `${sz}px`, height: `${sz}px`, borderRadius: '50%', background: '#fff6d0', boxShadow: '0 0 12px 4px rgba(255,200,80,.8)' } });
    return { e, x0: (i * 211) % 1920, y0: 1080 + (i * 89) % 600, vx: 120 + (i * 37) % 160, vy: 380 + (i * 53) % 420 };
  });
  const sparkBox = h('div', { class: 'fill' }, ...sparks.map(s => s.e));

  // film strips (as on the banner) drifting at the corners
  const strip = (w) => {
    const e = h('div', { class: 'abs', style: { width: `${w}px`, height: '210px', borderRadius: '16px', background: 'rgba(30,18,10,.78)', boxShadow: '0 30px 60px rgba(90,20,0,.35)', overflow: 'hidden' } });
    for (let r = 0; r < 2; r++) {
      const row = h('div', { class: 'abs', style: { left: '0', right: '0', [r ? 'bottom' : 'top']: '10px', height: '20px', display: 'flex', gap: '18px', paddingLeft: '14px' } });
      for (let k = 0; k < Math.ceil(w / 38); k++) row.append(h('div', { style: { flex: '0 0 20px', height: '20px', borderRadius: '4px', background: 'rgba(255,240,220,.85)' } }));
      e.append(row);
    }
    const frames = h('div', { class: 'abs', style: { left: '14px', right: '14px', top: '42px', bottom: '42px', display: 'flex', gap: '12px' } });
    const ids = Object.keys(window.K.CLIPS);
    for (let k = 0; k < Math.ceil(w / 230); k++) {
      const id = ids[(k * 3 + w) % Math.max(1, ids.length)];
      frames.append(h('div', { style: { flex: '0 0 210px', borderRadius: '8px', background: id ? `#222 url(assets/work/thumbs/${id}.jpg) center/cover` : '#3a2a20' } }));
    }
    e.append(frames);
    return e;
  };
  const stripA = strip(1400), stripB = strip(1300);

  // DESIGNER
  const word = h('div', { class: 'abs', style: { left: '0', right: '0', top: '330px', textAlign: 'center', whiteSpace: 'nowrap',
    font: '400 390px/1 Anton, Impact, sans-serif', letterSpacing: '0.005em', transform: 'skewX(-7deg)', filter: 'drop-shadow(0 26px 50px rgba(120,25,0,.45))' } });
  const letters = 'DESIGNER'.split('').map(ch => {
    const s = h('span', { class: 'sp', style: { background: 'linear-gradient(180deg,#ffffff 0%, #fffaf3 55%, #ffe3c6 100%)',
      WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' } }, ch);
    word.append(s); return s;
  });

  // Aminur
  const me = h('img', { src: 'assets/me/cutout.png', class: 'abs', style: { height: '1010px', left: '418px', bottom: '-40px', filter: 'drop-shadow(0 30px 60px rgba(90,20,0,.45))' } });
  const rim = h('div', { class: 'abs', style: { left: '700px', bottom: '0', width: '760px', height: '900px', borderRadius: '50%',
    background: 'radial-gradient(closest-side, rgba(255,240,200,.55), rgba(255,200,80,0))', filter: 'blur(30px)' } });

  // MOTION brush lettering and signature, both lifted from the banner
  const motion = h('img', { src: 'assets/me/motion.png', class: 'abs', style: { left: '262px', top: '150px', width: '660px', transform: 'rotate(-5deg)',
    filter: 'drop-shadow(0 14px 24px rgba(110,25,0,.5))' } });
  const sig = h('img', { src: 'assets/me/signature.png', class: 'abs', style: { left: '1150px', top: '760px', width: '720px', filter: 'drop-shadow(0 8px 18px rgba(110,25,0,.45))' } });

  // tool icons
  const tile = (html, bgc, glow) => h('div', { class: 'abs', style: { width: '210px', height: '210px', borderRadius: '50px', background: bgc, display: 'grid', placeItems: 'center',
    boxShadow: `0 0 0 3px rgba(255,255,255,.12) inset, 0 0 60px ${glow}, 0 30px 60px rgba(60,10,0,.45)` }, html });
  const pr = tile('<span style="font:700 112px/1 Poppins;color:#a6a6ff;letter-spacing:-.04em">Pr</span>', 'linear-gradient(150deg,#2b1a8f,#0a0656 70%)', 'rgba(140,120,255,.65)');
  const ae = tile('<span style="font:700 112px/1 Poppins;color:#a6a6ff;letter-spacing:-.04em">Ae</span>', 'linear-gradient(150deg,#2b1a8f,#0a0656 70%)', 'rgba(140,120,255,.65)');
  const sp = tile('<svg viewBox="0 0 100 100" width="120" height="120"><g stroke="#fff" stroke-width="8" stroke-linecap="round">' +
    Array.from({ length: 10 }, (_, i) => { const a = i * Math.PI / 5; return `<line x1="${50 + Math.cos(a) * 12}" y1="${50 + Math.sin(a) * 12}" x2="${50 + Math.cos(a) * 44}" y2="${50 + Math.sin(a) * 44}"/>`; }).join('') +
    '</g></svg>', 'linear-gradient(150deg,#ff9a6a,#ef5a28 70%)', 'rgba(255,160,90,.75)');
  const icons = [
    { e: pr, x: 30, y: 70, from: [-500, -400], r: -12, at: 12.78 },
    { e: ae, x: 1500, y: 90, from: [500, -420], r: 10, at: 12.86 },
    { e: sp, x: 1640, y: 470, from: [600, 120], r: 8, at: 12.94 },
  ];

  const flash = h('div', { class: 'fill', style: { background: '#fff8e8', opacity: '0' } });
  const cam = h('div', { class: 'fill' }, bg, flare, streakBox, stripA, stripB, sparkBox, word, rim, me, motion, sig, ...icons.map(i => i.e));
  root.append(cam, flash);

  scene('s10', 12.0, 16.05, (lt, t) => {
    // impact: flash + decaying shake + push-in
    flash.style.opacity = (kf(t, [[12.0, 0.9], [12.28, 0, E.outCubic]]) + kf(t, [[15.8, 0], [16.05, 1, E.inCubic]])).toFixed(3);
    const shake = Math.exp(-(t - 12.0) * 7) * 16;
    const push = kf(t, [[12.0, 1.08], [12.6, 1.0, E.outExpo], [15.7, 1.05, E.lin], [16.05, 1.3, E.inCubic]]);
    set(cam, { x: Math.sin(t * 70) * shake, y: Math.cos(t * 55) * shake * 0.7, s: push, blur: P(t, 15.75, 16.05, E.inCubic) * 18 });

    flare.style.opacity = (0.75 + 0.25 * Math.sin(t * 3.1)).toFixed(3);
    streaks.forEach(s => { s.e.style.transform = `translateX(${(((t - 12) * s.speed + s.off) % 3200) - 900}px)`; });
    sparks.forEach(s => {
      const k = t - 12;
      set(s.e, { x: s.x0 + s.vx * k, y: ((s.y0 - s.vy * k) % 1400 + 1400) % 1400 - 200, o: 0.85 });
    });
    set(stripA, { x: kf(t, [[12.0, -900], [12.7, -260, E.outExpo], [16.05, -120]]), y: 840, r: -14, blur: 3 });
    set(stripB, { x: kf(t, [[12.0, 1900], [12.75, 1260, E.outExpo], [16.05, 1140]]), y: -60, r: -14, blur: 3 });

    letters.forEach((l, i) => {
      const a = 12.02 + i * 0.035;
      const k = P(t, a, a + 0.42, E.outExpo);
      set(l, { o: P(t, a, a + 0.06), s: mix(2.1, 1, k), y: mix(-40, 0, k), blur: (1 - k) * 26 });
    });

    const mk = P(t, 12.15, 12.8, E.outExpo);
    set(me, { y: mix(560, 0, mk), s: mix(0.94, 1, mk), o: P(t, 12.15, 12.3) });
    rim.style.opacity = (mk * (0.8 + 0.2 * Math.sin(t * 2.4))).toFixed(3);

    const wk = P(t, 12.55, 13.0, E.outExpo);
    motion.style.clipPath = `inset(0 ${((1 - wk) * 100).toFixed(2)}% 0 0)`;
    motion.style.transform = `rotate(-5deg) translateX(${mix(-90, 0, wk).toFixed(1)}px)`;

    icons.forEach((ic, i) => {
      const k = P(t, ic.at, ic.at + 0.55, E.outBack);
      const bob = Math.sin((t - 12) * 2.2 + i * 1.7) * 14;
      set(ic.e, { x: ic.x + ic.from[0] * (1 - k), y: ic.y + ic.from[1] * (1 - k) + bob, r: ic.r + (1 - k) * 90 + Math.sin((t - 12) * 1.6 + i) * 3,
        s: mix(0.4, 1, k), o: P(t, ic.at, ic.at + 0.1), blur: (1 - P(t, ic.at, ic.at + 0.35)) * 14, rx: Math.sin((t - 12) * 1.3 + i) * 10, persp: 900 });
    });

    const sk = P(t, 13.15, 14.15, E.inOutCubic);
    sig.style.clipPath = `inset(-20px ${((1 - sk) * 100).toFixed(2)}% -20px 0)`;
  });
})();
