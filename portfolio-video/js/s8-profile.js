// S8 · Profile card (23.98–26.08s)
// The glass comes back for the bookend: a frosted Instagram-style card for @aminur_rex
// assembles itself, a cursor taps Follow and the follower count ticks up by one.
(() => {
  const { h, P, E, mix, kf, set, split, blurIn, scene } = window.V;
  const { icon } = window.K;
  const C = window.CFG;
  const root = document.getElementById('s8');
  root.style.background = '#1a1530';

  const blobs = h('div', { class: 'fill', style: { background:
    'radial-gradient(40% 50% at 22% 30%, rgba(200,255,0,.85), rgba(200,255,0,0) 70%),' +
    'radial-gradient(45% 55% at 80% 70%, rgba(150,90,255,.95), rgba(150,90,255,0) 70%),' +
    'radial-gradient(35% 45% at 75% 18%, rgba(110,231,255,.7), rgba(110,231,255,0) 70%),' +
    'radial-gradient(40% 50% at 30% 85%, rgba(255,110,210,.6), rgba(255,110,210,0) 70%),' +
    'linear-gradient(160deg, #2a1d6e, #120d2a)', filter: 'blur(10px)' } });

  const CW = 1320, CH = 800;
  const card = h('div', { class: 'center', style: { width: `${CW}px`, height: `${CH}px`, marginLeft: `${-CW / 2}px`, marginTop: `${-CH / 2}px`, borderRadius: '56px',
    background: 'linear-gradient(180deg, rgba(255,255,255,.22), rgba(255,255,255,.08))',
    backdropFilter: 'blur(36px) saturate(1.5)', WebkitBackdropFilter: 'blur(36px) saturate(1.5)',
    boxShadow: 'inset 0 1.5px 0 rgba(255,255,255,.7), inset 0 0 0 1.5px rgba(255,255,255,.28), inset 0 0 40px rgba(255,255,255,.10), 0 50px 140px rgba(10,5,40,.5)',
    color: '#fff', fontFamily: 'Poppins' } });

  // avatar with a story ring
  const av = h('div', { class: 'abs', style: { left: '76px', top: '76px', width: '280px', height: '280px', borderRadius: '50%', padding: '8px',
    background: 'conic-gradient(from 200deg, #c8ff00, #6ee7ff, #a56bff, #ff6ed2, #c8ff00)' } });
  const avIn = h('div', { style: { width: '100%', height: '100%', borderRadius: '50%', padding: '6px', background: '#1a1530' } });
  const avImgWrap = h('div', { style: { width: '100%', height: '100%', borderRadius: '50%', overflow: 'hidden', background: '#c8ff00', display: 'grid', placeItems: 'center',
    font: '700 96px/1 Poppins', color: '#12160a', letterSpacing: '-0.04em' } }, 'AR');
  if (C.avatar) {
    const img = h('img', { src: C.avatar, style: { width: '100%', height: '100%', objectFit: 'cover', display: 'block' } });
    img.onload = () => { avImgWrap.textContent = ''; avImgWrap.append(img); };
  }
  avIn.append(avImgWrap); av.append(avIn);

  const name = h('div', { class: 'abs', style: { left: '412px', top: '96px', font: '700 76px/1 Poppins', letterSpacing: '-0.03em', whiteSpace: 'nowrap' } }, C.handle.replace('@', ''));
  const nameChars = split(name, 'chars');
  const role = h('div', { class: 'abs', style: { left: '414px', top: '192px', font: '500 36px/1 Poppins', color: 'rgba(255,255,255,.82)', whiteSpace: 'nowrap' } }, `${C.name} | ${C.role}`);
  const stats = h('div', { class: 'abs', style: { left: '414px', top: '268px', display: 'flex', gap: '60px', font: '500 36px/1 Poppins', color: 'rgba(255,255,255,.8)', whiteSpace: 'nowrap' } });
  const statEls = [['posts', C.posts], ['followers', 2615], ['following', C.following]].map(([lab, v]) => {
    const n = h('b', { style: { color: '#fff', fontWeight: '700', marginRight: '10px', fontVariantNumeric: 'tabular-nums' } }, '0');
    const e = h('span', {}, n, lab);
    stats.append(e);
    return { e, n, v };
  });
  const bio = h('div', { class: 'abs', style: { left: '80px', top: '400px', font: '500 40px/1.5 Poppins', whiteSpace: 'nowrap' } });
  const bioLines = ['4+ Years of Video Editing 🎬', '1000+ Videos Delivered for Clients', 'Helping Brands & Creators Stand Out'].map(l => {
    const d = h('div', {}, l); bio.append(d); return d;
  });
  const btnRow = h('div', { class: 'abs', style: { left: '80px', right: '80px', bottom: '64px', display: 'flex', gap: '22px' } });
  const follow = h('div', { style: { flex: '1', height: '96px', borderRadius: '28px', background: '#c8ff00', color: '#12160a', display: 'grid', placeItems: 'center', font: '700 36px/1 Poppins', position: 'relative', overflow: 'hidden' } });
  const fLabel = h('span', {}, 'Follow');
  const fDone = h('span', { style: { position: 'absolute', inset: '0', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', background: 'rgba(255,255,255,.16)', color: '#fff' } });
  fDone.innerHTML = `<span style="width:40px;height:40px;display:inline-block">${icon.check}</span>Following`;
  follow.append(fLabel, fDone);
  const msg = h('div', { style: { flex: '1', height: '96px', borderRadius: '28px', background: 'rgba(255,255,255,.16)', boxShadow: 'inset 0 0 0 1.5px rgba(255,255,255,.25)', display: 'grid', placeItems: 'center', font: '600 36px/1 Poppins' } }, 'Book a call');
  btnRow.append(follow, msg);
  card.append(av, name, role, stats, bio, btnRow);

  const cursor = h('div', { class: 'abs', style: { width: '64px', height: '64px', left: '0', top: '0' }, html: icon.cursor });
  const ripple = h('div', { class: 'abs', style: { width: '120px', height: '120px', marginLeft: '-60px', marginTop: '-60px', borderRadius: '50%', border: '4px solid #c8ff00', opacity: '0' } });
  root.append(blobs, card, ripple, cursor);

  const TAP = 25.32;
  scene('s8', 23.98, 26.08, (lt, t) => {
    root.style.opacity = P(t, 23.98, 24.18).toFixed(3);
    blobs.style.transform = `scale(${kf(t, [[23.98, 1.25], [26.08, 1.05, E.outCubic]]).toFixed(4)}) rotate(${(t - 24) * 6}deg)`;
    const ck = P(t, 24.05, 24.65, E.outExpo);
    const out = P(t, 25.75, 26.08, E.inCubic);
    set(card, { o: P(t, 24.05, 24.25) * (1 - P(t, 25.92, 26.08)), y: mix(140, 0, ck) - out * 40, s: mix(0.88, 1, ck) * (1 + out * 0.25), blur: (1 - ck) * 18 + out * 16, rx: mix(14, 0, ck), persp: 1600 });

    const ak = P(t, 24.25, 24.75, E.outBack);
    set(av, { o: P(t, 24.25, 24.4), s: mix(0.4, 1, ak), r: mix(-30, 0, ak) });
    avIn.parentElement.style.background = `conic-gradient(from ${200 + (t - 24) * 120}deg, #c8ff00, #6ee7ff, #a56bff, #ff6ed2, #c8ff00)`;
    blurIn(nameChars, t, 24.32, { stagger: 0.02, dur: 0.4, blur: 14, dy: 24 });
    const rk = P(t, 24.5, 24.85, E.outCubic);
    set(role, { o: rk, y: mix(16, 0, rk), blur: (1 - rk) * 10 });
    const sk = P(t, 24.58, 24.95, E.outCubic);
    set(stats, { o: sk, y: mix(16, 0, sk) });
    statEls.forEach(({ n, v }, i) => {
      let val = Math.round(v * P(t, 24.6, 25.25, E.outExpo));
      if (i === 1 && t > TAP + 0.06) val = v + 1; // the tap adds a follower
      n.textContent = val.toLocaleString('en-US');
    });
    bioLines.forEach((d, i) => {
      const k = P(t, 24.7 + i * 0.1, 25.05 + i * 0.1, E.outCubic);
      set(d, { o: k, x: mix(-24, 0, k), blur: (1 - k) * 10 });
    });
    const bk = P(t, 24.9, 25.25, E.outBack);
    set(btnRow, { o: P(t, 24.9, 25.0), y: mix(40, 0, bk) });

    // cursor glides in from the lower right and taps Follow
    const fx = 960 - CW / 2 + 80 + (CW - 160 - 22) / 4, fy = 540 + CH / 2 - 64 - 48;
    const ck2 = P(t, 24.95, TAP - 0.04, E.inOutCubic);
    const press = kf(t, [[TAP - 0.04, 1], [TAP + 0.04, 0.8], [TAP + 0.2, 1, E.outBack]]);
    set(cursor, { o: P(t, 24.95, 25.05) * (1 - P(t, 25.75, 25.9)), x: mix(1500, fx, ck2) - 10, y: mix(1000, fy, ck2) - 6, s: press });
    const fk = P(t, TAP, TAP + 0.18, E.outCubic);
    fDone.style.opacity = fk.toFixed(3);
    fLabel.style.opacity = (1 - fk).toFixed(3);
    follow.style.background = fk > 0.5 ? 'rgba(255,255,255,.14)' : '#c8ff00';
    follow.style.transform = `scale(${kf(t, [[TAP - 0.02, 1], [TAP + 0.05, 0.95], [TAP + 0.3, 1, E.outBack]])})`;
    const rp = P(t, TAP, TAP + 0.45, E.outCubic);
    set(ripple, { o: rp > 0 && rp < 1 ? 1 - rp : 0, x: fx, y: fy, s: 0.4 + rp * 2.2 });
  });
})();
