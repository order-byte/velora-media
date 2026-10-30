// S1 · Glass hook (0–4s)
// Violet frost -> fluted glass melts and clouds part to reveal a mountain meadow (as in
// reference 5) -> a liquid-glass prompt pill rises with a neon orbit behind it, types
// the hook, answers, then swallows the screen.
(() => {
  const { h, P, E, mix, kf, set, split, typeIn, blurIn, blurOut, scene, clamp } = window.V;
  const { icon } = window.K;
  const root = document.getElementById('s1');

  // the meadow photo is laid out like background-size: cover (2560x1707 -> 1920x1280)
  const IMG = 'assets/bg/meadow.jpg', IW = 1920, IH = 1280, IY = -100;
  const photoBg = (zoom, sq, cx, ex) => {
    // horizontal squeeze sq about cx (for the glass ribs), uniform zoom about the frame centre
    const w = IW * zoom * sq, hgt = IH * zoom;
    const x = cx + (960 + (0 - 960) * zoom - cx) * sq - ex; // image left edge, squeezed about cx
    const y = 540 + (IY - 540) * zoom;
    return { backgroundImage: `url(${IMG})`, backgroundRepeat: 'no-repeat', backgroundSize: `${w.toFixed(1)}px ${hgt.toFixed(1)}px`, backgroundPosition: `${x.toFixed(1)}px ${y.toFixed(1)}px` };
  };
  const sky = h('div', { class: 'fill' });
  const veilViolet = h('div', { class: 'fill', style: { background: 'linear-gradient(180deg, #5b4bff 0%, #8a7bff 55%, #c3b6ff 100%)' } });
  // cloud banks the camera pushes through
  const CLOUDS = [[260, 260, 1500, 900], [1640, 240, 1500, 900], [960, 820, 2200, 900], [120, 880, 1300, 800], [1800, 860, 1300, 800], [960, 420, 1500, 900], [600, 560, 1200, 700], [1340, 600, 1200, 700]];
  const cloudBox = h('div', { class: 'fill' });
  const clouds = CLOUDS.map(([x, y, w, hh]) => {
    const e = h('div', { class: 'abs', style: { left: `${x - w / 2}px`, top: `${y - hh / 2}px`, width: `${w}px`, height: `${hh}px`, borderRadius: '50%',
      background: 'radial-gradient(closest-side, rgba(255,255,255,.82), rgba(250,248,255,.55) 50%, rgba(255,255,255,0))', filter: 'blur(36px)' } });
    cloudBox.append(e); return { e, x, y };
  });
  // fluted glass: vertical ribs, each showing a horizontally squeezed copy of the sky
  const RIBS = 16, RW = 1920 / RIBS;
  const flutes = h('div', { class: 'fill' });
  const ribs = Array.from({ length: RIBS }, (_, i) => {
    const rib = h('div', { class: 'abs', style: { left: `${i * RW}px`, top: '0', width: `${RW + 0.5}px`, height: '1080px', overflow: 'hidden' } });
    const shade = h('div', { class: 'fill', style: {
      background: 'linear-gradient(90deg, rgba(255,255,255,.30) 0%, rgba(255,255,255,0) 22%, rgba(40,10,120,.10) 62%, rgba(255,255,255,.18) 88%, rgba(255,255,255,.55) 99%, rgba(255,255,255,0) 100%)' } });
    rib.append(shade);
    flutes.append(rib);
    return { rib, shade, cx: i * RW + RW / 2 };
  });
  const glint = h('div', { class: 'fill', style: {
    background: 'linear-gradient(105deg, rgba(255,255,255,0) 40%, rgba(255,255,255,.55) 49%, rgba(255,255,255,.0) 51%, rgba(255,255,255,.22) 54%, rgba(255,255,255,0) 60%)',
    mixBlendMode: 'soft-light', backgroundSize: '200% 100%' } });

  // neon orbit behind the pill
  const orbitWrap = h('div', { class: 'center', style: { width: '0', height: '0', perspective: '1400px' } });
  const ringStyle = (thick, blur) => ({
    position: 'absolute', left: '-700px', top: '-700px', width: '1400px', height: '1400px', borderRadius: '50%',
    WebkitMask: `radial-gradient(closest-side, transparent calc(100% - ${thick}px), #000 calc(100% - ${thick}px), #000 100%, transparent 100%)`,
    mask: `radial-gradient(closest-side, transparent calc(100% - ${thick}px), #000 calc(100% - ${thick}px), #000 100%, transparent 100%)`,
    filter: blur ? `blur(${blur}px)` : 'none',
  });
  const ringGlow = h('div', { style: ringStyle(46, 26) });
  const ring = h('div', { style: ringStyle(7, 0) });
  orbitWrap.append(ringGlow, ring);

  // liquid glass pill
  const PW = 1180, PH = 168;
  const pill = h('div', { class: 'center', style: {
    width: `${PW}px`, height: `${PH}px`, marginLeft: `${-PW / 2}px`, marginTop: `${-PH / 2}px`, borderRadius: `${PH / 2}px`,
    backdropFilter: 'blur(18px) saturate(1.6) brightness(1.06)', WebkitBackdropFilter: 'blur(18px) saturate(1.6) brightness(1.06)',
    background: 'linear-gradient(180deg, rgba(255,255,255,.30), rgba(255,255,255,.06) 55%, rgba(255,255,255,.14)), rgba(20,30,60,.16)',
    boxShadow: 'inset 0 1.5px 0 rgba(255,255,255,.95), inset 0 -1px 0 rgba(255,255,255,.45), inset 0 0 0 1.5px rgba(255,255,255,.45), inset 0 0 26px rgba(255,255,255,.35), 0 30px 80px rgba(40,10,120,.28), 0 6px 18px rgba(40,10,120,.12)',
    overflow: 'hidden' } });
  const rim = h('div', { class: 'fill', style: {
    borderRadius: 'inherit', padding: '2px',
    background: 'conic-gradient(from 210deg, rgba(200,255,0,.0), rgba(200,255,0,.85), rgba(110,231,255,.8), rgba(170,110,255,.8), rgba(255,120,220,.6), rgba(200,255,0,0))',
    WebkitMask: 'linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)', WebkitMaskComposite: 'xor',
    mask: 'linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0)', opacity: '.55' } });
  const fog = h('div', { class: 'fill', style: { background: '#eeeef2', opacity: '0' } });
  const plusBtn = h('div', { class: 'abs', style: { left: '26px', top: '33px', width: '90px', height: '90px', borderRadius: '50%',
    background: 'rgba(255,255,255,.28)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,.9), inset 0 0 0 1px rgba(255,255,255,.5)', color: '#fff', padding: '27px' }, html: icon.plus });
  const sendBtn = h('div', { class: 'abs', style: { right: '26px', top: '33px', width: '90px', height: '90px', borderRadius: '50%',
    background: '#c8ff00', color: '#141a00', padding: '24px', boxShadow: '0 8px 24px rgba(160,210,0,.45), inset 0 1px 0 rgba(255,255,255,.7)' }, html: icon.arrowUp });
  const textStyle = { left: '150px', top: '0', height: `${PH}px`, font: `500 50px/${PH}px Poppins`, color: '#fff',
    whiteSpace: 'nowrap', textShadow: '0 2px 18px rgba(10,20,50,.45)', letterSpacing: '-0.01em' };
  const text = h('div', { class: 'abs', style: textStyle }, 'Need a video that stops the scroll?');
  const caret = h('span', { style: { display: 'inline-block', width: '3px', height: '54px', background: '#fff', marginLeft: '5px', borderRadius: '2px', verticalAlign: 'middle' } });
  const chars = split(text, 'chars');
  text.append(caret);
  // the answer that replaces the question once it is sent
  const reply = h('div', { class: 'abs', style: textStyle });
  const replyA = h('span', {}, 'Say less.');
  const replyB = h('span', { style: { color: '#c8ff00' } }, ' Watch this.');
  reply.append(replyA, replyB);
  const replyWords = [...split(replyA, 'words'), ...split(replyB, 'words')];
  // specular sheen that sweeps across the glass once it has landed
  const sheen = h('div', { class: 'fill', style: { background: 'linear-gradient(100deg, rgba(255,255,255,0) 35%, rgba(255,255,255,.55) 47%, rgba(255,255,255,0) 50%, rgba(255,255,255,.25) 54%, rgba(255,255,255,0) 62%)',
    backgroundSize: '250% 100%', mixBlendMode: 'overlay', opacity: '0' } });
  pill.append(rim, sheen, plusBtn, text, reply, sendBtn, fog);

  const vignette = h('div', { class: 'fill', style: { background: 'radial-gradient(120% 90% at 50% 45%, rgba(0,0,0,0) 55%, rgba(30,10,90,.28) 100%)' } });
  const cam = h('div', { class: 'fill' }, sky, flutes, veilViolet, cloudBox, glint, orbitWrap, vignette, pill);
  root.append(cam);

  const TYPE_AT = 1.38, CPS = 30;

  scene('s1', 0, 3.86, t => {
    // camera: slow push-in that settles, then a punch at the end
    const camS = kf(t, [[0, 1.14], [1.6, 1.0, E.outExpo], [3.3, 1.02, E.inOutCubic], [3.86, 1.18, E.inExpo]]);
    set(cam, { s: camS });

    // fluted glass melts: ribs stop squeezing, shading fades, then they are removed
    const melt = P(t, 0.3, 1.5, E.inOutQuart);
    const zoom = kf(t, [[0, 1.22], [1.7, 1.04, E.outCubic], [3.86, 1.0, E.lin]]);
    if (melt < 1) {
      flutes.style.display = 'block'; sky.style.display = 'none';
      ribs.forEach(({ rib, shade, cx }, i) => {
        const local = clamp(melt * 1.25 - (Math.abs(i - RIBS / 2) / RIBS) * 0.25);
        const sq = mix(0.25, 1, E.inOutCubic(local));
        Object.assign(rib.style, photoBg(zoom * mix(1.06, 1, local), sq, cx, cx - RW / 2));
        shade.style.opacity = (1 - E.outCubic(local)).toFixed(3);
      });
    } else {
      flutes.style.display = 'none'; sky.style.display = 'block';
      Object.assign(sky.style, photoBg(zoom, 1, 960, 0));
    }
    // flat violet open (reference 5) that dissolves into the clouds
    veilViolet.style.opacity = (1 - P(t, 0.0, 0.85, E.inOutCubic)).toFixed(3);
    flutes.style.filter = `blur(${(kf(t, [[0, 6], [1.2, 0, E.outCubic]])).toFixed(2)}px) saturate(1.12)`;
    sky.style.filter = 'saturate(1.12) contrast(1.03)';
    clouds.forEach((c, i) => {
      const k = P(t, 0.15 + i * 0.05, 1.45 + i * 0.04, E.inOutCubic);
      const dx = (c.x - 960) * k * 1.4, dy = (c.y - 540) * k * 1.2;
      set(c.e, { x: dx, y: dy, s: 1 + k * 1.6, o: 1 - k });
    });
    cloudBox.style.display = t < 1.8 ? 'block' : 'none';
    glint.style.backgroundPosition = `${kf(t, [[0.1, 140], [1.25, -60, E.inOutCubic]])}% 0`;
    glint.style.opacity = (P(t, 0.1, 0.3) * (1 - P(t, 1.1, 1.4))).toFixed(3);

    // orbit ring
    const ringIn = P(t, 0.85, 1.7, E.outExpo);
    const spin = 40 + t * 70 + kf(t, [[2.7, 0], [3.4, 220, E.inOutCubic]]);
    const tilt = mix(64, 72, ringIn);
    const rs = mix(0.55, 1, ringIn) * kf(t, [[2.7, 1], [3.1, 1.06, E.outCubic], [3.86, 1.4, E.inCubic]]);
    const grad = `conic-gradient(from ${spin}deg, rgba(200,255,0,0) 0deg, rgba(200,255,0,1) 70deg, #6ee7ff 140deg, #a56bff 210deg, rgba(255,110,210,.9) 260deg, rgba(255,110,210,0) 330deg)`;
    ring.style.background = grad; ringGlow.style.background = grad;
    for (const r of [ring, ringGlow]) r.style.transform = `rotateX(${tilt}deg) scale(${rs})`;
    orbitWrap.style.opacity = (ringIn * (1 - P(t, 3.45, 3.8))).toFixed(3);
    ringGlow.style.opacity = (0.75 + 0.25 * Math.sin(t * 6)).toFixed(3);

    // pill rises out of the frost
    const pin = P(t, 0.9, 1.75, E.outExpo);
    const press = kf(t, [[2.62, 1], [2.72, 0.94, E.outCubic], [2.98, 1, E.outBack]]);
    // final swallow: the pill grows to cover the frame and fogs to the next scene's grey
    const grow = P(t, 3.24, 3.86, E.inOutCubic);
    const w = mix(PW, 2300, grow), hh = mix(PH, 1400, grow);
    set(pill, {
      o: pin, y: mix(110, 0, pin), s: mix(0.86, 1, pin) * press, blur: mix(22, 0, pin),
      width: `${w}px`, height: `${hh}px`, marginLeft: `${-w / 2}px`, marginTop: `${-hh / 2}px`, borderRadius: `${mix(PH / 2, 0, E.inCubic(grow))}px`,
    });
    fog.style.opacity = P(t, 3.3, 3.84, E.smooth).toFixed(3);
    sheen.style.backgroundPosition = `${kf(t, [[1.7, 120], [2.5, -20, E.inOutCubic]])}% 0`;
    sheen.style.opacity = (P(t, 1.7, 1.85) * (1 - P(t, 2.35, 2.5))).toFixed(3);
    const btnIn = P(t, 1.15, 1.7, E.outBack);
    set(plusBtn, { o: btnIn, s: mix(0.5, 1, btnIn) });
    const sendIn = P(t, 1.25, 1.8, E.outBack);
    const sendPress = kf(t, [[2.55, 1], [2.65, 0.82, E.outCubic], [2.95, 1, E.outBack]]);
    set(sendBtn, { o: sendIn, s: mix(0.5, 1, sendIn) * sendPress, r: mix(-90, 0, sendIn) });
    plusBtn.style.top = sendBtn.style.top = `${(hh - 90) / 2}px`;
    text.style.height = reply.style.height = text.style.lineHeight = reply.style.lineHeight = `${hh}px`;

    const shown = typeIn(chars, t, TYPE_AT, CPS, { accent: [200, 255, 0], base: [255, 255, 255], settle: 0.3, blur: 8 });
    const typing = t >= TYPE_AT && shown < chars.length;
    caret.style.opacity = (t > 1.2 && t < 2.62 && (typing || Math.floor(t * 2.4) % 2 === 0)) ? 1 : 0;
    if (t > 2.66) blurOut(chars, t, 2.66, { stagger: 0.008, dur: 0.32, blur: 16, dy: -30 });
    blurIn(replyWords, t, 2.86, { stagger: 0.06, dur: 0.45, blur: 18, dy: 34 });
    reply.style.opacity = (1 - P(t, 3.34, 3.6)).toFixed(3);
  });
})();
