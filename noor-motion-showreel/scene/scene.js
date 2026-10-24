/* Noor Motion showreel scene.
 *
 * Everything is a pure function of time: window.__render(t) poses every
 * element for second t and resolves once the frame's images are decoded.
 * The beat map mirrors the ender.vfx reference edit so its music lands on
 * the same cuts:
 *   0.00  title + cursor selection      4.45  profile card
 *   6.25  services                      7.45  chat message + send
 *  10.12  grid 1 PRODUCT VIDEOS        13.30  grid 2 UI ANIMATION
 *  17.83  grid 3 EXPLAINERS            22.60  outro / end card
 */
(() => {
  const Q = new URLSearchParams(location.search);
  const CLIPS = Q.get("clips") || "../build/clips";
  const AVATAR = "../assets/avatar.png";
  const CLIP_FPS = 30;
  const CLIP_FRAMES = 162;
  const DURATION = 25.05;

  // ---------------------------------------------------------------- math
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const E = {
    lin: (t) => t,
    outCubic: (t) => 1 - Math.pow(1 - t, 3),
    inCubic: (t) => t * t * t,
    inOutCubic: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    outQuint: (t) => 1 - Math.pow(1 - t, 5),
    outExpo: (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
    inExpo: (t) => (t <= 0 ? 0 : Math.pow(2, 10 * t - 10)),
    inOutExpo: (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2),
    inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
    outBack: (t) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
    outBackSoft: (t) => { const c1 = 0.9, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  };
  const P = (t, a, b, e = E.lin) => e(clamp((t - a) / (b - a)));
  // keyframes: [[time, value], [time, value, easeIntoThisKey], ...]
  function kf(t, keys) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const [t1, v1, e] = keys[i];
      const [t0, v0] = keys[i - 1];
      if (t <= t1) return lerp(v0, v1, (e || E.inOutCubic)(clamp((t - t0) / (t1 - t0))));
    }
    return keys[keys.length - 1][1];
  }
  const wob = (t, f, ph, amp) => Math.sin((t * f + ph) * Math.PI * 2) * amp;

  function hex(c) { const n = parseInt(c.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function mix(a, b, t) { const A = hex(a), B = hex(b); return `rgb(${A.map((v, i) => Math.round(lerp(v, B[i], t))).join(",")})`; }

  // ---------------------------------------------------------------- dom
  const $ = (s) => document.querySelector(s);
  function mk(tag, cls, parent, html) {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (html != null) el.innerHTML = html;
    if (parent) parent.appendChild(el);
    return el;
  }
  function tf(el, s) {
    let str = `translate3d(${(s.x || 0).toFixed(2)}px,${(s.y || 0).toFixed(2)}px,${(s.z || 0).toFixed(2)}px)`;
    if (s.rx) str += ` rotateX(${s.rx.toFixed(3)}deg)`;
    if (s.ry) str += ` rotateY(${s.ry.toFixed(3)}deg)`;
    if (s.rz) str += ` rotateZ(${s.rz.toFixed(3)}deg)`;
    const sc = s.sc == null ? 1 : s.sc;
    if (sc !== 1) str += ` scale(${Math.max(0.0001, sc).toFixed(4)})`;
    str += s.anchor || " translate(-50%,-50%)";
    el.style.transform = str;
    if (s.o != null) {
      el.style.opacity = clamp(s.o).toFixed(3);
      el.style.visibility = s.o <= 0.001 ? "hidden" : "visible";
    }
    if (s.blur != null) el.style.filter = s.blur > 0.05 ? `blur(${s.blur.toFixed(2)}px)` : "none";
  }
  const show = (el, on) => { el.style.display = on ? "" : "none"; };

  const world = $("#world");
  const camera = $("#camera");
  const bg = $("#bg");
  const bgGrid = $("#bgGrid");
  const glows = $("#glows");
  const waves = $("#waves");
  const chrome = $("#chrome");
  const flash = $("#flash");
  const fade = $("#fade");
  const grain = $("#grain");

  function applyCamera(c) {
    world.style.transform =
      `translateZ(${(c.z || 0).toFixed(2)}px) rotateX(${(c.rx || 0).toFixed(3)}deg) rotateY(${(c.ry || 0).toFixed(3)}deg) rotateZ(${(c.rz || 0).toFixed(3)}deg) translate3d(${(-(c.x || 0)).toFixed(2)}px,${(-(c.y || 0)).toFixed(2)}px,0)`;
    camera.style.filter = c.blur > 0.05 ? `blur(${c.blur.toFixed(2)}px)` : "none";
  }

  // 3D extruded type: stacked copies behind a gradient face.
  function extruded(text, size, { depth = 22, step = 1.6, back = "#2a0b01", front = "#c24300", glow = true } = {}) {
    const wrap = mk("div", "ext o");
    wrap.style.fontSize = size + "px";
    if (glow) {
      const g = mk("div", "glow", wrap);
      g.textContent = text;
      g.style.transform = `translateZ(${-(depth + 2) * step}px)`;
    }
    for (let i = depth; i >= 1; i--) {
      const l = mk("div", "layer", wrap);
      l.textContent = text;
      l.style.color = mix(front, back, i / depth);
      l.style.transform = `translateZ(${(-i * step).toFixed(2)}px)`;
    }
    const face = mk("div", "face", wrap);
    face.textContent = text;
    face.style.transform = "translateZ(0.5px)";
    const shine = mk("div", "shine", wrap);
    shine.textContent = text;
    shine.style.transform = "translateZ(1px)";
    shine.style.backgroundPosition = "120% 0";
    wrap._face = face;
    wrap._shine = shine;
    return wrap;
  }

  const CURSOR_SVG = '<svg width="40" height="48" viewBox="0 0 40 48"><path d="M4 3 L4 37 L13 29 L19 43 L25 40.5 L19 27 L31 27 Z" fill="#fff" stroke="#120804" stroke-width="2.4" stroke-linejoin="round"/></svg>';
  function cursor(parent) { return mk("div", "o cursor", parent, CURSOR_SVG); }
  function poseCursor(el, x, y, z, sc, o) { tf(el, { x, y, z, sc, o, anchor: " translate(-4px,-3px)" }); }

  const ICON = {
    play: (s, c = "#fff") => `<svg width="${s}" height="${s}" viewBox="0 0 24 24"><path d="M8 5.2c0-.9 1-1.4 1.7-.9l9.1 6.1c.6.4.6 1.3 0 1.7l-9.1 6.1c-.7.5-1.7 0-1.7-.9z" fill="${c}"/></svg>`,
    cursor: (s, c = "#fff") => `<svg width="${s}" height="${s}" viewBox="0 0 24 24"><path d="M5 3.5l13 6.2-5.6 1.7 3.6 6.4-2.4 1.3-3.6-6.4-4 4.2z" fill="${c}"/><path d="M17.5 2.5l.6 1.6 1.6.6-1.6.6-.6 1.6-.6-1.6-1.6-.6 1.6-.6z" fill="${c}"/></svg>`,
    bulb: (s, c = "#fff") => `<svg width="${s}" height="${s}" viewBox="0 0 24 24"><path d="M12 2.8a6.6 6.6 0 0 0-3.9 11.9c.6.5 1 1.2 1 2V17h5.8v-.3c0-.8.4-1.5 1-2A6.6 6.6 0 0 0 12 2.8z" fill="${c}"/><rect x="9.2" y="18.3" width="5.6" height="1.6" rx=".8" fill="${c}"/><rect x="10" y="20.6" width="4" height="1.5" rx=".75" fill="${c}"/></svg>`,
  };

  // ---------------------------------------------------------------- background helpers
  const BG = {
    intro: "radial-gradient(ellipse 1300px 900px at 62% 38%, #5c2309 0%, #2a0f04 42%, #0b0502 78%, #050302 100%)",
    dark: "radial-gradient(ellipse 1000px 760px at 50% 55%, #2c0f04 0%, #130703 48%, #050302 100%)",
    grid: "radial-gradient(ellipse 1500px 950px at 50% 45%, #45190a 0%, #1f0b04 48%, #080302 100%)",
    black: "#030201",
  };
  const orbs = [];
  for (let i = 0; i < 3; i++) {
    const o = mk("div", "orb", glows);
    orbs.push(o);
  }
  function orb(i, x, y, size, color, alpha) {
    const o = orbs[i];
    o.style.width = o.style.height = size + "px";
    o.style.background = `radial-gradient(circle, ${color} 0%, transparent 68%)`;
    o.style.opacity = alpha.toFixed(3);
    o.style.transform = `translate(${(x - size / 2).toFixed(1)}px,${(y - size / 2).toFixed(1)}px)`;
  }

  // grain tiles (deterministic)
  const grainTiles = [];
  (function makeGrain() {
    let seed = 1337;
    const rnd = () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
    for (let k = 0; k < 6; k++) {
      const c = document.createElement("canvas");
      c.width = c.height = 256;
      const g = c.getContext("2d");
      const im = g.createImageData(256, 256);
      for (let i = 0; i < im.data.length; i += 4) {
        const v = Math.floor(rnd() * 255);
        im.data[i] = im.data[i + 1] = im.data[i + 2] = v;
        im.data[i + 3] = 255;
      }
      g.putImageData(im, 0, 0);
      grainTiles.push(c.toDataURL());
    }
  })();

  // ================================================================ SECTION 1 — title
  const intro = (() => {
    const root = mk("div", "sec", world);
    const title = mk("div", "o", root);
    const noor = extruded("NOOR", 158, { depth: 30, step: 2.1, back: "#1c0700", front: "#b33c00" });
    const motion = extruded("MOTION", 158, { depth: 30, step: 2.1, back: "#1c0700", front: "#b33c00" });
    title.append(noor, motion);

    const tags = [
      ["Product videos", -650, -175, 40],
      ["Explainers", -600, 335, 90],
      ["UI animation", 480, 265, 70],
    ].map(([txt, x, y, z]) => {
      const el = mk("div", "o glass tag", root, `<div class="dots"><i></i><i></i></div><span>${txt}</span>`);
      return { el, x, y, z };
    });
    const mini = mk("div", "o glass mini", root,
      `<div class="dots"><i></i><i></i><i></i></div><div class="row"><img src="${AVATAR}" alt=""><div><b>noor_motion</b><div class="bar"></div><span class="follow">Follow</span></div></div>`);

    const sel = mk("div", "o sel", title);
    const handles = [];
    for (let i = 0; i < 8; i++) handles.push(mk("div", "h", sel));
    const cur = cursor(title);

    let box = { x0: -500, y0: -200, x1: 420, y1: 200 };
    function measure() {
      const w = Math.max(noor._face.offsetWidth, motion._face.offsetWidth);
      const lh = noor._face.offsetHeight;
      noor._w = noor._face.offsetWidth; motion._w = motion._face.offsetWidth;
      noor._y = -lh * 0.5; motion._y = lh * 0.5;
      // selection hugs the glyphs (font box has generous padding) with some air
      box = { x0: -w / 2 - 36, y0: noor._y - lh * 0.36 - 30, x1: w / 2 + 36, y1: motion._y + lh * 0.36 + 30 };
    }

    const TX = -40, TY = -6; // title centre in world space

    function update(t) {
      // camera
      const cam = {
        x: kf(t, [[0, -60], [0.9, -40, E.outExpo], [2.9, -20, E.inOutSine], [3.85, TX + 10, E.inOutCubic]]),
        y: kf(t, [[0, 10], [0.9, 0, E.outExpo], [3.85, TY, E.inOutCubic]]),
        z: kf(t, [[0, -160], [0.9, 0, E.outExpo], [2.9, 50, E.inOutSine], [3.85, 330, E.inOutCubic], [4.45, 1120, E.inExpo]]),
        rx: kf(t, [[0, 12], [0.9, 9, E.outExpo], [2.9, 6.5, E.inOutSine], [3.85, 3, E.inOutCubic]]),
        ry: kf(t, [[0, -20], [0.9, -11, E.outExpo], [2.9, -6, E.inOutSine], [3.85, -2, E.inOutCubic]]),
        rz: kf(t, [[0, -2.5], [0.9, -1.2, E.outExpo], [3.85, 0]]),
        // speed blur on the fast fly-in, then the whip into the title
        blur: lerp(9, 0, P(t, 0.03, 0.45, E.outCubic)) + kf(t, [[3.9, 0], [4.45, 16, E.inCubic]]),
      };

      // title flies in rotating, then breathes
      const pi = P(t, 0.06, 0.9, E.outExpo);
      tf(title, {
        x: lerp(-950, TX, pi), y: lerp(140, TY, pi) + wob(t, 0.35, 0.1, 4), z: lerp(-1100, 0, pi),
        rx: lerp(30, 7, pi) + wob(t, 0.3, 0.3, 1.0), ry: lerp(-100, -14, pi) + wob(t, 0.25, 0, 1.5), rz: lerp(-10, -1, pi),
      });
      tf(noor, { x: 0, y: noor._y || -70 });
      tf(motion, { x: 0, y: motion._y || 70 });
      // light sweep over the face
      const sw = P(t, 1.0, 1.9, E.inOutCubic);
      const bp = `${lerp(130, -40, sw).toFixed(1)}% 0`;
      noor._shine.style.backgroundPosition = bp;
      motion._shine.style.backgroundPosition = `${lerp(140, -30, P(t, 1.08, 1.98, E.inOutCubic)).toFixed(1)}% 0`;

      // tags fly in from the edges and drift apart during the push-in
      const from = [[-1500, -300, 300], [-1300, 900, 300], [1300, 900, 300]];
      tags.forEach((g, i) => {
        const p = P(t, 0.16 + i * 0.07, 0.78 + i * 0.07, E.outExpo);
        const spread = P(t, 2.9, 4.4, E.inCubic);
        tf(g.el, {
          x: lerp(from[i][0], g.x, p) + g.x * spread * 0.5 + wob(t, 0.3, i * 0.3, 6),
          y: lerp(from[i][1], g.y, p) + g.y * spread * 0.5 + wob(t, 0.27, i * 0.2 + 0.5, 7),
          z: lerp(from[i][2], g.z, p) + spread * 200,
          ry: lerp(i === 2 ? -40 : 40, 0, p) + wob(t, 0.2, i, 2), rz: lerp(i === 2 ? 8 : -8, 0, p),
        });
      });
      const pm = P(t, 0.0, 0.62, E.outExpo);
      tf(mini, { x: lerp(1100, 610, pm) + wob(t, 0.22, 0.4, 6), y: lerp(-760, -355, pm) + wob(t, 0.26, 0.1, 6), z: lerp(-400, -90, pm), ry: lerp(-35, -8, pm), rz: lerp(10, 2, pm) });

      // cursor: wander, grab the title, drag a selection, release
      const sx = box.x0, sy = box.y0, ex = box.x1, ey = box.y1;
      const cx = kf(t, [[0.95, 800], [1.55, 420, E.outCubic], [2.05, sx, E.inOutCubic], [2.75, ex, E.inOutCubic], [3.7, ex + 260, E.inOutSine]]);
      const cy = kf(t, [[0.95, 640], [1.55, 300, E.outCubic], [2.05, sy, E.inOutCubic], [2.75, ey, E.inOutCubic], [3.7, ey + 180, E.inOutSine]]);
      const press = (t > 2.03 && t < 2.78) ? 0.86 : 1;
      poseCursor(cur, cx, cy, 46, press, kf(t, [[0.9, 0], [1.05, 1], [3.3, 1], [3.7, 0]]));

      // selection rectangle (grows with the drag, then stays)
      const dragging = t >= 2.05;
      if (dragging) {
        const rx1 = t < 2.75 ? cx : ex, ry1 = t < 2.75 ? cy : ey;
        const w = Math.max(2, rx1 - sx), h = Math.max(2, ry1 - sy);
        sel.style.width = w + "px"; sel.style.height = h + "px";
        tf(sel, { x: sx, y: sy, z: 26, o: 1, anchor: " " });
        const hp = P(t, 2.76, 2.98, E.outBack);
        const pts = [[0, 0], [0.5, 0], [1, 0], [1, 0.5], [1, 1], [0.5, 1], [0, 1], [0, 0.5]];
        handles.forEach((hd, i) => {
          hd.style.left = pts[i][0] * w + "px"; hd.style.top = pts[i][1] * h + "px";
          const corner = i % 2 === 0;
          const s = t < 2.75 ? (corner && (i === 0 || i === 4) ? 1 : 0) : (corner ? 1 : hp);
          hd.style.transform = `translate(-50%,-50%) scale(${s.toFixed(3)})`;
        });
      } else {
        sel.style.visibility = "hidden";
      }

      applyCamera(cam);
      // environment
      bg.style.background = BG.intro;
      bgGrid.style.opacity = "1";
      bgGrid.style.backgroundPosition = `${(t * 6).toFixed(1)}px ${(t * 3).toFixed(1)}px`;
      waves.style.opacity = String(kf(t, [[0, 0.2], [0.4, 1], [3.6, 1], [4.3, 0]]));
      const draw = P(t, 0.05, 1.0, E.outCubic);
      for (const [id, len] of [["wave1", 2300], ["wave2", 1100]]) {
        const p = document.getElementById(id);
        p.style.strokeDasharray = `${len}`;
        p.style.strokeDashoffset = `${(len * (1 - draw)).toFixed(1)}`;
      }
      waves.style.transform = `translate(${wob(t, 0.15, 0, 18).toFixed(1)}px, ${wob(t, 0.12, 0.3, 10).toFixed(1)}px)`;
      orb(0, 1250 + wob(t, 0.1, 0, 60), 330, 1100, "rgba(255,110,30,0.30)", 1);
      orb(1, 380 + wob(t, 0.12, 0.5, 50), 860, 900, "rgba(255,70,0,0.20)", 1);
      orb(2, 960, 540, 10, "rgba(0,0,0,0)", 0);
      chrome.style.opacity = "1";
      fade.style.opacity = String(kf(t, [[0, 0.6], [0.25, 0], [4.25, 0], [4.45, 1]]));
      flash.style.opacity = "0";
    }
    return { root, update, measure, range: [0, 4.45] };
  })();

  // ================================================================ SECTION 2 — profile card
  const profile = (() => {
    const root = mk("div", "sec", world);
    const card = mk("div", "o glass pcard", root, `
      <div class="lbl">studio</div>
      <div class="av"><img src="${AVATAR}" alt=""></div>
      <div class="name">noor_motion</div>
      <div class="sub">SaaS Video &amp; Motion Design</div>
      <div class="pills"></div>`);
    card.style.transformStyle = "flat";
    const pillsBox = card.querySelector(".pills");
    const pills = [["Product videos", ICON.play(22)], ["UI animation", ICON.cursor(22)], ["Explainers", ICON.bulb(22)]]
      .map(([txt, ic]) => mk("div", "pill", pillsBox, `<span>${txt}</span><span class="ic">${ic}</span>`));
    const emos = [["🎬", 70, 160], ["🔥", 66, 252], ["✨", 400, 150], ["🚀", 404, 246]].map(([e, x, y]) => {
      const el = mk("div", "emo", card, e);
      el.style.position = "absolute"; el.style.left = x + "px"; el.style.top = y + "px";
      return el;
    });
    const cur = cursor(root);

    function update(t) {
      const lt = t - 4.45;
      const p = P(t, 4.47, 5.05, E.outExpo);
      const exit = P(t, 5.9, 6.3, E.inExpo);
      tf(card, {
        x: lerp(0, -1250, exit), y: lerp(560, 30, p) + wob(t, 0.3, 0, 5), z: lerp(-380, 0, p),
        rx: lerp(38, 0, p) + wob(t, 0.25, 0.2, 1.5), ry: lerp(-6, 0, p) + exit * 38 + wob(t, 0.2, 0.5, 2.5), rz: lerp(-3, 0, p),
        o: P(t, 4.47, 4.7), blur: exit * 10,
      });
      emos.forEach((el, i) => {
        const s = P(t, 4.66 + i * 0.07, 5.0 + i * 0.07, E.outBack);
        el.style.transform = `translate(-50%,-50%) translateY(${wob(t, 0.6, i * 0.25, 6).toFixed(1)}px) rotate(${(wob(t, 0.4, i * 0.3, 8)).toFixed(1)}deg) scale(${s.toFixed(3)})`;
      });
      pills.forEach((el, i) => {
        const s = P(t, 4.98 + i * 0.2, 5.36 + i * 0.2, E.outBackSoft);
        el.style.opacity = P(t, 4.98 + i * 0.2, 5.1 + i * 0.2).toFixed(3);
        el.style.transform = `translateY(${lerp(-26, 0, s).toFixed(1)}px) scale(${lerp(0.85, 1, s).toFixed(3)})`;
        el.classList.toggle("hover", i === 2 && t > 5.72 && t < 6.0);
      });
      const cx = kf(t, [[5.3, 420], [5.75, 150, E.outCubic], [6.3, -1000, E.inExpo]]);
      const cy = kf(t, [[5.3, 520], [5.75, 266, E.outCubic], [6.3, 300, E.inExpo]]);
      poseCursor(cur, cx, cy, 40, 1, kf(t, [[5.28, 0], [5.38, 1]]));

      applyCamera({ x: 0, y: 14, z: kf(t, [[4.45, 40], [5.0, 190, E.outExpo], [5.9, 260, E.inOutSine], [6.3, 230]]), rx: 4, ry: kf(t, [[4.45, -3], [5.9, 3, E.inOutSine], [6.3, 10, E.inCubic]]), blur: 0 });
      bg.style.background = BG.dark;
      bgGrid.style.opacity = "0.35";
      waves.style.opacity = "0";
      orb(0, 960 + wob(t, 0.2, 0, 40) - exit * 500, 560, 1100, "rgba(255,90,10,0.32)", 1);
      orb(1, 1400, 200, 700, "rgba(255,140,40,0.12)", 1);
      orb(2, 960, 540, 10, "rgba(0,0,0,0)", 0);
      chrome.style.opacity = "1";
      fade.style.opacity = String(kf(t, [[4.45, 1], [4.62, 0]]));
      flash.style.opacity = "0";
    }
    return { root, update, range: [4.45, 6.25] };
  })();

  // ================================================================ SECTION 3 — services
  const services = (() => {
    const root = mk("div", "sec", world);
    const word = mk("div", "o bigword", root, "SERVICES");
    const apps = [
      ["Product videos", "t1", ICON.play(120), -230, -170, 0, 6.27, 1.22],
      ["UI animation", "t2", ICON.cursor(116, "#ffb04a"), 300, -125, 60, 6.5, 1.34],
      ["Explainers", "t3", ICON.bulb(120, "#7a2a00"), 40, 275, 30, 6.86, 1.26],
    ].map(([name, cls, ic, x, y, z, at, sc]) => {
      const el = mk("div", "o glass app", root, `<div class="bar"><span>${name}</span><span class="dots"><i></i><i></i><i></i></span></div><div class="tile ${cls}">${ic}</div>`);
      el.style.transformStyle = "flat";
      return { el, x, y, z, at, sc };
    });
    function update(t) {
      tf(word, { x: kf(t, [[6.25, 120], [7.45, -90, E.lin]]), y: 40, z: -260 });
      apps.forEach((a, i) => {
        const p = P(t, a.at, a.at + 0.5, E.outBack);
        const q = P(t, a.at, a.at + 0.45, E.outExpo);
        tf(a.el, {
          x: a.x + wob(t, 0.35, i * 0.3, 5), y: a.y + lerp(80, 0, q) + wob(t, 0.3, i * 0.2, 6), z: lerp(-260, a.z, q),
          rz: lerp(i === 1 ? 10 : -10, 0, q) + wob(t, 0.25, i, 1.2), ry: lerp(25, 0, q),
          sc: a.sc * lerp(0.35, 1, p), o: P(t, a.at, a.at + 0.12),
        });
      });
      applyCamera({ x: 0, y: 0, z: kf(t, [[6.25, -40], [6.6, 0, E.outExpo], [7.45, 70, E.inOutSine]]), rx: kf(t, [[6.25, 6], [7.45, 2]]), ry: kf(t, [[6.25, -9], [7.45, 5]]), blur: 0 });
      bg.style.background = BG.dark;
      bgGrid.style.opacity = "0.5";
      waves.style.opacity = "0";
      orb(0, 900, 520, 1300, "rgba(255,90,10,0.22)", 1);
      orb(1, 1500, 860, 700, "rgba(255,140,40,0.10)", 1);
      orb(2, 960, 540, 10, "rgba(0,0,0,0)", 0);
      chrome.style.opacity = "1";
      fade.style.opacity = "0";
      flash.style.opacity = String(kf(t, [[6.25, 0.18], [6.45, 0]]));
    }
    return { root, update, range: [6.25, 7.45] };
  })();

  // ================================================================ SECTION 4 — chat message
  const chat = (() => {
    const MSG = "We make SaaS products easy to understand.";
    const root = mk("div", "sec", world);
    const card = mk("div", "o glass chat", root, `
      <div class="dots"><i></i><i></i><i></i></div>
      <div class="row"><div class="av"><img src="${AVATAR}" alt=""></div>
        <div><div class="who">Noor<small>00:30</small></div><div class="msg"><span class="txt"></span><span class="caret"></span></div></div></div>
      <div class="send">Send</div>`);
    card.style.transformStyle = "flat";
    const txt = card.querySelector(".txt");
    const caret = card.querySelector(".caret");
    const send = card.querySelector(".send");
    const cur = cursor(root);

    function update(t) {
      const p = P(t, 7.45, 8.1, E.outExpo);
      const out = P(t, 9.92, 10.12, E.inCubic);
      tf(card, {
        x: lerp(160, 0, p), y: lerp(90, 0, p) + wob(t, 0.3, 0, 4), z: lerp(-560, 0, p) + out * 500,
        rx: lerp(22, 0, p) + wob(t, 0.25, 0.3, 1), ry: lerp(-30, 0, p) + wob(t, 0.2, 0.1, 1.5), rz: lerp(-5, 0, p),
        sc: 1.28, o: P(t, 7.45, 7.62), blur: out * 10,
      });
      const n = Math.round(P(t, 7.8, 8.55) * MSG.length);
      if (txt.textContent.length !== n) txt.textContent = MSG.slice(0, n);
      caret.style.opacity = (t < 8.55 || Math.floor(t * 3) % 2 === 0) ? "1" : "0";
      const sp = P(t, 8.28, 8.62, E.outBack);
      const pressed = t > 9.46 && t < 9.6;
      send.style.transform = `scale(${(sp * (pressed ? 0.9 : 1)).toFixed(3)})`;
      send.style.filter = t > 9.46 && t < 9.9 ? `brightness(${(1.35 - 0.35 * P(t, 9.5, 9.9)).toFixed(3)})` : "none";

      // cursor wanders in, settles on Send, clicks
      const cx = kf(t, [[8.5, 640], [8.95, 480, E.outCubic], [9.3, 345, E.inOutCubic], [9.92, 338]]);
      const cy = kf(t, [[8.5, 420], [8.95, 260, E.outCubic], [9.3, 108, E.inOutCubic], [9.92, 104]]);
      poseCursor(cur, cx * 1.28 + wob(t, 0.9, 0, 3), cy * 1.28 + wob(t, 0.8, 0.4, 3), 40 + out * 500, pressed ? 0.86 : 1, kf(t, [[8.48, 0], [8.6, 1]]));

      applyCamera({ x: 0, y: 0, z: kf(t, [[7.45, -40], [8.0, 0, E.outExpo], [9.9, 110, E.inOutSine]]), rx: kf(t, [[7.45, 5], [9.9, 2]]), ry: kf(t, [[7.45, -6], [9.9, 4]]), blur: 0 });
      bg.style.background = BG.dark;
      bgGrid.style.opacity = "0.3";
      waves.style.opacity = "0";
      orb(0, 960 + wob(t, 0.18, 0, 50), 560, 1250, "rgba(255,90,10,0.30)", 1);
      orb(1, 300, 200, 700, "rgba(255,140,40,0.10)", 1);
      orb(2, 1150, 610, 420, "rgba(255,150,60,0.5)", P(t, 9.5, 9.6) * (1 - P(t, 9.6, 10.0)));
      chrome.style.opacity = "1";
      fade.style.opacity = "0";
      flash.style.opacity = String(kf(t, [[7.45, 0.15], [7.6, 0]]));
    }
    return { root, update, range: [7.45, 10.12] };
  })();

  // ================================================================ SECTIONS 5-7 — work grids
  const grids = (() => {
    const root = mk("div", "sec", world);
    const SEG = [
      { at: 10.12, end: 13.3, label: "PRODUCT VIDEOS", clips: ["g1_commas", "g1_fortknox", "g1_neural", "g1_nano"] },
      { at: 13.3, end: 17.83, label: "UI ANIMATION", clips: ["g2_fortknox", "g2_commas", "g2_nano", "g2_neural"] },
      { at: 17.83, end: 22.65, label: "EXPLAINERS", clips: ["g3_nano", "g3_fortknox", "g3_commas", "g3_neural"] },
    ];
    const POS = [[-425, -252], [425, -252], [-425, 252], [425, 252]];
    const cards = POS.map(([x, y], i) => {
      const el = mk("div", "o card", root);
      el.style.transformStyle = "flat";
      const img = mk("img", "", el);
      img.decoding = "sync";
      const shade = mk("div", "shade", el);
      mk("div", "gloss", el);
      return { el, img, shade, x, y, src: "" };
    });
    // one extruded label per segment, letter by letter
    const labels = SEG.map((s) => {
      const box = mk("div", "o glabel", root);
      const letters = [];
      for (const ch of s.label) {
        if (ch === " ") { letters.push(null); continue; }
        const L = extruded(ch, 96, { depth: 14, step: 1.6, glow: false });
        box.appendChild(L);
        letters.push(L);
      }
      return { box, letters, widths: [] };
    });
    function measure() {
      labels.forEach((lb) => {
        const space = 34, gap = 2;
        const ws = lb.letters.map((L) => (L ? L._face.offsetWidth : space));
        const total = ws.reduce((a, b) => a + b, 0) + gap * (ws.length - 1);
        let x = -total / 2;
        lb.xs = ws.map((w) => { const c = x + w / 2; x += w + gap; return c; });
      });
    }
    const pending = [];

    function update(t) {
      const gi = t < SEG[1].at ? 0 : t < SEG[2].at ? 1 : 2;
      const seg = SEG[gi];
      const lt = t - seg.at;
      const into = P(t, seg.at, seg.at + 0.55, E.outExpo);
      const leaving = gi < 2 ? P(t, seg.end - 0.14, seg.end, E.inCubic) : 0;

      cards.forEach((c, i) => {
        const clip = seg.clips[i];
        const idx = clamp(Math.floor((lt + 0.2) * CLIP_FPS) + 1, 1, CLIP_FRAMES);
        const src = `${CLIPS}/${clip}/${String(idx).padStart(4, "0")}.jpg`;
        if (c.src !== src) { c.src = src; c.img.src = src; pending.push(c.img.decode().catch(() => {})); }
        const stagger = P(t, seg.at + i * 0.04, seg.at + 0.5 + i * 0.04, E.outExpo);
        const s = lerp(gi === 0 ? 0.9 : 1.07, 1, stagger) * lerp(1, 0.96, leaving);
        tf(c.el, {
          x: c.x + wob(t, 0.18, i * 0.25, 6), y: c.y + wob(t, 0.2, i * 0.2 + 0.4, 6), z: wob(t, 0.15, i * 0.3, 14),
          rx: wob(t, 0.13, i * 0.17, 1.2), ry: wob(t, 0.11, i * 0.29, 1.6), sc: s,
        });
        c.img.style.transform = `scale(${lerp(1.08, 1.0, P(t, seg.at, seg.end, E.outCubic)).toFixed(4)})`;
        c.shade.style.opacity = Math.max(1 - P(t, seg.at + i * 0.04, seg.at + 0.32 + i * 0.04, E.outCubic), leaving * 0.9).toFixed(3);
      });

      labels.forEach((lb, li) => {
        const on = li === gi;
        show(lb.box, on);
        if (!on) return;
        tf(lb.box, { x: wob(t, 0.2, 0, 8), y: 2 + wob(t, 0.23, 0.3, 4), z: 70 });
        lb.letters.forEach((L, k) => {
          if (!L) return;
          const a = seg.at + 0.12 + k * 0.035;
          const s = P(t, a, a + 0.5, E.outBack) * (1 - leaving);
          tf(L, { x: lb.xs[k], y: lerp(40, 0, P(t, a, a + 0.5, E.outExpo)), z: 0, ry: lerp(-60, 0, P(t, a, a + 0.6, E.outExpo)), sc: s });
          L._shine.style.backgroundPosition = `${lerp(130, -40, P(t, seg.at + 0.9 + k * 0.02, seg.at + 1.7 + k * 0.02, E.inOutCubic)).toFixed(1)}% 0`;
        });
      });

      // camera: first grid pulls back from a blurred close-up, later grids punch in
      const g0 = gi === 0;
      const z0 = g0 ? lerp(950, 0, into) : lerp(160, 0, into);
      applyCamera({
        x: wob(t, 0.07, 0.1, 40), y: 10 + wob(t, 0.09, 0.4, 16),
        z: z0 + lerp(0, 70, P(t, seg.at, seg.end, E.inOutSine)),
        rx: 11 + wob(t, 0.08, 0.2, 2.2),
        ry: lerp(-7, 5, P(t, seg.at, seg.end, E.inOutSine)) * (gi === 1 ? -1 : 1),
        rz: wob(t, 0.06, 0.6, 0.6),
        blur: g0 ? lerp(18, 0, P(t, seg.at, seg.at + 0.5, E.outCubic)) : 0,
      });
      bg.style.background = BG.grid;
      bgGrid.style.opacity = "0.8";
      bgGrid.style.backgroundPosition = `${(t * -8).toFixed(1)}px ${(t * 4).toFixed(1)}px`;
      waves.style.opacity = "0";
      orb(0, 960 + wob(t, 0.1, 0, 120), 520, 1400, "rgba(255,100,20,0.20)", 1);
      orb(1, 300 + wob(t, 0.08, 0.5, 80), 950, 900, "rgba(255,60,0,0.14)", 1);
      orb(2, 1650, 120, 800, "rgba(255,160,60,0.10)", 1);
      chrome.style.opacity = "0";
      flash.style.opacity = String(gi === 0 ? kf(t, [[10.12, 0.3], [10.45, 0]]) : kf(t, [[seg.at, 0.42], [seg.at + 0.35, 0, E.outCubic]]));
      fade.style.opacity = String(kf(t, [[21.95, 0], [22.6, 1, E.inOutCubic]]));
    }
    return { root, update, measure, pending, range: [10.12, 22.62] };
  })();

  // ================================================================ SECTION 8 — outro
  const outro = (() => {
    const root = mk("div", "sec", world);
    const av = mk("div", "o", root, `<img src="${AVATAR}" alt="" style="width:150px;height:150px;border-radius:50%;display:block;box-shadow:0 0 60px rgba(255,110,30,.55)">`);
    const handle = mk("div", "o handle", root, "noor_motion");
    const glowCopy = mk("div", "o handle", root, "noor_motion");
    glowCopy.style.color = "#ff5a00";
    const tag = mk("div", "o tagline", root, "SaaS VIDEO &amp; MOTION DESIGN &nbsp;·&nbsp; DM “VIDEO”");
    const spark = mk("div", "o", root);
    spark.style.cssText += "width:4px;height:240px;border-radius:4px;background:linear-gradient(180deg,transparent,#ffd9a8 70%,#fff);box-shadow:0 0 18px #ff8a2a,0 0 40px #ff5a00";
    const burst = mk("div", "o", root);
    burst.style.cssText += "width:520px;height:520px;border-radius:50%;background:radial-gradient(circle,rgba(255,220,170,.9),rgba(255,120,40,.35) 35%,transparent 70%)";
    const smoke = [0, 1, 2].map(() => {
      const s = mk("div", "o", root);
      s.style.cssText += "width:900px;height:520px;border-radius:50%;background:radial-gradient(ellipse,rgba(255,236,220,.55),rgba(255,170,110,.18) 45%,transparent 70%)";
      return s;
    });

    function update(t) {
      const appear = P(t, 22.7, 23.2, E.outCubic);
      const hit = P(t, 23.18, 23.42, E.outExpo);
      const gone = P(t, 24.35, 24.95, E.inOutCubic);
      const o = (0.35 * appear + 0.65 * hit) * (1 - gone);
      tf(handle, { x: 0, y: 40, z: 0, sc: lerp(1.06, 1, hit) * lerp(1, 0.97, gone), o, blur: lerp(10, 0, appear) * (1 - hit) + gone * 6 });
      handle.style.textShadow = `0 0 ${lerp(10, 26, hit).toFixed(1)}px rgba(255,120,30,${(0.5 + 0.5 * hit).toFixed(2)}), 0 0 ${lerp(30, 80, hit).toFixed(1)}px rgba(255,80,0,${(0.3 + 0.4 * hit).toFixed(2)})`;
      const pulse = 0.5 + 0.5 * Math.sin((t - 23.4) * Math.PI * 2 * 0.9);
      tf(glowCopy, { x: 0, y: 40, z: -2, sc: 1.01, o: (0.2 + 0.25 * hit * pulse) * (1 - gone), blur: 22 });
      tf(av, { x: 0, y: -120, z: 0, sc: lerp(0.6, 1, P(t, 23.2, 23.7, E.outBack)), o: P(t, 23.2, 23.4) * (1 - gone), blur: gone * 8 });
      tf(tag, { x: 0, y: 140, z: 0, o: P(t, 23.45, 23.85, E.outCubic) * (1 - gone), blur: lerp(6, 0, P(t, 23.45, 23.85)) });
      // spark falls onto the word, then bursts
      const sp = P(t, 22.95, 23.2, E.inCubic);
      tf(spark, { x: 6, y: lerp(-620, -40, sp), z: 10, o: (t > 22.95 && t < 23.22) ? 1 : 0 });
      tf(burst, { x: 0, y: 30, z: 5, sc: lerp(0.3, 1.6, P(t, 23.18, 23.6, E.outCubic)), o: kf(t, [[23.18, 0], [23.22, 0.9], [23.7, 0, E.outCubic]]) });
      smoke.forEach((s, i) => {
        const p = P(t, 24.05 + i * 0.12, 25.05, E.outCubic);
        tf(s, { x: lerp(900 - i * 120, 250 - i * 260, p), y: 300 - i * 70 + wob(t, 0.3, i * 0.3, 20), z: 20, sc: lerp(0.7, 1.5, p), o: kf(t, [[24.05 + i * 0.12, 0], [24.45 + i * 0.12, 0.85], [25.05, 0.3]]), blur: 30 });
      });
      applyCamera({ x: 0, y: 0, z: kf(t, [[22.6, -40], [25.05, 60, E.lin]]), rx: 0, ry: 0, blur: 0 });
      bg.style.background = BG.black;
      bgGrid.style.opacity = "0";
      waves.style.opacity = "0";
      orb(0, 960, 600, 1200, "rgba(255,80,0,0.16)", (0.3 + 0.7 * hit) * (1 - gone));
      orb(1, 960, 540, 10, "rgba(0,0,0,0)", 0);
      orb(2, 960, 540, 10, "rgba(0,0,0,0)", 0);
      chrome.style.opacity = "0";
      flash.style.opacity = "0";
      fade.style.opacity = String(kf(t, [[22.6, 1], [22.75, 0], [24.8, 0], [25.05, 1]]));
    }
    return { root, update, range: [22.62, 25.1] };
  })();

  const SECTIONS = [intro, profile, services, chat, grids, outro];

  // ---------------------------------------------------------------- frame API
  let ready = null;
  async function setup() {
    await document.fonts.load('800 150px "Unbounded"');
    await document.fonts.load('600 92px "Unbounded"');
    await document.fonts.load('900 300px "Unbounded"');
    await document.fonts.load('600 30px "Sora"');
    await document.fonts.load('500 30px "Sora"');
    await document.fonts.load('700 30px "Sora"');
    await document.fonts.load('52px "Noto Color Emoji"', "🎬🔥✨🚀");
    await document.fonts.ready;
    await Promise.all([...document.images].map((im) => im.decode().catch(() => {})));
    for (const s of SECTIONS) { show(s.root, true); if (s.measure) s.measure(); }
  }

  window.__render = async (t) => {
    if (!ready) ready = setup();
    await ready;
    t = clamp(t, 0, DURATION);
    let active = null;
    for (const s of SECTIONS) {
      const on = t >= s.range[0] && t < s.range[1];
      show(s.root, on);
      if (on && !active) active = s;
    }
    if (!active) active = SECTIONS[SECTIONS.length - 1];
    show(active.root, true);
    active.update(t);
    const f = Math.floor(t * 60);
    grain.style.backgroundImage = `url(${grainTiles[f % grainTiles.length]})`;
    grain.style.backgroundPosition = `${(f * 37) % 256}px ${(f * 91) % 256}px`;
    const waits = grids.pending.splice(0);
    await Promise.all(waits);
  };
  window.__duration = DURATION;

  if (Q.has("t")) window.__render(parseFloat(Q.get("t")));
})();
