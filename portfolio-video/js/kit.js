// Shared building blocks: the procedural sky used behind the glass, glass styling,
// and Clip, which plays a piece of Aminur's work in both the live preview (<video>)
// and the frame renderer (pre-extracted JPEG frames, so every frame is exact).
(() => {
  const { h, P, E, mix, kf, clamp } = window.V;
  const RENDER = !!window.__RENDER;

  // ---------- procedural sky (violet dusk with soft clouds) ----------
  // Blobs in source space; positions drift slowly with time.
  const BLOBS = [
    // x, y, rx, ry, rgba, vx, vy
    [300, 260, 520, 360, '255,120,220,0.55', 18, 6],
    [1500, 220, 640, 420, '120,210,255,0.55', -22, 4],
    [980, 120, 760, 380, '160,120,255,0.65', 10, -3],
    [1180, 900, 980, 260, '255,255,255,0.80', -14, 0],
    [380, 960, 820, 240, '255,255,255,0.75', 16, 0],
    [1700, 1000, 640, 220, '255,236,250,0.80', -10, 0],
    [960, 1110, 1400, 240, '255,255,255,0.95', 0, 0],
    [760, 640, 420, 200, '255,170,235,0.40', 26, -4],
    [1460, 600, 380, 180, '170,220,255,0.38', -24, 3],
  ];
  const SKY_STOPS = [[0, '#2a1bc4'], [340, '#5236ee'], [640, '#8b73ff'], [920, '#dccdff'], [1080, '#fbefff']];

  // map = { cx, cy, mx, my, ex, ey } : magnify around (cx,cy) then express in an element at (ex,ey)
  function skyBg(t, map = {}) {
    const { cx = 960, cy = 540, mx = 1, my = 1, ex = 0, ey = 0, height = 1080 } = map;
    const layers = BLOBS.map(([x, y, rx, ry, c, vx, vy]) => {
      const bx = x + vx * t, by = y + vy * t;
      const px = cx + (bx - cx) * mx - ex, py = cy + (by - cy) * my - ey;
      return `radial-gradient(${(rx * mx).toFixed(1)}px ${(ry * my).toFixed(1)}px at ${px.toFixed(1)}px ${py.toFixed(1)}px, rgba(${c}) 0%, rgba(${c.replace(/[\d.]+$/, '0')}) 100%)`;
    });
    const stops = SKY_STOPS.map(([y, col]) => `${col} ${(cy + (y - cy) * my - ey).toFixed(1)}px`).join(',');
    layers.push(`linear-gradient(180deg, ${stops})`);
    return layers.join(',');
  }

  // ---------- Clip: a looping excerpt of a work video ----------
  // spec = { id, frames, fps, w, h }  (see assets/work/clips.json, written by tools/prepare_work.sh)
  const CLIPS = window.CLIPS || {};
  function clip(id, { fit = 'cover', className = '' } = {}) {
    const spec = CLIPS[id];
    const wrap = h('div', { class: 'clip ' + className, style: { position: 'absolute', inset: '0', overflow: 'hidden', background: '#111' } });
    if (!spec) return { el: wrap, seek() {} };
    let media;
    if (RENDER) {
      media = h('img', { style: { width: '100%', height: '100%', objectFit: fit, display: 'block' } });
    } else {
      media = h('video', { src: `assets/work/preview/${id}.mp4`, muted: '', playsinline: '', preload: 'auto', style: { width: '100%', height: '100%', objectFit: fit, display: 'block' } });
      media.muted = true;
    }
    wrap.append(media);
    let lastFrame = -1;
    return {
      el: wrap,
      // lt = seconds into the clip (wraps around)
      seek(lt) {
        const len = spec.frames / spec.fps;
        const ct = ((lt % len) + len) % len;
        if (RENDER) {
          const f = Math.min(spec.frames - 1, Math.floor(ct * spec.fps + 1e-6));
          if (f !== lastFrame) {
            lastFrame = f;
            media.src = `assets/work/frames/${id}/${String(f + 1).padStart(4, '0')}.jpg`;
            window.__pending.push(media.decode().catch(() => {}));
          }
        } else if (Math.abs(media.currentTime - ct) > 0.08) {
          media.currentTime = ct;
        }
      },
    };
  }

  // ---------- small UI atoms ----------
  const icon = {
    plus: '<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
    arrowUp: '<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5.5 11.5 12 5l6.5 6.5"/></svg>',
    sparkle: '<svg viewBox="0 0 24 24" width="100%" height="100%" fill="currentColor"><path d="M12 1.5c.6 4.9 2.6 8 9 10.5-6.4 2.5-8.4 5.6-9 10.5-.6-4.9-2.6-8-9-10.5 6.4-2.5 8.4-5.6 9-10.5Z"/></svg>',
    check: '<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>',
    cursor: '<svg viewBox="0 0 28 28" width="100%" height="100%"><path d="M5 3.5v18.2l4.6-4.3 3 7 3.3-1.4-3-6.9 6.4-.2Z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>',
    mic: '<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/></svg>',
  };

  window.K = { RENDER, skyBg, clip, icon, CLIPS };
})();
