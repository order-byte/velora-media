// S2 · Client chat (3.86–8.0s)
// iMessage-style bubbles type themselves in (fresh letters glow magenta, then settle),
// emoji stickers pop on, the thread scrolls up as the conversation grows.
(() => {
  const { h, P, E, mix, kf, set, split, typeIn, scene } = window.V;
  const root = document.getElementById('s2');
  root.style.background = '#eeeef2';

  const thread = h('div', { class: 'fill' });
  const cam = h('div', { class: 'fill' }, thread);
  const veil = h('div', { class: 'fill', style: { background: '#07060c', opacity: '0' } });
  root.append(cam, veil);

  const tailSvg = color => `<svg viewBox="0 0 30 30" width="30" height="30"><path d="M30 0C28 14 18 25 0 29c13-1 22-6 30-14Z" fill="${color}"/></svg>`;

  function bubble({ text, side, at, cps, y, sticker, stickerAt }) {
    const mine = side === 'right';
    const bg = mine ? '#2f8cff' : '#e2e2e8';
    const el = h('div', { class: 'abs', style: {
      top: `${y}px`, [mine ? 'right' : 'left']: '360px',
      padding: '30px 46px', borderRadius: '48px', background: bg,
      font: '500 50px/1.25 Poppins', color: mine ? '#fff' : '#1b1b22', whiteSpace: 'nowrap',
      boxShadow: mine ? '0 14px 40px rgba(47,140,255,.28)' : '0 10px 30px rgba(30,30,60,.06)',
      transformOrigin: mine ? '100% 100%' : '0% 100%' } });
    const label = h('span', {}, text);
    const caret = h('span', { style: { display: 'inline-block', width: '3px', height: '52px', marginLeft: '3px', verticalAlign: '-8px', background: mine ? '#fff' : '#c43cff', borderRadius: '2px' } });
    el.append(label, caret);
    const chars = split(label, 'chars');
    const tail = h('div', { class: 'abs', style: { bottom: '-2px', [mine ? 'right' : 'left']: '-10px', transform: mine ? 'none' : 'scaleX(-1)' }, html: tailSvg(bg) });
    el.append(tail);
    let stick = null;
    if (sticker) {
      stick = h('div', { class: 'abs', style: {
        top: '-58px', [mine ? 'left' : 'right']: '-74px', width: '104px', height: '104px', borderRadius: '50%',
        background: 'radial-gradient(circle at 35% 30%, #6cc2ff, #2b8cff 70%)', boxShadow: '0 10px 26px rgba(43,140,255,.35), inset 0 2px 0 rgba(255,255,255,.5)',
        display: 'grid', placeItems: 'center', font: '56px/1 "Noto Color Emoji", "Apple Color Emoji", sans-serif' } }, sticker);
      const dot = h('div', { class: 'abs', style: { width: '18px', height: '18px', borderRadius: '50%', background: '#2b8cff', bottom: '-4px', [mine ? 'right' : 'left']: '-4px' } });
      stick.append(dot);
      el.append(stick);
    }
    thread.append(el);
    return { el, chars, caret, at, cps, stick, stickerAt, mine };
  }

  const B = [
    bubble({ text: 'Hey Aminur! We launch next week 🚀', side: 'left', at: 3.94, cps: 46, y: 330, sticker: '💜', stickerAt: 4.78 }),
    bubble({ text: 'Need a promo that actually stops the scroll', side: 'left', at: 4.92, cps: 56, y: 505 }),
    bubble({ text: 'Say less. I got you 🔥', side: 'right', at: 5.92, cps: 40, y: 680, sticker: '🔥', stickerAt: 6.5 }),
    bubble({ text: 'Let’s gooo 🙌', side: 'left', at: 6.82, cps: 30, y: 855 }),
  ];

  scene('s2', 3.86, 8.02, (lt, t) => {
    // thread scrolls up as messages arrive; gentle settle on the camera
    const scroll = kf(t, [[5.7, 0], [6.1, -110, E.outExpo], [6.65, -110], [7.05, -215, E.outExpo]]);
    set(thread, { y: scroll });
    const camS = kf(t, [[3.86, 1.06], [5.2, 1.0, E.outCubic], [7.5, 1.0], [8.02, 1.12, E.inCubic]]);
    set(cam, { s: camS, blur: kf(t, [[7.55, 0], [8.0, 14, E.inCubic]]) });
    veil.style.opacity = P(t, 7.62, 8.0, E.inOutCubic).toFixed(3);

    for (const b of B) {
      const k = P(t, b.at - 0.12, b.at + 0.38, E.outBack);
      const fade = P(t, b.at - 0.12, b.at + 0.12, E.outCubic);
      set(b.el, { o: fade, s: mix(0.6, 1, k), y: mix(30, 0, P(t, b.at - 0.12, b.at + 0.3, E.outExpo)), blur: mix(10, 0, fade) });
      const shown = typeIn(b.chars, t, b.at, b.cps, b.mine
        ? { accent: [200, 255, 0], base: [255, 255, 255], settle: 0.28 }
        : { accent: [204, 60, 255], base: [27, 27, 34], settle: 0.32 });
      const typing = shown > 0 && shown < b.chars.length;
      b.caret.style.display = typing ? 'inline-block' : 'none';
      if (b.stick) {
        const sk = P(t, b.stickerAt, b.stickerAt + 0.42, E.outBack);
        set(b.stick, { o: P(t, b.stickerAt, b.stickerAt + 0.1), s: mix(0.2, 1, sk), r: mix(-35, 0, sk) });
      }
    }
  });
})();
