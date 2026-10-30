// S4 · Gradient title (9.98–14.02s)
// The flood from the prompt settles into a soft liquid wave; "Ready to launch?" writes
// itself in, the wave climbs back over the frame for the name reveal, then wipes off
// to a rapid "Promos for <category>" swap.
(() => {
  const { h, P, E, mix, kf, set, split, blurIn, blurOut, scene, clamp } = window.V;
  const C = window.CFG;
  const root = document.getElementById('s4');
  root.style.background = '#fbfafc';

  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', '0 0 1920 1080'); svg.setAttribute('width', '1920'); svg.setAttribute('height', '1080');
  svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;filter:blur(26px)';
  svg.innerHTML = `
    <defs>
      <linearGradient id="s4g" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#ffb347"/><stop offset=".22" stop-color="#ff6a3d"/>
        <stop offset=".5" stop-color="#ff2d78"/><stop offset=".78" stop-color="#e22cff"/><stop offset="1" stop-color="#8a2cff"/>
      </linearGradient>
      <linearGradient id="s4g2" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="#ff7a59" stop-opacity=".0"/><stop offset=".5" stop-color="#ff9a6b" stop-opacity=".85"/><stop offset="1" stop-color="#ff4fa3" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <path id="s4w2" fill="url(#s4g2)"/>
    <path id="s4w1" fill="url(#s4g)"/>`;
  const w1 = svg.querySelector('#s4w1'), w2 = svg.querySelector('#s4w2');
  function wavePath(base, amp, t, k = 1, ph = 0) {
    let d = `M -200 1400 L -200 ${base}`;
    for (let x = -200; x <= 2120; x += 40) {
      const y = base + amp * (Math.sin(x / 260 * k + t * 2.2 + ph) * 0.6 + Math.sin(x / 520 * k - t * 1.4 + ph * 2) * 0.4);
      d += ` L ${x} ${y.toFixed(1)}`;
    }
    return d + ' L 2120 1400 Z';
  }

  const title = h('div', { class: 'abs', style: { left: '0', right: '0', top: '330px', textAlign: 'center', font: '700 150px/1 Poppins', letterSpacing: '-0.04em', whiteSpace: 'nowrap' } }, 'Ready to launch?');
  const tChars = split(title, 'chars');
  // magenta -> coral across the word
  tChars.forEach((c, i) => {
    const k = i / (tChars.length - 1);
    const a = [226, 44, 255], b = [255, 92, 58];
    c.style.color = `rgb(${a.map((v, j) => Math.round(mix(v, b[j], k)))})`;
  });

  // name reveal on the full gradient
  const mark = h('div', { class: 'center', style: { transform: 'translate(-50%,-50%)', display: 'flex', alignItems: 'center', gap: '34px', whiteSpace: 'nowrap' } });
  const logo = h('div', { style: { width: '150px', height: '150px', borderRadius: '42px', background: '#c8ff00', display: 'grid', placeItems: 'center',
    boxShadow: '0 20px 60px rgba(120,20,80,.35), inset 0 2px 0 rgba(255,255,255,.7)' },
    html: '<svg viewBox="0 0 24 24" width="70" height="70"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.4-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5Z" fill="#12160a"/></svg>' });
  const word = h('div', { style: { font: '700 160px/1 Poppins', color: '#fff', letterSpacing: '-0.045em', textShadow: '0 10px 50px rgba(120,10,60,.25)' } }, C.handle.replace('@', ''));
  mark.append(logo, word);
  const wChars = split(word, 'chars');

  // "Promos for <category>"
  const cats = ['SaaS', 'Gaming', 'EdTech', 'AI tools', 'Tech brands'];
  const line = h('div', { class: 'abs', style: { left: '0', right: '0', top: '470px', textAlign: 'center', font: '600 120px/1.1 Poppins', letterSpacing: '-0.035em', color: '#16161d', whiteSpace: 'nowrap' } });
  const lead = h('span', {}, 'Promos for ');
  const slot = h('span', { style: { display: 'inline-block', position: 'relative', width: '760px', height: '140px', verticalAlign: 'top', textAlign: 'left' } });
  const catEls = cats.map(c => {
    const e = h('span', { style: { position: 'absolute', left: '0', top: '0', whiteSpace: 'nowrap', background: 'linear-gradient(90deg,#e22cff,#ff5c3a)', WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent', paddingRight: '8px' } }, c);
    slot.append(e); return e;
  });
  line.append(lead, slot);
  const leadWords = split(lead, 'words');

  root.append(svg, title, mark, line);
  const CAT_AT = 13.08, CAT_STEP = 0.19;
  let catW = null;

  scene('s4', 9.98, 14.02, (lt, t) => {
    // wave level: full frame -> low wave -> full frame -> wiped away
    const base = kf(t, [[9.98, -260], [10.75, 760, E.outQuint], [11.55, 790], [11.95, -300, E.inOutQuint], [12.82, -300], [13.12, -1700, E.inQuint]]);
    w1.setAttribute('d', wavePath(base, 70 + 40 * Math.sin(t * 1.3), t));
    w2.setAttribute('d', wavePath(base - 120, 90, t, 0.8, 1.7));
    w2.style.opacity = (P(t, 10.3, 10.8) * (1 - P(t, 11.6, 11.9))).toFixed(3);
    svg.style.display = t < 13.15 ? 'block' : 'none';

    title.style.display = t > 10.0 && t < 11.95 ? 'block' : 'none';
    blurIn(tChars, t, 10.18, { stagger: 0.035, dur: 0.5, blur: 22, dx: -40 });
    if (t > 11.5) blurOut(tChars, t, 11.5, { stagger: 0.012, dur: 0.3, blur: 22, dy: -40 });
    set(title, { y: kf(t, [[10.1, 30], [11.5, 0, E.outCubic]]) });

    mark.style.display = t > 11.85 && t < 13.15 ? 'flex' : 'none';
    const lk = P(t, 11.9, 12.35, E.outBack);
    set(logo, { o: P(t, 11.9, 12.05), s: mix(0.3, 1, lk), r: mix(-40, 0, lk) });
    blurIn(wChars, t, 12.02, { stagger: 0.03, dur: 0.45, blur: 20, dx: -30 });
    mark.style.transform = `translate(-50%,-50%) scale(${kf(t, [[11.9, 0.94], [12.9, 1.0, E.outCubic], [13.12, 1.1, E.inCubic]])})`;
    mark.style.opacity = (1 - P(t, 12.92, 13.1)).toFixed(3);

    line.style.display = t > 12.95 ? 'block' : 'none';
    blurIn(leadWords, t, 12.98, { stagger: 0.05, dur: 0.35, blur: 16, dy: 30 });
    if (line.style.display === 'block') {
      // the slot hugs the current word so the line stays centred
      if (!catW) catW = catEls.map(e => e.offsetWidth);
      const f = clamp((t - CAT_AT) / CAT_STEP, 0, cats.length - 1);
      const i0 = Math.floor(f), i1 = Math.min(cats.length - 1, i0 + 1);
      slot.style.width = `${mix(catW[i0], catW[i1], E.inOutCubic(clamp((f - i0 - 0.55) / 0.45)))}px`;
    }
    catEls.forEach((e, i) => {
      const a = CAT_AT + i * CAT_STEP, last = i === cats.length - 1;
      const kin = P(t, a, a + 0.16, E.outCubic);
      const kout = last ? 0 : P(t, a + CAT_STEP, a + CAT_STEP + 0.12, E.inCubic);
      set(e, { o: kin * (1 - kout), y: mix(60, 0, kin) - kout * 60, blur: (1 - kin) * 14 + kout * 14 });
    });
    set(line, { s: kf(t, [[13.0, 1.04], [14.02, 1.0, E.outCubic]]), blur: P(t, 13.85, 14.02, E.inCubic) * 10 });
    line.style.opacity = (1 - P(t, 13.88, 14.02)).toFixed(3);
  });
})();
