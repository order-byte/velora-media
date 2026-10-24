/* Aminur Rahaman (@aminur_rex) X-profile showreel.
 *
 * Everything is a pure function of time: window.__render(t) poses every
 * element for second t and resolves once the frame's images are decoded.
 * Beat map and transitions follow the reference edit (measured at 30 fps):
 *   0.00  3D name title, cursor drags a selection, push-in
 *   4.20  zoom through the title -> 4 black frames -> profile card rises
 *   4.45  X profile card, 3D pop-out avatar, Follow click
 *   6.10  whip pan out -> SOFTWARE racks into focus
 *   7.45  hard cut, chat card swings in tilted, types, Send click
 *  10.12  hard cut to a blurred close-up of grid 1, fast pull-back
 *  13.30  grid 2: cards drop to black, clips fade up, label grows in
 *  17.83  grid 3: straight cut, label already full size
 *  22.00  fade to black -> end card
 */
(() => {
  const Q = new URLSearchParams(location.search);
  const CLIPS = Q.get("clips") || "../build/clips";
  const A = "../assets/";
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
    outExpo: (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
    inExpo: (t) => (t <= 0 ? 0 : Math.pow(2, 10 * t - 10)),
    inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
    outBack: (t) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
    outBackSoft: (t) => { const c1 = 0.9, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  };
  const P = (t, a, b, e = E.lin) => e(clamp((t - a) / (b - a)));
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
  function mix(a, b, t) { const X = hex(a), Y = hex(b); return `rgb(${X.map((v, i) => Math.round(lerp(v, Y[i], t))).join(",")})`; }

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
    str += s.anchor == null ? " translate(-50%,-50%)" : s.anchor;
    el.style.transform = str;
    if (s.o != null) {
      el.style.opacity = clamp(s.o).toFixed(3);
      el.style.visibility = s.o <= 0.001 ? "hidden" : "visible";
    }
    if (s.blur != null) el.style.filter = s.blur > 0.05 ? `blur(${s.blur.toFixed(2)}px)` : "none";
  }
  const show = (el, on) => { el.style.display = on ? "" : "none"; };

  const world = $("#world"), camera = $("#camera"), bg = $("#bg"), bgGrid = $("#bgGrid"), glows = $("#glows");
  const waves = $("#waves"), chrome = $("#chrome"), flash = $("#flash"), fade = $("#fade"), grain = $("#grain");
  const overlay = $("#overlay");

  function applyCamera(c) {
    world.style.transform =
      `translateZ(${(c.z || 0).toFixed(2)}px) rotateX(${(c.rx || 0).toFixed(3)}deg) rotateY(${(c.ry || 0).toFixed(3)}deg) rotateZ(${(c.rz || 0).toFixed(3)}deg) translate3d(${(-(c.x || 0)).toFixed(2)}px,${(-(c.y || 0)).toFixed(2)}px,0)`;
    camera.style.filter = c.blur > 0.05 ? `blur(${c.blur.toFixed(2)}px)` : "none";
  }
  function env({ bgName, grid = 0, wavesO = 0, chromeO = 0, flashO = 0, fadeO = 0 }) {
    bg.style.background = BG[bgName];
    bgGrid.style.opacity = String(grid);
    waves.style.opacity = String(wavesO);
    chrome.style.opacity = String(chromeO);
    flash.style.opacity = String(flashO);
    fade.style.opacity = String(fadeO);
  }

  function extruded(text, size, { depth = 22, step = 1.6, back = "#0d1200", front = "#5c7a00", glow = true } = {}) {
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

  const CURSOR_SVG = '<svg width="40" height="48" viewBox="0 0 40 48"><path d="M4 3 L4 37 L13 29 L19 43 L25 40.5 L19 27 L31 27 Z" fill="#fff" stroke="#0a0b08" stroke-width="2.4" stroke-linejoin="round"/></svg>';
  const cursor = (parent) => mk("div", "o cursor", parent, CURSOR_SVG);
  const poseCursor = (el, x, y, z, sc, o) => tf(el, { x, y, z, sc, o, anchor: " translate(-4px,-3px)" });

  const ICON = {
    play: (s, c = "#0b0d06") => `<svg width="${s}" height="${s}" viewBox="0 0 24 24"><path d="M8 5.2c0-.9 1-1.4 1.7-.9l9.1 6.1c.6.4.6 1.3 0 1.7l-9.1 6.1c-.7.5-1.7 0-1.7-.9z" fill="${c}"/></svg>`,
    bulb: (s, c = "#0b0d06") => `<svg width="${s}" height="${s}" viewBox="0 0 24 24"><path d="M12 2.8a6.6 6.6 0 0 0-3.9 11.9c.6.5 1 1.2 1 2V17h5.8v-.3c0-.8.4-1.5 1-2A6.6 6.6 0 0 0 12 2.8z" fill="${c}"/><rect x="9.2" y="18.3" width="5.6" height="1.6" rx=".8" fill="${c}"/><rect x="10" y="20.6" width="4" height="1.5" rx=".75" fill="${c}"/></svg>`,
    shapes: (s, c = "#0b0d06") => `<svg width="${s}" height="${s}" viewBox="0 0 24 24"><circle cx="8" cy="8.5" r="4.6" fill="${c}"/><rect x="12.4" y="12.4" width="8.4" height="8.4" rx="1.8" fill="${c}"/><path d="M15.8 2.8l4.6 7.6h-9.2z" fill="${c}"/></svg>`,
    spark: (s) => {
      let rays = "";
      for (let i = 0; i < 12; i++) {
        const a = (i / 12) * Math.PI * 2, r0 = 9, r1 = i % 2 ? 40 : 46;
        rays += `<line x1="${50 + Math.cos(a) * r0}" y1="${50 + Math.sin(a) * r0}" x2="${50 + Math.cos(a) * r1}" y2="${50 + Math.sin(a) * r1}" />`;
      }
      return `<svg width="${s}" height="${s}" viewBox="0 0 100 100"><g stroke="#fff6ee" stroke-width="7.5" stroke-linecap="round">${rays}</g></svg>`;
    },
  };

  // 3D avatar: lime ring + the cut-out person popping above it on its own depth layer
  function popAvatar(parent, size) {
    const g = mk("div", "o ava", parent);
    g.style.width = g.style.height = size + "px";
    const ring = mk("div", "ring", g);
    ring.style.transform = "translateZ(0px)";
    const pop = mk("div", "pop", g);
    pop.style.width = pop.style.height = size + "px";
    // person.png: 640 px, original avatar circle centred (318, 310) r 281
    const k = (size / 2) * 1.14 / 281;
    const img = mk("img", "", pop);
    img.src = A + "person.png";
    img.style.width = img.style.height = 640 * k + "px";
    img.style.left = size / 2 - 318 * k + "px";
    img.style.top = size / 2 - size * 0.1 - 310 * k + "px";
    // free above the ring's centre line (head breaks out of the frame), round below it
    const h = size / 2, wide = size * 0.35;
    pop.style.clipPath = `path('M ${-wide} ${-size} L ${size + wide} ${-size} L ${size + wide} ${h} L ${size} ${h} A ${h} ${h} 0 0 1 0 ${h} L ${-wide} ${h} Z')`;
    g._ring = ring; g._pop = pop; g._img = img;
    return g;
  }
  function poseAvatar(g, popZ, popScale) {
    g._pop.style.transform = `translateZ(${popZ.toFixed(2)}px) scale(${popScale.toFixed(4)})`;
    g._pop.style.transformOrigin = "50% 100%";
  }

  // ---------------------------------------------------------------- backgrounds
  const BG = {
    intro: "radial-gradient(ellipse 1300px 900px at 62% 38%, #283409 0%, #121707 42%, #070806 78%, #040504 100%)",
    dark: "radial-gradient(ellipse 1000px 760px at 50% 55%, #1b2308 0%, #0b0e06 48%, #040504 100%)",
    grid: "radial-gradient(ellipse 1500px 950px at 50% 45%, #263209 0%, #10140a 48%, #050604 100%)",
    black: "#030303",
  };
  const orbs = [0, 1, 2].map(() => mk("div", "orb", glows));
  function orb(i, x, y, size, color, alpha) {
    const o = orbs[i];
    o.style.width = o.style.height = size + "px";
    o.style.background = `radial-gradient(circle, ${color} 0%, transparent 68%)`;
    o.style.opacity = alpha.toFixed(3);
    o.style.transform = `translate(${(x - size / 2).toFixed(1)}px,${(y - size / 2).toFixed(1)}px)`;
  }
  const noOrbs = (from = 0) => { for (let i = from; i < 3; i++) orb(i, 960, 540, 10, "rgba(0,0,0,0)", 0); };

  const grainTiles = [];
  (function makeGrain() {
    let seed = 2024;
    const rnd = () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
    for (let k = 0; k < 6; k++) {
      const c = document.createElement("canvas");
      c.width = c.height = 256;
      const g = c.getContext("2d");
      const im = g.createImageData(256, 256);
      for (let i = 0; i < im.data.length; i += 4) { const v = Math.floor(rnd() * 255); im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
      g.putImageData(im, 0, 0);
      grainTiles.push(c.toDataURL());
    }
  })();

  // ================================================================ 1 — name title
  const intro = (() => {
    const root = mk("div", "sec", world);
    const title = mk("div", "o", root);
    const opt = { depth: 30, step: 2.1, back: "#0a0e00", front: "#5a7800" };
    const l1 = extruded("AMINUR", 150, opt);
    const l2 = extruded("RAHAMAN", 150, opt);
    title.append(l1, l2);
    const tags = [["Product animation", -660, -190, 40], ["Explainers", -610, 340, 90], ["Motion graphics", 500, 270, 70]]
      .map(([txt, x, y, z]) => ({ el: mk("div", "o glass tag", root, `<div class="dots"><i></i><i></i></div><span>${txt}</span>`), x, y, z }));
    const mini = mk("div", "o glass mini", root,
      `<div class="dots"><i></i><i></i><i></i></div><div class="row"><div class="ring"><img src="${A}avatar.png" alt=""></div><div><b>@aminur_rex</b><div class="bar"></div><span class="follow">Follow</span></div></div>`);
    const sel = mk("div", "o sel", title);
    const handles = [];
    for (let i = 0; i < 8; i++) handles.push(mk("div", "h", sel));
    const cur = cursor(title);
    let box = { x0: -520, y0: -200, x1: 520, y1: 200 };
    function measure() {
      const w = Math.max(l1._face.offsetWidth, l2._face.offsetWidth);
      const lh = l1._face.offsetHeight;
      l1._y = -lh * 0.5; l2._y = lh * 0.5;
      box = { x0: -w / 2 - 36, y0: l1._y - lh * 0.36 - 30, x1: w / 2 + 36, y1: l2._y + lh * 0.36 + 30 };
    }
    const TX = -30, TY = -6;

    function update(t) {
      const cam = {
        x: kf(t, [[0, -60], [0.9, -40, E.outExpo], [2.9, -20, E.inOutSine], [3.7, TX + 10, E.inOutCubic]]),
        y: kf(t, [[0, 10], [0.9, 0, E.outExpo], [3.7, TY, E.inOutCubic]]),
        // steady push, then accelerate straight through the title
        z: kf(t, [[0, -160], [0.9, 0, E.outExpo], [2.9, 50, E.inOutSine], [3.7, 160, E.inOutCubic], [4.2, 400, E.inOutSine], [4.44, 1180, E.inExpo]]),
        rx: kf(t, [[0, 12], [0.9, 9, E.outExpo], [2.9, 6.5, E.inOutSine], [3.7, 3.5, E.inOutCubic]]),
        ry: kf(t, [[0, -20], [0.9, -11, E.outExpo], [2.9, -6, E.inOutSine], [3.7, -3, E.inOutCubic]]),
        rz: kf(t, [[0, -2.5], [0.9, -1.2, E.outExpo], [4.2, 0], [4.44, -5, E.inCubic]]),
        blur: lerp(9, 0, P(t, 0.03, 0.45, E.outCubic)) + kf(t, [[4.18, 0], [4.44, 15, E.inCubic]]),
      };
      const pi = P(t, 0.06, 0.9, E.outExpo);
      tf(title, {
        x: lerp(-950, TX, pi), y: lerp(140, TY, pi) + wob(t, 0.35, 0.1, 4), z: lerp(-1100, 0, pi),
        rx: lerp(30, 7, pi) + wob(t, 0.3, 0.3, 1.0), ry: lerp(-100, -14, pi) + wob(t, 0.25, 0, 1.5), rz: lerp(-10, -1, pi),
      });
      tf(l1, { x: 0, y: l1._y || -70 });
      tf(l2, { x: 0, y: l2._y || 70 });
      l1._shine.style.backgroundPosition = `${lerp(130, -40, P(t, 1.0, 1.9, E.inOutCubic)).toFixed(1)}% 0`;
      l2._shine.style.backgroundPosition = `${lerp(140, -30, P(t, 1.08, 1.98, E.inOutCubic)).toFixed(1)}% 0`;

      const from = [[-1500, -300, 300], [-1300, 900, 300], [1300, 900, 300]];
      tags.forEach((g, i) => {
        const p = P(t, 0.16 + i * 0.07, 0.78 + i * 0.07, E.outExpo);
        const spread = P(t, 3.0, 4.4, E.inCubic);
        tf(g.el, {
          x: lerp(from[i][0], g.x, p) + g.x * spread * 0.6 + wob(t, 0.3, i * 0.3, 6),
          y: lerp(from[i][1], g.y, p) + g.y * spread * 0.6 + wob(t, 0.27, i * 0.2 + 0.5, 7),
          z: lerp(from[i][2], g.z, p) + spread * 220,
          ry: lerp(i === 2 ? -40 : 40, 0, p) + wob(t, 0.2, i, 2), rz: lerp(i === 2 ? 8 : -8, 0, p),
        });
      });
      const pm = P(t, 0.0, 0.62, E.outExpo);
      tf(mini, { x: lerp(1100, 620, pm) + wob(t, 0.22, 0.4, 6), y: lerp(-760, -360, pm) + wob(t, 0.26, 0.1, 6), z: lerp(-400, -90, pm), ry: lerp(-35, -8, pm), rz: lerp(10, 2, pm) });

      const sx = box.x0, sy = box.y0, ex = box.x1, ey = box.y1;
      const cx = kf(t, [[0.95, 820], [1.55, 440, E.outCubic], [2.05, sx, E.inOutCubic], [2.75, ex, E.inOutCubic], [3.7, ex + 260, E.inOutSine]]);
      const cy = kf(t, [[0.95, 640], [1.55, 310, E.outCubic], [2.05, sy, E.inOutCubic], [2.75, ey, E.inOutCubic], [3.7, ey + 180, E.inOutSine]]);
      poseCursor(cur, cx, cy, 46, (t > 2.03 && t < 2.78) ? 0.86 : 1, kf(t, [[0.9, 0], [1.05, 1], [3.3, 1], [3.7, 0]]));
      if (t >= 2.05) {
        const rx1 = t < 2.75 ? cx : ex, ry1 = t < 2.75 ? cy : ey;
        const w = Math.max(2, rx1 - sx), h = Math.max(2, ry1 - sy);
        sel.style.width = w + "px"; sel.style.height = h + "px";
        tf(sel, { x: sx, y: sy, z: 26, o: 1, anchor: " " });
        const hp = P(t, 2.76, 2.98, E.outBack);
        const pts = [[0, 0], [0.5, 0], [1, 0], [1, 0.5], [1, 1], [0.5, 1], [0, 1], [0, 0.5]];
        handles.forEach((hd, i) => {
          hd.style.left = pts[i][0] * w + "px"; hd.style.top = pts[i][1] * h + "px";
          const corner = i % 2 === 0;
          const s = t < 2.75 ? (i === 0 || i === 4 ? 1 : 0) : (corner ? 1 : hp);
          hd.style.transform = `translate(-50%,-50%) scale(${s.toFixed(3)})`;
        });
      } else sel.style.visibility = "hidden";

      applyCamera(cam);
      env({ bgName: "intro", grid: 1, wavesO: kf(t, [[0, 0.2], [0.4, 1], [3.6, 1], [4.3, 0]]), chromeO: 1, fadeO: t >= 4.44 ? 1 : kf(t, [[0, 0.6], [0.25, 0]]) });
      bgGrid.style.backgroundPosition = `${(t * 6).toFixed(1)}px ${(t * 3).toFixed(1)}px`;
      const draw = P(t, 0.05, 1.0, E.outCubic);
      for (const [id, len] of [["wave1", 2300], ["wave2", 1100]]) {
        const p = document.getElementById(id);
        p.style.strokeDasharray = `${len}`;
        p.style.strokeDashoffset = `${(len * (1 - draw)).toFixed(1)}`;
      }
      waves.style.transform = `translate(${wob(t, 0.15, 0, 18).toFixed(1)}px, ${wob(t, 0.12, 0.3, 10).toFixed(1)}px)`;
      orb(0, 1250 + wob(t, 0.1, 0, 60), 330, 1100, "rgba(200,243,29,0.20)", 1);
      orb(1, 380 + wob(t, 0.12, 0.5, 50), 860, 900, "rgba(160,220,0,0.13)", 1);
      noOrbs(2);
    }
    return { root, update, measure, range: [0, 4.45] };
  })();

  // ================================================================ 2 — X profile card with 3D avatar
  const profile = (() => {
    const root = mk("div", "sec", world);
    const card = mk("div", "o xcard", root);
    mk("div", "plate glass", card);
    mk("div", "banner", card, `<img src="${A}banner.jpg" alt="">`);
    const follow = mk("div", "follow", card, "Follow");
    mk("div", "who", card, "<b>Aminur Rahaman</b><span>@aminur_rex</span>");
    mk("div", "bio", card, "I help SaaS &amp; tech startups explain their product with animated videos");
    const chipBox = mk("div", "chips", card);
    const chips = [["Product animation", ICON.play(18)], ["Explainers", ICON.bulb(18)], ["Motion graphics", ICON.shapes(18)]]
      .map(([txt, ic]) => mk("div", "chip", chipBox, `<i>${ic}</i>${txt}`));
    const meta = mk("div", "meta", card, `<span>📍 Kolkata, India</span><span>🎬 <b>2,000+</b> videos delivered</span><span>💬 DMs open</span>`);
    const ava = popAvatar(card, 300);
    const emos = [["🎬", 20, 128, 120], ["✨", 330, 118, 140], ["🔥", 368, 236, 110], ["🚀", 12, 372, 130]]
      .map(([e, x, y, z]) => { const el = mk("div", "o emo", card, e); return { el, x, y, z }; });
    const cur = cursor(card);

    function update(t) {
      const rise = P(t, 4.57, 5.05, E.outExpo);
      const pan = P(t, 5.8, 6.1, E.inOutSine);
      const whip = P(t, 6.1, 6.25, E.inExpo);
      tf(card, {
        x: -pan * 140 - whip * 1500, y: lerp(980, 30, rise) + wob(t, 0.3, 0, 4), z: lerp(-260, 0, rise),
        rx: lerp(34, 3, rise) + wob(t, 0.25, 0.2, 1.2),
        ry: lerp(-20, -11, rise) + 17 * P(t, 5.0, 6.1, E.inOutSine) + whip * 25,
        rz: lerp(-4, 0, rise),
      });
      // avatar sits on its own layers: ring on the card, person and emojis in front of it
      tf(ava, { x: 42, y: 116, z: 30 * P(t, 4.7, 5.2, E.outCubic), anchor: " " });
      const pp = P(t, 4.72, 5.2, E.outBack);
      poseAvatar(ava, lerp(0, 34, P(t, 4.72, 5.2, E.outCubic)), lerp(0.82, 1, pp));
      emos.forEach((m, i) => {
        const s = P(t, 4.86 + i * 0.07, 5.2 + i * 0.07, E.outBack);
        tf(m.el, { x: m.x, y: m.y + wob(t, 0.6, i * 0.25, 6), z: m.z, rz: wob(t, 0.4, i * 0.3, 8), sc: s });
      });
      chips.forEach((el, i) => {
        const s = P(t, 5.05 + i * 0.15, 5.4 + i * 0.15, E.outBackSoft);
        el.style.opacity = P(t, 5.05 + i * 0.15, 5.15 + i * 0.15).toFixed(3);
        el.style.transform = `translateY(${lerp(18, 0, s).toFixed(1)}px) scale(${lerp(0.85, 1, s).toFixed(3)})`;
      });
      meta.style.opacity = P(t, 5.42, 5.6).toFixed(3);
      // cursor comes in and follows
      const pressed = t > 5.6 && t < 5.68;
      const following = t >= 5.66;
      follow.classList.toggle("on", following);
      const label = following ? "Following" : "Follow";
      if (follow.textContent !== label) follow.textContent = label;
      follow.style.transform = `scale(${pressed ? 0.92 : 1})`;
      const cx = kf(t, [[5.18, 900], [5.56, 700, E.outCubic], [6.1, 760, E.inOutSine]]);
      const cy = kf(t, [[5.18, 560], [5.56, 322, E.outCubic], [6.1, 390, E.inOutSine]]);
      poseCursor(cur, cx, cy, 60, pressed ? 0.86 : 1, kf(t, [[5.16, 0], [5.26, 1]]));

      applyCamera({
        x: 0, y: 20, z: kf(t, [[4.45, 60], [5.05, 150, E.outExpo], [5.9, 205, E.inOutSine]]),
        rx: 3, ry: 0,
        blur: kf(t, [[4.57, 14], [4.86, 0, E.outCubic]]) + kf(t, [[6.1, 0], [6.25, 14, E.inCubic]]),
      });
      env({ bgName: "dark", grid: 0.35, chromeO: 1, fadeO: t < 4.57 ? 1 : 0,
        flashO: kf(t, [[6.11, 0], [6.13, 0.35], [6.2, 0]]) });
      orb(0, 960 + wob(t, 0.2, 0, 40) - (pan * 200 + whip * 600), 600, 1150, "rgba(200,243,29,0.22)", rise);
      orb(1, 1450, 220, 700, "rgba(200,243,29,0.08)", 1);
      noOrbs(2);
    }
    return { root, update, range: [4.45, 6.25] };
  })();

  // ================================================================ 3 — software
  const software = (() => {
    const root = mk("div", "sec", world);
    const word = mk("div", "o bigword", root, "SOFTWARE");
    const apps = [
      ["After Effects", '<div class="tile adobe">Ae</div>', -300, -170, 0, 6.3, 1.12],
      ["AI tools", `<div class="tile spark">${ICON.spark(150)}</div>`, 250, -130, 60, 6.52, 1.34],
      ["Premiere Pro", '<div class="tile adobe">Pr</div>', -20, 255, 30, 6.86, 1.28],
    ].map(([name, tile, x, y, z, at, sc]) => {
      const el = mk("div", "o glass app", root, `<div class="bar"><span>${name}</span><span class="dots"><i></i><i></i><i></i></span></div>${tile}`);
      el.style.transformStyle = "flat";
      return { el, x, y, z, at, sc };
    });
    function update(t) {
      tf(word, { x: kf(t, [[6.25, 140], [7.45, -90, E.lin]]), y: 40, z: -260 });
      apps.forEach((a, i) => {
        const p = P(t, a.at, a.at + 0.5, E.outBack);
        const q = P(t, a.at, a.at + 0.45, E.outExpo);
        tf(a.el, {
          x: a.x + wob(t, 0.35, i * 0.3, 5), y: a.y + lerp(80, 0, q) + wob(t, 0.3, i * 0.2, 6), z: lerp(-260, a.z, q),
          rz: lerp(i === 1 ? 10 : -10, 0, q) + wob(t, 0.25, i, 1.2), ry: lerp(25, 0, q),
          sc: a.sc * lerp(0.3, 1, p), o: P(t, a.at, a.at + 0.1),
        });
      });
      // racks into focus out of the whip
      applyCamera({
        x: 0, y: 0, z: kf(t, [[6.25, -320], [6.45, 0, E.outCubic], [7.45, 70, E.inOutSine]]),
        rx: kf(t, [[6.25, 6], [7.45, 2]]), ry: kf(t, [[6.25, -9], [7.45, 5]]),
        blur: kf(t, [[6.25, 12], [6.42, 0, E.outCubic]]),
      });
      env({ bgName: "dark", grid: 0.5, chromeO: 1 });
      orb(0, 900, 520, 1300, "rgba(200,243,29,0.15)", 1);
      orb(1, 1500, 860, 700, "rgba(200,243,29,0.07)", 1);
      noOrbs(2);
    }
    return { root, update, range: [6.25, 7.45] };
  })();

  // ================================================================ 4 — chat message
  const chat = (() => {
    const MSG = "I help SaaS & tech startups explain their product.";
    const root = mk("div", "sec", world);
    const card = mk("div", "o glass chat", root, `
      <div class="dots"><i></i><i></i><i></i></div>
      <div class="row"><div class="av"><img src="${A}avatar.png" alt=""></div>
        <div class="txtcol"><div class="who">Aminur<small>00:30</small></div><div class="msg"><span class="txt"></span><span class="caret"></span></div></div></div>
      <div class="send">Send</div>`);
    card.style.transformStyle = "flat";
    const rowEl = card.querySelector(".row");
    const txt = card.querySelector(".txt");
    const caret = card.querySelector(".caret");
    const send = card.querySelector(".send");
    const cur = cursor(root);
    const SC = 1.28;

    function update(t) {
      // hard cut in: the card hangs tilted and dim, then swings flat
      const p = P(t, 7.45, 8.12, E.outCubic);
      tf(card, {
        x: lerp(120, 0, p), y: lerp(70, 0, p) + wob(t, 0.3, 0, 4), z: lerp(-220, 0, p),
        rx: lerp(30, 0, p) + wob(t, 0.25, 0.3, 1), ry: lerp(-40, 0, p) + wob(t, 0.2, 0.1, 1.5), rz: lerp(-7, 0, p),
        sc: SC, o: lerp(0.35, 1, P(t, 7.45, 7.9, E.outCubic)),
      });
      rowEl.style.opacity = P(t, 7.52, 7.68).toFixed(3);
      const n = Math.round(P(t, 7.78, 8.62) * MSG.length);
      if (txt.textContent.length !== n) txt.textContent = MSG.slice(0, n);
      caret.style.opacity = (t < 8.62 || Math.floor(t * 3) % 2 === 0) ? "1" : "0";
      const sp = P(t, 8.35, 8.68, E.outBack);
      const pressed = t > 9.46 && t < 9.6;
      send.style.transform = `scale(${(sp * (pressed ? 0.9 : 1)).toFixed(3)})`;
      send.style.filter = t > 9.46 && t < 9.95 ? `brightness(${(1.3 - 0.3 * P(t, 9.5, 9.95)).toFixed(3)})` : "none";
      const cx = kf(t, [[8.5, 640], [8.95, 480, E.outCubic], [9.3, 345, E.inOutCubic], [10.12, 340]]);
      const cy = kf(t, [[8.5, 420], [8.95, 260, E.outCubic], [9.3, 108, E.inOutCubic], [10.12, 106]]);
      poseCursor(cur, cx * SC + wob(t, 0.9, 0, 3), cy * SC + wob(t, 0.8, 0.4, 3), 40, pressed ? 0.86 : 1, kf(t, [[8.48, 0], [8.6, 1]]));

      applyCamera({ x: 0, y: 0, z: kf(t, [[7.45, 0], [10.12, 120, E.inOutSine]]), rx: kf(t, [[7.45, 5], [10.12, 2]]), ry: kf(t, [[7.45, -6], [10.12, 4]]), blur: 0 });
      env({ bgName: "dark", grid: 0.3, chromeO: 1 });
      orb(0, 960 + wob(t, 0.18, 0, 50), 560, 1250, "rgba(200,243,29,0.20)", P(t, 7.45, 7.9));
      orb(1, 300, 200, 700, "rgba(200,243,29,0.07)", 1);
      orb(2, 1150, 610, 420, "rgba(220,255,90,0.5)", P(t, 9.5, 9.6) * (1 - P(t, 9.6, 10.0)));
    }
    return { root, update, range: [7.45, 10.12] };
  })();

  // ================================================================ 5-7 — work grids
  const grids = (() => {
    const root = mk("div", "sec", world);
    const SEG = [
      { at: 10.12, end: 13.3, label: "PRODUCT ANIMATION", clips: ["g1_commas", "g1_fortknox", "g1_neural", "g1_nano"], enter: "pullback" },
      { at: 13.3, end: 17.83, label: "EXPLAINERS", clips: ["g3_nano", "g3_fortknox", "g3_commas", "g3_neural"], enter: "dark" },
      { at: 17.83, end: 22.65, label: "MOTION GRAPHICS", clips: ["g2_fortknox", "g2_commas", "g2_nano", "g2_neural"], enter: "cut" },
    ];
    const POS = [[-425, -252], [425, -252], [-425, 252], [425, 252]];
    const cards = POS.map(([x, y]) => {
      const el = mk("div", "o card", root);
      el.style.transformStyle = "flat";
      const img = mk("img", "", el);
      const shade = mk("div", "shade", el);
      mk("div", "gloss", el);
      return { el, img, shade, x, y, src: "" };
    });
    const labels = SEG.map((s) => {
      const box = mk("div", "o", root);
      const inner = mk("div", "o", box);
      const letters = [];
      for (const ch of s.label) {
        if (ch === " ") { letters.push(null); continue; }
        const L = extruded(ch, 92, { depth: 14, step: 1.7, glow: false });
        inner.appendChild(L);
        letters.push(L);
      }
      return { box, inner, letters, xs: [], fit: 1 };
    });
    function measure() {
      labels.forEach((lb) => {
        const space = 32, gap = 2;
        const ws = lb.letters.map((L) => (L ? L._face.offsetWidth : space));
        const total = ws.reduce((a, b) => a + b, 0) + gap * (ws.length - 1);
        let x = -total / 2;
        lb.xs = ws.map((w) => { const c = x + w / 2; x += w + gap; return c; });
        lb.fit = Math.min(1, 1240 / total);
      });
    }
    const pending = [];

    function update(t) {
      const gi = t < SEG[1].at ? 0 : t < SEG[2].at ? 1 : 2;
      const seg = SEG[gi];
      const lt = t - seg.at;
      cards.forEach((c, i) => {
        const idx = clamp(Math.floor((lt + 0.2) * CLIP_FPS) + 1, 1, CLIP_FRAMES);
        const src = `${CLIPS}/${seg.clips[i]}/${String(idx).padStart(4, "0")}.jpg`;
        if (c.src !== src) { c.src = src; c.img.src = src; pending.push(c.img.decode().catch(() => {})); }
        let s = 1, shade = 0;
        if (seg.enter === "pullback") s = lerp(0.92, 1, P(t, seg.at + i * 0.03, seg.at + 0.45 + i * 0.03, E.outExpo));
        if (seg.enter === "dark") {
          shade = 1 - P(t, seg.at + 0.04 + i * 0.05, seg.at + 0.34 + i * 0.05, E.outCubic);
          s = lerp(1.05, 1, P(t, seg.at, seg.at + 0.5, E.outExpo));
        }
        if (seg.enter === "cut") s = lerp(1.03, 1, P(t, seg.at, seg.at + 0.4, E.outExpo));
        tf(c.el, {
          x: c.x + wob(t, 0.18, i * 0.25, 6), y: c.y + wob(t, 0.2, i * 0.2 + 0.4, 6), z: wob(t, 0.15, i * 0.3, 14),
          rx: wob(t, 0.13, i * 0.17, 1.2), ry: wob(t, 0.11, i * 0.29, 1.6), sc: s,
        });
        c.img.style.transform = `scale(${lerp(1.08, 1.0, P(t, seg.at, seg.end, E.outCubic)).toFixed(4)})`;
        c.shade.style.opacity = shade.toFixed(3);
      });

      labels.forEach((lb, li) => {
        const on = li === gi;
        show(lb.box, on);
        if (!on) return;
        // grid 1 and 2 labels grow in from small; grid 3 cuts in at full size (as in the reference)
        let s = 1;
        if (seg.enter === "pullback") s = lerp(0.2, 1, P(t, seg.at + 0.12, seg.at + 0.52, E.outBack));
        if (seg.enter === "dark") s = lerp(0.15, 1, P(t, seg.at + 0.12, seg.at + 0.48, E.outBack));
        tf(lb.box, { x: wob(t, 0.2, 0, 8), y: 2 + wob(t, 0.23, 0.3, 4), z: 70, sc: s * lb.fit, anchor: " " });
        tf(lb.inner, { anchor: " " });
        lb.letters.forEach((L, k) => {
          if (!L) return;
          tf(L, { x: lb.xs[k], y: 0 });
          L._shine.style.backgroundPosition = `${lerp(130, -40, P(t, seg.at + 0.6 + k * 0.02, seg.at + 1.4 + k * 0.02, E.inOutCubic)).toFixed(1)}% 0`;
        });
      });

      const z0 = seg.enter === "pullback" ? lerp(1100, 0, P(t, seg.at, seg.at + 0.38, E.outExpo))
        : seg.enter === "dark" ? lerp(140, 0, P(t, seg.at, seg.at + 0.5, E.outExpo))
        : lerp(80, 0, P(t, seg.at, seg.at + 0.35, E.outExpo));
      applyCamera({
        x: wob(t, 0.07, 0.1, 40), y: 10 + wob(t, 0.09, 0.4, 16),
        z: z0 + lerp(0, 70, P(t, seg.at, seg.end, E.inOutSine)),
        rx: 11 + wob(t, 0.08, 0.2, 2.2),
        ry: lerp(-7, 5, P(t, seg.at, seg.end, E.inOutSine)) * (gi === 1 ? -1 : 1),
        rz: wob(t, 0.06, 0.6, 0.6),
        blur: seg.enter === "pullback" ? lerp(16, 0, P(t, seg.at, seg.at + 0.32, E.outCubic)) : 0,
      });
      env({ bgName: "grid", grid: 0.8, fadeO: kf(t, [[22.0, 0], [22.6, 1, E.inOutCubic]]),
        flashO: gi === 0 ? kf(t, [[10.12, 0.25], [10.4, 0]]) : gi === 1 ? kf(t, [[13.3, 0.18], [13.5, 0]]) : kf(t, [[17.83, 0.3], [18.05, 0]]) });
      bgGrid.style.backgroundPosition = `${(t * -8).toFixed(1)}px ${(t * 4).toFixed(1)}px`;
      orb(0, 960 + wob(t, 0.1, 0, 120), 520, 1400, "rgba(200,243,29,0.13)", 1);
      orb(1, 300 + wob(t, 0.08, 0.5, 80), 950, 900, "rgba(160,220,0,0.10)", 1);
      orb(2, 1650, 120, 800, "rgba(220,255,120,0.07)", 1);
    }
    return { root, update, measure, pending, range: [10.12, 22.62] };
  })();

  // ================================================================ 8 — end card
  const outro = (() => {
    const root = mk("div", "sec", world);
    // the handle and tagline live in the flat overlay: Chromium's 3D sorting against the
    // swinging avatar dropped tiles of the text when they shared the 3D scene
    const flat = mk("div", "flat", overlay);
    const ava = popAvatar(root, 360);
    ava._ring.style.boxShadow = "0 0 0 2px rgba(200,243,29,0.6), 0 0 70px rgba(200,243,29,0.45)";
    ava._img.style.filter = "none";
    const handle = mk("div", "o handle", flat, "@aminur_rex");
    const tag = mk("div", "o tagline", flat, "2,000+ VIDEOS DELIVERED &nbsp;·&nbsp; DMs OPEN");
    const spark = mk("div", "o", root);
    spark.style.cssText += "width:4px;height:240px;border-radius:4px;background:linear-gradient(180deg,transparent,#efffb0 70%,#fff);box-shadow:0 0 18px #c8f31d,0 0 40px #a8dc00";
    const burst = mk("div", "o", root);
    burst.style.cssText += "width:560px;height:560px;border-radius:50%;background:radial-gradient(circle,rgba(240,255,200,.6),rgba(200,243,29,.28) 35%,transparent 66%)";
    const smoke = [0, 1, 2].map(() => {
      const s = mk("div", "o", root);
      s.style.cssText += "width:900px;height:520px;border-radius:50%;background:radial-gradient(ellipse,rgba(245,250,235,.5),rgba(200,243,29,.14) 45%,transparent 70%)";
      return s;
    });

    function update(t) {
      const appear = P(t, 22.7, 23.2, E.outCubic);
      const hit = P(t, 23.18, 23.42, E.outExpo);
      const gone = P(t, 24.35, 24.95, E.inOutCubic);
      const o = (0.35 * appear + 0.65 * hit) * (1 - gone);
      tf(handle, { x: 0, y: 190, z: 0, sc: lerp(1.06, 1, hit) * lerp(1, 0.97, gone), o, blur: lerp(10, 0, appear) * (1 - hit) + gone * 6 });
      // glow lives in text-shadow: a separate blurred copy got mis-sorted against the rotating 3D avatar
      const pulse = 0.5 + 0.5 * Math.sin((t - 23.4) * Math.PI * 2 * 0.9);
      handle.style.textShadow = `0 0 ${lerp(10, 24, hit).toFixed(1)}px rgba(200,243,29,${(0.45 + 0.45 * hit).toFixed(2)}), 0 0 ${lerp(30, 70 + 20 * pulse, hit).toFixed(1)}px rgba(160,220,0,${(0.25 + 0.35 * hit).toFixed(2)})`;
      // the 3D avatar swings slowly so the pop-out reads as depth
      const ap = P(t, 23.18, 23.7, E.outBack);
      tf(ava, { x: 0, y: -140, z: 0, ry: lerp(-16, 12, P(t, 23.2, 24.9, E.inOutSine)), rx: 6, sc: lerp(0.5, 1, ap) * lerp(1, 0.94, gone) });
      ava._ring.style.opacity = ava._pop.style.opacity = (P(t, 23.18, 23.3) * (1 - gone)).toFixed(3);
      poseAvatar(ava, 40, lerp(0.85, 1, P(t, 23.25, 23.75, E.outBack)));
      tf(tag, { x: 0, y: 272, z: 0, o: P(t, 23.45, 23.85, E.outCubic) * (1 - gone), blur: lerp(6, 0, P(t, 23.45, 23.85)) });
      const sp = P(t, 22.95, 23.2, E.inCubic);
      tf(spark, { x: 6, y: lerp(-760, -330, sp), z: 10, o: (t > 22.95 && t < 23.22) ? 1 : 0 });
      tf(burst, { x: 0, y: -140, z: -5, sc: lerp(0.3, 1.25, P(t, 23.18, 23.62, E.outCubic)), o: kf(t, [[23.18, 0], [23.22, 0.85], [23.72, 0, E.outCubic]]) });
      smoke.forEach((s, i) => {
        const p = P(t, 24.05 + i * 0.12, 25.05, E.outCubic);
        tf(s, { x: lerp(900 - i * 120, 250 - i * 260, p), y: 300 - i * 70 + wob(t, 0.3, i * 0.3, 20), z: 20, sc: lerp(0.7, 1.5, p), o: kf(t, [[24.05 + i * 0.12, 0], [24.45 + i * 0.12, 0.8], [25.05, 0.3]]), blur: 30 });
      });
      const camZ = kf(t, [[22.6, -40], [25.05, 60, E.lin]]);
      applyCamera({ x: 0, y: 0, z: camZ, rx: 0, ry: 0, blur: 0 });
      flat.style.transform = `scale(${(1500 / (1500 - camZ)).toFixed(4)})`;
      env({ bgName: "black", fadeO: kf(t, [[22.6, 1], [22.75, 0], [24.8, 0], [25.05, 1]]) });
      orb(0, 960, 520, 1200, "rgba(200,243,29,0.13)", (0.3 + 0.7 * hit) * (1 - gone));
      noOrbs(1);
    }
    return { root, extra: flat, update, range: [22.62, 25.1] };
  })();

  const SECTIONS = [intro, profile, software, chat, grids, outro];

  let ready = null;
  async function setup() {
    for (const f of ['800 150px "Unbounded"', '600 84px "Unbounded"', '900 300px "Unbounded"', '700 30px "Sora"', '600 30px "Sora"', '500 30px "Sora"'])
      await document.fonts.load(f);
    await document.fonts.load('54px "Noto Color Emoji"', "🎬🔥✨🚀📍💬");
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
      if (s.extra) show(s.extra, on);
      if (on && !active) active = s;
    }
    if (!active) active = SECTIONS[SECTIONS.length - 1];
    show(active.root, true);
    if (active.extra) show(active.extra, true);
    active.update(t);
    const f = Math.floor(t * 60);
    grain.style.backgroundImage = `url(${grainTiles[f % grainTiles.length]})`;
    grain.style.backgroundPosition = `${(f * 37) % 256}px ${(f * 91) % 256}px`;
    await Promise.all(grids.pending.splice(0));
  };
  window.__duration = DURATION;
  if (Q.has("t")) window.__render(parseFloat(Q.get("t")));
})();
