// S7 · Services (21.95–24.05s)
// Tilted rows of service pills race across a red glow (reference 4) while a counter
// in the middle runs up to Aminur's "1000+ videos delivered".
(() => {
  const { h, P, E, mix, kf, set, split, blurIn, scene } = window.V;
  const root = document.getElementById('s7');
  root.style.background = 'radial-gradient(90% 80% at 50% 55%, #ff4a24 0%, #d01a10 38%, #5a0707 74%, #160202 100%)';

  const ico = {
    play: '<svg viewBox="0 0 24 24" width="62" height="62"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.4-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5Z" fill="currentColor"/></svg>',
    spark: '<svg viewBox="0 0 24 24" width="62" height="62"><path fill="currentColor" d="M12 1.5c.6 4.9 2.6 8 9 10.5-6.4 2.5-8.4 5.6-9 10.5-.6-4.9-2.6-8-9-10.5 6.4-2.5 8.4-5.6 9-10.5Z"/></svg>',
    bolt: '<svg viewBox="0 0 24 24" width="62" height="62"><path fill="currentColor" d="M13.5 2 4 13.5h6.5L9.5 22 20 9.5h-6.6L13.5 2Z"/></svg>',
    layers: '<svg viewBox="0 0 24 24" width="62" height="62" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/></svg>',
    phone: '<svg viewBox="0 0 24 24" width="62" height="62" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="6" y="2.5" width="12" height="19" rx="3"/><path d="M10.5 18.5h3" stroke-linecap="round"/></svg>',
    cursor: '<svg viewBox="0 0 24 24" width="62" height="62"><path fill="currentColor" d="M5 3v16.5l4.3-4 2.8 6.5 3-1.3-2.8-6.4 6-.3Z"/></svg>',
  };
  const ROWS = [
    [['play', 'Promo Videos'], ['spark', 'Motion Graphics'], ['phone', 'Reels'], ['bolt', 'SaaS Launches']],
    [['layers', 'Product Demos'], ['cursor', 'UI Animation'], ['play', 'Ads'], ['spark', 'Explainers']],
    [['bolt', 'Brand Films'], ['phone', 'App Promos'], ['layers', 'Kinetic Type'], ['play', 'Launch Trailers']],
    [['spark', 'Social Cuts'], ['cursor', 'Web Demos'], ['bolt', 'Hooks that hit'], ['phone', 'Story Edits']],
  ];
  const plane = h('div', { class: 'center', style: { width: '0', height: '0' } });
  const rows = ROWS.map((items, r) => {
    const row = h('div', { class: 'abs', style: { left: '-3000px', top: `${(r - 1.5) * 190 - 80}px`, display: 'flex', gap: '28px', whiteSpace: 'nowrap' } });
    for (let rep = 0; rep < 4; rep++) {
      items.forEach(([ic, label], j) => {
        const hot = r === 1 && j === 0 && rep === 1;
        row.append(h('div', { style: { display: 'flex', alignItems: 'center', gap: '22px', padding: '22px 46px 22px 34px', borderRadius: '999px',
          font: '600 78px/1 Poppins', letterSpacing: '-0.03em', color: hot ? '#12160a' : '#fff',
          background: hot ? '#c8ff00' : 'rgba(30,0,0,.38)', boxShadow: hot ? '0 0 60px rgba(200,255,0,.45)' : 'inset 0 0 0 2px rgba(255,255,255,.14), 0 20px 50px rgba(40,0,0,.35)' },
          html: `${ico[ic]}<span>${label}</span>` }));
      });
    }
    plane.append(row);
    return { row, dir: r % 2 ? 1 : -1, off: r * 310 };
  });

  // counter
  const counter = h('div', { class: 'center', style: { transform: 'translate(-50%,-50%)', textAlign: 'center', whiteSpace: 'nowrap', padding: '40px 80px 46px', borderRadius: '48px',
    background: 'rgba(18,2,2,.62)', backdropFilter: 'blur(26px) saturate(1.3)', WebkitBackdropFilter: 'blur(26px) saturate(1.3)',
    boxShadow: 'inset 0 0 0 1.5px rgba(255,255,255,.18), inset 0 1.5px 0 rgba(255,255,255,.35), 0 40px 120px rgba(20,0,0,.55)' } });
  const num = h('div', { style: { font: '700 230px/1 Poppins', letterSpacing: '-0.05em', color: '#fff', fontVariantNumeric: 'tabular-nums' } });
  const numVal = h('span', {}, '0');
  const plus = h('span', { style: { color: '#c8ff00', display: 'inline-block' } }, '+');
  num.append(numVal, plus);
  const sub = h('div', { style: { font: '500 50px/1.2 Poppins', color: 'rgba(255,255,255,.88)', marginTop: '10px', letterSpacing: '-0.01em' } }, 'videos delivered for clients');
  const subW = split(sub, 'words');
  counter.append(num, sub);

  root.append(plane, counter);

  scene('s7', 21.95, 24.05, (lt, t) => {
    root.style.opacity = P(t, 21.95, 22.12).toFixed(3);
    const speedBlur = kf(t, [[21.95, 1], [22.5, 0.15, E.outCubic], [23.7, 0.15], [24.05, 1, E.inCubic]]);
    rows.forEach(r => {
      // fast entrance that settles into a cruise
      const dist = kf(t, [[21.95, 0], [22.5, 900, E.outCubic], [23.7, 1300, E.lin], [24.05, 2300, E.inCubic]]);
      set(r.row, { x: r.dir * dist + r.off - 600 * r.dir, blur: speedBlur * 16 });
    });
    plane.style.transform = `rotate(-9deg) scale(${kf(t, [[21.95, 1.35], [22.6, 1.12, E.outCubic], [24.05, 1.2]]).toFixed(4)})`;

    const ck = P(t, 22.38, 22.8, E.outBack);
    counter.style.opacity = P(t, 22.38, 22.55).toFixed(3);
    counter.style.transform = `translate(-50%,-50%) scale(${(mix(0.7, 1, ck) * kf(t, [[23.6, 1], [24.05, 1.5, E.inCubic]])).toFixed(4)})`;
    counter.style.filter = t > 23.7 ? `blur(${(P(t, 23.7, 24.05, E.inCubic) * 20).toFixed(2)}px)` : 'none';
    const n = Math.round(1000 * P(t, 22.45, 23.25, E.outExpo));
    numVal.textContent = n.toLocaleString('en-US');
    const pk = P(t, 23.2, 23.45, E.outBack);
    set(plus, { o: P(t, 23.2, 23.28), s: mix(0.2, 1, pk), r: mix(-90, 0, pk) });
    blurIn(subW, t, 22.62, { stagger: 0.05, dur: 0.4, blur: 14, dy: 20 });
  });
})();
