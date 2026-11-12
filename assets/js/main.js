/* ==========================================================================
   Aminur Rex SFX Pack — page behaviour
   - Currency: ₹ INR in India, $ USD elsewhere (time-zone based, switchable)
   - Hero timeline "Play the edit" demo (UI-style sounds synthesised in the browser)
   - Buy flow, sticky mobile buy bar, reveal animations
   ========================================================================== */
(() => {
  "use strict";

  const C = window.STORE_CONFIG || {};
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const clamp01 = (v) => Math.min(1, Math.max(0, v));
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
  };
  // Analytics (analytics.js). Does nothing if that script didn't load.
  const track = (name, tags) => { if (typeof window.track === "function") window.track(name, tags); };
  const escapeHTML = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ======================================================================
     Pricing & currency
     ====================================================================== */
  const Pricing = (() => {
    const KEY_CUR = "store.currency";
    const KEY_RATE = "store.inrUsd";
    const RATE_TTL = 12 * 60 * 60 * 1000;
    const price = Object.assign({ inr: 99, inrOriginal: 199 }, C.price);

    const state = {
      currency: "INR",
      how: "auto",
      rate: Number(C.fallbackInrToUsd) || 0.0113,
      live: false,
      fetching: false,
    };

    const fmtINR = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
    const fmtUSD = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const fmt = (v, cur) => (cur === "INR" ? fmtINR : fmtUSD).format(v);
    const round2 = (v) => Math.round(v * 100) / 100;

    function detect() {
      const saved = store.get(KEY_CUR);
      if (saved === "INR" || saved === "USD") return { currency: saved, how: "saved" };

      let tz = "";
      try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch { /* ignore */ }
      const indiaZones = C.indiaTimeZones || ["Asia/Kolkata", "Asia/Calcutta"];
      if (tz) return { currency: indiaZones.includes(tz) ? "INR" : "USD", how: "auto" };

      // No time zone available: fall back to the browser's language region.
      const langs = navigator.languages || [navigator.language || ""];
      return { currency: langs.some((l) => /-IN$/i.test(l)) ? "INR" : "USD", how: "auto" };
    }

    function amounts(cur = state.currency) {
      if (cur === "INR") return { now: price.inr, was: price.inrOriginal };
      if (C.fixedUSD && C.fixedUSD.price) {
        return { now: Number(C.fixedUSD.price), was: Number(C.fixedUSD.original || C.fixedUSD.price) };
      }
      return { now: round2(price.inr * state.rate), was: round2(price.inrOriginal * state.rate) };
    }

    function render() {
      const cur = state.currency;
      const { now, was } = amounts();
      const save = round2(Math.max(0, was - now));
      const pct = was > 0 ? Math.round((1 - now / was) * 100) : 0;

      $$("[data-price]").forEach((el) => { el.textContent = fmt(now, cur); });
      $$("[data-price-original]").forEach((el) => { el.textContent = fmt(was, cur); });
      $$("[data-save]").forEach((el) => { el.textContent = fmt(save, cur); });
      $$("[data-discount]").forEach((el) => { el.textContent = `${pct}% off`; });
      $$("[data-discount-pct]").forEach((el) => { el.textContent = `${pct}%`; });
      $$("[data-currency-label]").forEach((el) => { el.textContent = cur === "INR" ? "₹ INR" : "$ USD"; });
      $$("[data-currency-switch]").forEach((el) => { el.textContent = cur === "INR" ? "Switch to $ USD" : "Switch to ₹ INR"; });

      $$("[data-segmented]").forEach((seg) => {
        seg.dataset.active = cur;
        $$("[data-currency]", seg).forEach((btn) => {
          const on = btn.dataset.currency === cur;
          btn.setAttribute("aria-checked", String(on));
          btn.tabIndex = on ? 0 : -1;
        });
      });

      const geo = state.how === "saved"
        ? (cur === "INR" ? "Showing prices in ₹ INR." : "Showing prices in $ USD.")
        : (cur === "INR" ? "Prices shown in ₹ INR for India." : "You're outside India, so prices are shown in $ USD.");
      $$("[data-geo-note]").forEach((el) => { el.textContent = geo; });

      $$("[data-rate-note]").forEach((el) => {
        const converted = cur === "USD" && !(C.fixedUSD && C.fixedUSD.price);
        el.hidden = !converted;
        if (converted) {
          el.textContent = `About ${fmt(price.inr, "INR")} at ${state.live ? "today's" : "an approximate"} exchange rate. Checkout shows the exact amount in your currency.`;
        }
      });

      document.documentElement.dataset.currency = cur;
    }

    async function loadRate() {
      if ((C.fixedUSD && C.fixedUSD.price) || state.live || state.fetching) return;

      try {
        const cached = JSON.parse(store.get(KEY_RATE) || "null");
        if (cached && cached.r > 0 && Date.now() - cached.t < RATE_TTL) {
          state.rate = cached.r;
          state.live = true;
          render();
          return;
        }
      } catch { /* ignore bad cache */ }

      if (!C.rateApi || !window.fetch) return;
      state.fetching = true;
      const ctrl = "AbortController" in window ? new AbortController() : null;
      const timer = ctrl && setTimeout(() => ctrl.abort(), 5000);
      try {
        const res = await fetch(C.rateApi, { signal: ctrl && ctrl.signal, cache: "no-store" });
        const data = await res.json();
        const r = data && data.rates && Number(data.rates.USD);
        if (r > 0 && r < 1) {
          state.rate = r;
          state.live = true;
          store.set(KEY_RATE, JSON.stringify({ r, t: Date.now() }));
          render();
        }
      } catch { /* keep fallback rate */ }
      finally {
        state.fetching = false;
        if (timer) clearTimeout(timer);
      }
    }

    function set(cur, { save = true } = {}) {
      if (cur !== "INR" && cur !== "USD") return;
      state.currency = cur;
      if (save) {
        state.how = "saved";
        store.set(KEY_CUR, cur);
        track("currency_switch", { currency: cur });
      }
      render();
      if (cur === "USD") loadRate();
    }

    function init() {
      const d = detect();
      state.currency = d.currency;
      state.how = d.how;
      render();
      if (state.currency === "USD") loadRate();

      document.addEventListener("click", (e) => {
        const pick = e.target.closest("[data-currency]");
        if (pick) { set(pick.dataset.currency); return; }
        if (e.target.closest("[data-currency-switch]")) set(state.currency === "INR" ? "USD" : "INR");
      });

      // Arrow keys move between segments (radio-group pattern).
      $$("[data-segmented]").forEach((seg) => {
        seg.addEventListener("keydown", (e) => {
          if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) return;
          e.preventDefault();
          set(state.currency === "INR" ? "USD" : "INR");
          const active = $(`[data-currency="${state.currency}"]`, seg);
          if (active) active.focus();
        });
      });
    }

    return { init, get currency() { return state.currency; } };
  })();

  /* ======================================================================
     Audio: playback + demo synthesis
     ====================================================================== */
  const Player = (() => {
    let ctx = null;
    let analyser = null;
    let current = null;
    const listeners = new Set();
    const notify = (playing) => listeners.forEach((fn) => fn(playing));

    function audio() {
      if (!ctx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return null;
        ctx = new AC();
        analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.72;
        analyser.connect(ctx.destination);
        // Let iPhone play even with the silent switch on (Safari 17+).
        try { if (navigator.audioSession) navigator.audioSession.type = "playback"; } catch { /* ignore */ }
      }
      if (ctx.state === "suspended") ctx.resume();
      return ctx;
    }

    /** Loudness (0–1) of `edges.length - 1` frequency bands of whatever is playing. */
    const bins = new Uint8Array(128);
    function levels(edges) {
      if (!analyser || !current) return null;
      analyser.getByteFrequencyData(bins);
      const out = [];
      for (let i = 0; i < edges.length - 1; i++) {
        let sum = 0;
        for (let k = edges[i]; k < edges[i + 1]; k++) sum += bins[k];
        out.push(sum / (edges[i + 1] - edges[i]) / 255);
      }
      return out;
    }

    function stopAll() {
      if (!current) return;
      const session = current;
      current = null;
      session.sources.forEach((s) => { try { s.stop(); } catch { /* already stopped */ } });
      try { session.out.disconnect(); } catch { /* ignore */ }
      if (session.onStop) session.onStop();
      notify(false);
    }

    /** list: [{ buffer, at }] — `at` is seconds from start. */
    function play(list, onStop) {
      stopAll();
      const c = audio();
      if (!c) return null;
      const t0 = c.currentTime + 0.06;
      const out = c.createGain();
      out.gain.value = 0.9;
      out.connect(analyser || c.destination);
      const sources = list.map(({ buffer, at = 0 }) => {
        const s = c.createBufferSource();
        s.buffer = buffer;
        s.connect(out);
        s.start(t0 + at);
        return s;
      });
      current = { sources, out, onStop, t0 };
      notify(true);
      return current;
    }

    return {
      audio,
      play,
      stopAll,
      levels,
      subscribe: (fn) => listeners.add(fn),
      isCurrent: (s) => s !== null && s === current,
      elapsed: (s) => (ctx ? ctx.currentTime - s.t0 : 0),
    };
  })();

  const Synth = (() => {
    const SR = 44100;
    const OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    const cache = new Map();

    const rng = (seed) => {
      let s = (seed >>> 0) % 2147483647 || 1;
      return () => (s = (s * 16807) % 2147483647) / 2147483647;
    };

    function noiseSrc(ctx, sec, seed = 7) {
      const len = Math.max(1, Math.floor(ctx.sampleRate * sec));
      const buf = ctx.createBuffer(1, len, ctx.sampleRate);
      const d = buf.getChannelData(0);
      const r = rng(seed);
      for (let i = 0; i < len; i++) d[i] = r() * 2 - 1;
      const src = ctx.createBufferSource();
      src.buffer = buf;
      return src;
    }

    function gainEnv(ctx, points) {
      const g = ctx.createGain();
      const [t0, v0] = points[0];
      g.gain.setValueAtTime(v0, t0);
      for (let i = 1; i < points.length; i++) {
        const [t, v, kind] = points[i];
        if (kind === "set") g.gain.setValueAtTime(v, t);
        else if (kind === "lin") g.gain.linearRampToValueAtTime(v, t);
        else g.gain.exponentialRampToValueAtTime(Math.max(v, 0.0001), t);
      }
      return g;
    }

    function filter(ctx, type, freq, q) {
      const f = ctx.createBiquadFilter();
      f.type = type;
      f.frequency.value = freq;
      if (q != null) f.Q.value = q;
      return f;
    }

    function panner(ctx, from, to, dur) {
      if (!ctx.createStereoPanner) return null;
      const p = ctx.createStereoPanner();
      p.pan.setValueAtTime(from, 0);
      if (to !== undefined) p.pan.linearRampToValueAtTime(to, dur);
      return p;
    }

    function reverb(ctx, seconds, decay, seed) {
      const len = Math.floor(ctx.sampleRate * seconds);
      const buf = ctx.createBuffer(2, len, ctx.sampleRate);
      for (let ch = 0; ch < 2; ch++) {
        const d = buf.getChannelData(ch);
        const r = rng(seed + ch * 101);
        for (let i = 0; i < len; i++) d[i] = (r() * 2 - 1) * Math.pow(1 - i / len, decay);
      }
      const conv = ctx.createConvolver();
      conv.buffer = buf;
      return conv;
    }

    function softClip(ctx, amount) {
      const ws = ctx.createWaveShaper();
      const n = 2048;
      const curve = new Float32Array(n);
      for (let i = 0; i < n; i++) {
        const x = (i / (n - 1)) * 2 - 1;
        curve[i] = Math.tanh(x * amount) / Math.tanh(amount);
      }
      ws.curve = curve;
      return ws;
    }

    function airSweep(ctx, out, { dur, seed, type = "bandpass", q, f0, fPeak, f1, peakAt, gain = 1, pan }) {
      const n = noiseSrc(ctx, dur, seed);
      const f = filter(ctx, type, f0, q);
      f.frequency.setValueAtTime(f0, 0);
      f.frequency.exponentialRampToValueAtTime(fPeak, dur * peakAt);
      f.frequency.exponentialRampToValueAtTime(f1, dur);
      const g = gainEnv(ctx, [[0, 0.0001], [dur * peakAt, gain], [dur, 0.0001]]);
      n.connect(f).connect(g);
      const p = pan ? panner(ctx, pan[0], pan[1], dur) : null;
      if (p) g.connect(p).connect(out); else g.connect(out);
      n.start(0);
    }

    const recipes = {
      whoosh: {
        dur: 1.2,
        build(ctx, out) {
          airSweep(ctx, out, { dur: 1.2, seed: 3, q: 0.9, f0: 220, fPeak: 2600, f1: 320, peakAt: 0.52, gain: 1, pan: [-0.85, 0.85] });
          airSweep(ctx, out, { dur: 1.2, seed: 5, type: "highpass", f0: 1500, fPeak: 5200, f1: 1800, peakAt: 0.52, gain: 0.22, pan: [-0.6, 0.6] });
        },
      },
      swish: {
        dur: 0.6,
        build(ctx, out) {
          airSweep(ctx, out, { dur: 0.55, seed: 19, q: 1.8, f0: 1100, fPeak: 5600, f1: 1700, peakAt: 0.38, gain: 1, pan: [0.8, -0.8] });
        },
      },
      impact: {
        dur: 2.0,
        build(ctx, out) {
          const verb = reverb(ctx, 1.8, 2.6, 21);
          const wet = ctx.createGain();
          wet.gain.value = 0.32;
          verb.connect(wet).connect(out);

          const body = ctx.createOscillator();
          body.type = "sine";
          body.frequency.setValueAtTime(160, 0);
          body.frequency.exponentialRampToValueAtTime(42, 0.45);
          const bodyEnv = gainEnv(ctx, [[0, 0.0001], [0.006, 1], [1.5, 0.0001]]);
          const clip = softClip(ctx, 3);
          body.connect(bodyEnv).connect(clip);
          clip.connect(out);
          clip.connect(verb);

          const crack = noiseSrc(ctx, 0.5, 9);
          const lp = filter(ctx, "lowpass", 5000);
          lp.frequency.setValueAtTime(5000, 0);
          lp.frequency.exponentialRampToValueAtTime(400, 0.25);
          const crackEnv = gainEnv(ctx, [[0, 0.0001], [0.003, 0.9], [0.35, 0.0001]]);
          crack.connect(lp).connect(crackEnv);
          crackEnv.connect(out);
          crackEnv.connect(verb);

          const rumble = noiseSrc(ctx, 1.9, 13);
          const rumbleEnv = gainEnv(ctx, [[0, 0.0001], [0.02, 0.5], [1.85, 0.0001]]);
          rumble.connect(filter(ctx, "lowpass", 260)).connect(rumbleEnv).connect(out);

          body.start(0); body.stop(1.6);
          crack.start(0);
          rumble.start(0);
        },
      },
      riser: {
        dur: 2.6,
        build(ctx, out) {
          const d = 2.4;
          const master = gainEnv(ctx, [[0, 0.0001], [d, 0.9], [d, 0.9, "set"], [d + 0.06, 0.0001]]);
          master.connect(out);

          const trem = ctx.createGain();
          trem.gain.value = 0.7;
          const lfo = ctx.createOscillator();
          lfo.frequency.setValueAtTime(3, 0);
          lfo.frequency.exponentialRampToValueAtTime(18, d);
          const lfoAmt = ctx.createGain();
          lfoAmt.gain.value = 0.3;
          lfo.connect(lfoAmt).connect(trem.gain);
          trem.connect(master);

          const lp = filter(ctx, "lowpass", 300, 6);
          lp.frequency.setValueAtTime(300, 0);
          lp.frequency.exponentialRampToValueAtTime(7000, d);
          lp.connect(trem);

          [-27, 0, 21].forEach((detune) => {
            const o = ctx.createOscillator();
            o.type = "sawtooth";
            o.detune.value = detune;
            o.frequency.setValueAtTime(110, 0);
            o.frequency.exponentialRampToValueAtTime(880, d);
            const g = ctx.createGain();
            g.gain.value = 0.25;
            o.connect(g).connect(lp);
            o.start(0);
            o.stop(d + 0.1);
          });

          const air = noiseSrc(ctx, d + 0.1, 17);
          const hp = filter(ctx, "highpass", 400);
          hp.frequency.setValueAtTime(400, 0);
          hp.frequency.exponentialRampToValueAtTime(9000, d);
          const airGain = ctx.createGain();
          airGain.gain.value = 0.35;
          air.connect(hp).connect(airGain).connect(trem);

          lfo.start(0); lfo.stop(d + 0.1);
          air.start(0);
        },
      },
      glitch: {
        dur: 1.0,
        build(ctx, out) {
          const r = rng(42);
          const master = ctx.createGain();
          master.gain.value = 0.8;
          master.connect(out);
          let t = 0.005;
          while (t < 0.88) {
            const len = 0.02 + r() * 0.06;
            const g = ctx.createGain();
            g.gain.setValueAtTime(0, t);
            g.gain.linearRampToValueAtTime(0.9, t + 0.002);
            g.gain.setValueAtTime(0.9, t + len - 0.004);
            g.gain.linearRampToValueAtTime(0, t + len);
            if (r() < 0.55) {
              const o = ctx.createOscillator();
              o.type = r() < 0.5 ? "square" : "sawtooth";
              o.frequency.setValueAtTime(120 + r() * 1800, t);
              if (r() < 0.5) o.frequency.exponentialRampToValueAtTime(60 + r() * 3000, t + len);
              o.connect(g);
              o.start(t);
              o.stop(t + len + 0.01);
            } else {
              const n = noiseSrc(ctx, len + 0.01, Math.floor(r() * 1000) + 1);
              n.connect(filter(ctx, "bandpass", 500 + r() * 6000, 4)).connect(g);
              n.start(t);
            }
            const p = panner(ctx, (r() * 2 - 1) * 0.8);
            if (p) g.connect(p).connect(master); else g.connect(master);
            t += len + (r() < 0.3 ? r() * 0.05 : 0);
          }
        },
      },
      subdrop: {
        dur: 2.4,
        build(ctx, out) {
          const env = gainEnv(ctx, [[0, 0.0001], [0.02, 1], [0.3, 1, "set"], [2.3, 0.0001]]);
          const clip = softClip(ctx, 1.8);
          env.connect(clip).connect(out);
          const o = ctx.createOscillator();
          o.frequency.setValueAtTime(110, 0);
          o.frequency.exponentialRampToValueAtTime(30, 1.9);
          o.connect(env);
          const h = ctx.createOscillator();
          h.type = "triangle";
          h.frequency.setValueAtTime(220, 0);
          h.frequency.exponentialRampToValueAtTime(60, 1.9);
          const hg = ctx.createGain();
          hg.gain.value = 0.28;
          h.connect(hg).connect(env);
          o.start(0); o.stop(2.35);
          h.start(0); h.stop(2.35);
        },
      },
      pop: {
        dur: 0.4,
        build(ctx, out) {
          const o = ctx.createOscillator();
          o.frequency.setValueAtTime(260, 0);
          o.frequency.exponentialRampToValueAtTime(1150, 0.045);
          o.frequency.exponentialRampToValueAtTime(900, 0.2);
          o.connect(gainEnv(ctx, [[0, 0.0001], [0.004, 1], [0.28, 0.0001]])).connect(out);
          o.start(0); o.stop(0.35);
          const n = noiseSrc(ctx, 0.03, 77);
          n.connect(filter(ctx, "highpass", 3000)).connect(gainEnv(ctx, [[0, 0.4], [0.025, 0.0001]])).connect(out);
          n.start(0);
        },
      },
      click: {
        dur: 0.3,
        build(ctx, out) {
          const tick = (t, f, v) => {
            const o = ctx.createOscillator();
            o.type = "triangle";
            o.frequency.setValueAtTime(f, t);
            o.frequency.exponentialRampToValueAtTime(f * 0.6, t + 0.04);
            o.connect(gainEnv(ctx, [[t, 0.0001], [t + 0.002, v], [t + 0.05, 0.0001]])).connect(out);
            o.start(t);
            o.stop(t + 0.06);
          };
          tick(0.002, 2400, 1);
          tick(0.075, 1800, 0.6);
          const n = noiseSrc(ctx, 0.012, 5);
          n.connect(filter(ctx, "highpass", 4000)).connect(gainEnv(ctx, [[0, 0.5], [0.01, 0.0001]])).connect(out);
          n.start(0);
        },
      },
      // Keyboard typing: short bright clicks with a soft low "thock", irregular rhythm.
      keys: {
        dur: 1.1,
        build(ctx, out) {
          const r = rng(7);
          let t = 0.01;
          for (let i = 0; i < 9; i++) {
            const n = noiseSrc(ctx, 0.03, 100 + i);
            n.connect(filter(ctx, "bandpass", 2600 + r() * 1800, 1.4))
              .connect(gainEnv(ctx, [[t, 0.0001], [t + 0.001, 0.9], [t + 0.022, 0.0001]])).connect(out);
            n.start(t);
            const o = ctx.createOscillator();
            o.frequency.setValueAtTime(170 + r() * 40, t);
            o.connect(gainEnv(ctx, [[t, 0.0001], [t + 0.002, 0.35], [t + 0.03, 0.0001]])).connect(out);
            o.start(t);
            o.stop(t + 0.04);
            t += 0.07 + r() * 0.08;
          }
        },
      },
      // Data blips: quick, bright sine blips in a little melody.
      blips: {
        dur: 0.8,
        build(ctx, out) {
          [1318.5, 1760, 1174.7, 1568, 2093].forEach((f, i) => {
            const t = 0.01 + i * 0.085;
            const o = ctx.createOscillator();
            o.type = i % 2 ? "triangle" : "sine";
            o.frequency.setValueAtTime(f, t);
            o.connect(gainEnv(ctx, [[t, 0.0001], [t + 0.003, 0.8], [t + 0.06, 0.0001]])).connect(out);
            o.start(t);
            o.stop(t + 0.07);
          });
        },
      },
      // Confirm: a soft rising two-note success chime.
      confirm: {
        dur: 1.0,
        build(ctx, out) {
          [[1046.5, 0.01], [1568, 0.1]].forEach(([f, t]) => {
            [[1, 1], [2, 0.25], [3, 0.08]].forEach(([mult, amp]) => {
              const o = ctx.createOscillator();
              o.frequency.setValueAtTime(f * mult, t);
              o.connect(gainEnv(ctx, [[t, 0.0001], [t + 0.006, amp], [t + 0.75, 0.0001]])).connect(out);
              o.start(t);
              o.stop(t + 0.8);
            });
          });
        },
      },
      // Notification ding: bell-like partials, two notes.
      ding: {
        dur: 1.5,
        build(ctx, out) {
          [[1318.5, 0.01, 0.8], [1760, 0.14, 1]].forEach(([f, t, v]) => {
            [[1, 1], [2.76, 0.32], [5.4, 0.1]].forEach(([mult, amp]) => {
              const o = ctx.createOscillator();
              o.frequency.setValueAtTime(f * mult, t);
              o.connect(gainEnv(ctx, [[t, 0.0001], [t + 0.004, v * amp], [t + 1.2 / mult ** 0.5, 0.0001]])).connect(out);
              o.start(t);
              o.stop(t + 1.3);
            });
          });
        },
      },
    };

    function finish(buf) {
      let peak = 0;
      const chans = [];
      for (let c = 0; c < buf.numberOfChannels; c++) chans.push(buf.getChannelData(c));
      chans.forEach((d) => { for (let i = 0; i < d.length; i++) { const a = Math.abs(d[i]); if (a > peak) peak = a; } });
      const k = peak > 0 ? 0.89 / peak : 1;
      const fade = Math.floor(buf.sampleRate * 0.01);
      chans.forEach((d) => {
        for (let i = 0; i < d.length; i++) d[i] *= k;
        for (let i = 0; i < fade; i++) d[d.length - 1 - i] *= i / fade;
      });
      return buf;
    }

    function render(key) {
      if (cache.has(key)) return cache.get(key);
      const recipe = recipes[key];
      const job = (async () => {
        if (!recipe) throw new Error(`Unknown synth "${key}"`);
        if (!OAC) throw new Error("Web Audio not supported");
        const ctx = new OAC(2, Math.ceil(SR * recipe.dur), SR);
        recipe.build(ctx, ctx.destination);
        return finish(await ctx.startRendering());
      })();
      cache.set(key, job);
      return job;
    }

    function decode(url) {
      if (cache.has(url)) return cache.get(url);
      const job = (async () => {
        if (!OAC) throw new Error("Web Audio not supported");
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Could not load ${url}`);
        const data = await res.arrayBuffer();
        return new OAC(2, 1, SR).decodeAudioData(data);
      })();
      cache.set(url, job);
      return job;
    }

    function peaks(buf, count) {
      const chans = [];
      for (let c = 0; c < buf.numberOfChannels; c++) chans.push(buf.getChannelData(c));
      const step = Math.max(1, Math.floor(buf.length / count));
      const out = new Array(count).fill(0);
      for (let b = 0; b < count; b++) {
        let m = 0;
        const end = Math.min(buf.length, (b + 1) * step);
        for (let i = b * step; i < end; i += 3) {
          for (const d of chans) { const a = Math.abs(d[i]); if (a > m) m = a; }
        }
        out[b] = m;
      }
      const max = Math.max(...out) || 1;
      return out.map((v) => Math.max(0.06, Math.pow(v / max, 0.65)));
    }

    return { render, decode, peaks };
  })();

  /* ======================================================================
     Hero timeline demo
     ====================================================================== */
  function initReel() {
    const reel = $("#reel");
    if (!reel) return;
    const btn = $("[data-reel-play]", reel);
    const label = $("[data-reel-label]", reel);
    const icon = $("use", btn);
    const T = parseFloat(getComputedStyle(reel).getPropertyValue("--T")) || 7.2;
    const clips = $$("[data-sound]", reel).map((el) => ({
      el,
      key: el.dataset.sound,
      start: parseFloat(el.style.getPropertyValue("--s")) || 0,
      len: parseFloat(el.style.getPropertyValue("--l")) || 1,
    }));

    // Draw real waveforms into the timeline clips.
    const draw = () => clips.forEach((clip) => {
      Synth.render(clip.key).then((buf) => {
        const wave = $(".clip__wave", clip.el);
        if (!wave) return;
        const count = Math.max(8, Math.round((clip.len / T) * 90));
        wave.innerHTML = Synth.peaks(buf, count).map((h) => `<i style="height:${Math.round(h * 100)}%"></i>`).join("");
      }).catch(() => {});
    });
    if ("requestIdleCallback" in window) requestIdleCallback(draw, { timeout: 1200 }); else setTimeout(draw, 300);

    const setUI = (playing) => {
      reel.classList.toggle("is-playing", playing);
      btn.setAttribute("aria-pressed", String(playing));
      if (label) label.textContent = playing ? "Stop" : "Play the edit";
      if (icon) icon.setAttribute("href", playing ? "#i-pause" : "#i-play");
      if (!playing) {
        reel.style.setProperty("--p", "0");
        clips.forEach((c) => c.el.classList.remove("is-hit"));
      }
    };

    btn.addEventListener("click", async () => {
      if (reel.classList.contains("is-playing")) { Player.stopAll(); return; }
      if (!Player.audio()) return;
      track("play_the_edit");
      setUI(true);
      let buffers;
      try { buffers = await Promise.all(clips.map((c) => Synth.render(c.key))); } catch { setUI(false); return; }
      if (!reel.classList.contains("is-playing")) return;
      const session = Player.play(clips.map((c, i) => ({ buffer: buffers[i], at: c.start })), () => setUI(false));
      if (!session) { setUI(false); return; }

      const tick = () => {
        if (!Player.isCurrent(session)) return;
        const t = Math.max(0, Player.elapsed(session));
        reel.style.setProperty("--p", String(clamp01(t / T)));
        clips.forEach((c) => c.el.classList.toggle("is-hit", t >= c.start && t <= c.start + c.len * 0.85));
        if (t >= T) { Player.stopAll(); return; }
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }

  /* ======================================================================
     App icon equaliser: the icon's bars follow whatever sound is playing
     ====================================================================== */
  function initEqualiser() {
    const icons = $$("[data-eq]");
    if (!icons.length || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const bars = icons.map((icon) => $$(".eq rect", icon));
    const EDGES = [1, 3, 8, 20, 45, 100];  // ~170 Hz per bin: bass … air
    const ORDER = [3, 1, 0, 2, 4];         // loudest band (bass) in the middle bar
    let raf = 0;

    const frame = () => {
      const lv = Player.levels(EDGES);
      if (lv) {
        bars.forEach((set) => set.forEach((bar, i) => {
          const v = 0.42 + 0.58 * Math.min(1, lv[ORDER[i]] * 1.4);
          bar.style.setProperty("--lv", v.toFixed(3));
        }));
      }
      raf = requestAnimationFrame(frame);
    };

    Player.subscribe((playing) => {
      cancelAnimationFrame(raf);
      icons.forEach((icon) => icon.classList.toggle("is-live", playing));
      if (playing) raf = requestAnimationFrame(frame);
      else bars.forEach((set) => set.forEach((bar) => bar.style.removeProperty("--lv")));
    });
  }

  /* ======================================================================
     Logo marquee: fill each row wider than the screen, then loop it
     ====================================================================== */
  function initMarquee() {
    // Mask each logo's gloss to the logo's own shape (absolute URL, so it works from the stylesheet).
    $$(".logo-chip__icon").forEach((icon) => {
      const img = $("img", icon);
      if (img && img.src) icon.style.setProperty("--logo", `url("${img.src}")`);
    });

    $$("[data-marquee] .marquee__row").forEach((row) => {
      const set = $(".marquee__set", row);
      if (!set || !set.children.length) return;
      const originals = Array.from(set.children);
      row.classList.add("is-running");

      // Repeat the logos until one set is wider than the largest marquee (1240px).
      let guard = 0;
      while (set.getBoundingClientRect().width < 1400 && guard++ < 12) {
        originals.forEach((li) => {
          const copy = li.cloneNode(true);
          copy.setAttribute("aria-hidden", "true");
          copy.dataset.clone = "";
          set.appendChild(copy);
        });
      }

      // A second identical set makes the -50% loop seamless.
      const twin = set.cloneNode(true);
      twin.setAttribute("aria-hidden", "true");
      twin.dataset.clone = "";
      row.appendChild(twin);

      const speed = 34; // px per second: slow and calm
      row.style.setProperty("--dur", `${Math.round(set.getBoundingClientRect().width / speed)}s`);
    });
  }

  /* ======================================================================
     Buy flow
     ====================================================================== */
  function initBuy() {
    const sheet = $("#buy-sheet");
    const urls = C.checkoutUrl || {};

    // Test mode: let the owner walk through "buy → download" before payments are live.
    if (C.testMode) $$("[data-test-buy]").forEach((el) => { el.hidden = false; });

    const open = () => {
      if (!sheet) return;
      if (typeof sheet.showModal === "function") sheet.showModal(); else sheet.setAttribute("open", "");
    };
    const close = () => {
      if (!sheet) return;
      if (typeof sheet.close === "function") sheet.close(); else sheet.removeAttribute("open");
    };

    document.addEventListener("click", (e) => {
      const buy = e.target.closest("[data-buy]");
      if (buy) {
        e.preventDefault();
        const url = urls[Pricing.currency] || urls.INR || urls.USD;
        const where = [["#nav", "menu"], [".hero", "hero"], [".price-card", "price_card"], [".cta-card", "final_cta"],
          ["[data-buybar]", "phone_bar"], ["#buy-sheet", "sheet"]].find(([sel]) => buy.closest(sel));
        track("buy_click", { buy_button: where ? where[1] : "other", currency: Pricing.currency });
        // A short pause lets analytics send the click before the checkout page loads.
        if (url) setTimeout(() => { window.location.href = url; }, 150); else open();
        return;
      }
      if (e.target.closest("[data-sheet-close]")) close();
    });
    if (sheet) sheet.addEventListener("click", (e) => { if (e.target === sheet) close(); });

    // Contact links (footer + sheet) — only rendered when configured.
    const contact = C.contact || {};
    const links = [];
    if (contact.email) links.push({ href: `mailto:${contact.email}`, text: "Email", icon: "i-mail" });
    if (contact.whatsapp) links.push({ href: contact.whatsapp, text: "WhatsApp", icon: "i-chat" });
    if (contact.instagram) links.push({ href: contact.instagram, text: "Instagram", icon: "i-camera" });
    if (links.length) {
      const html = (withIcon) => links.map((l) => {
        const ext = l.href.startsWith("http") ? ' target="_blank" rel="noopener"' : "";
        const ico = withIcon ? `<svg class="ico" aria-hidden="true"><use href="#${l.icon}"/></svg>` : "";
        return `<a href="${escapeHTML(l.href)}"${ext}>${ico}${l.text}</a>`;
      }).join("");
      $$("[data-contact-links]").forEach((el) => { el.innerHTML = html(false); });
      $$("[data-sheet-contact]").forEach((el) => { el.innerHTML = html(true); el.hidden = false; });
    }
  }

  /* ======================================================================
     Chrome: nav, buy bar, reveal, year
     ====================================================================== */
  function initChrome() {
    const nav = $("#nav");
    if (nav) {
      const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 4);
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }

    $$("[data-year]").forEach((el) => { el.textContent = String(new Date().getFullYear()); });

    // Mobile buy bar: shown while no other Buy button is on screen.
    const bar = $("[data-buybar]");
    const watched = $$("[data-cta-watch]");
    if (bar && watched.length && "IntersectionObserver" in window) {
      const onScreen = new Set();
      let scrolled = false;
      const update = () => {
        const show = scrolled && onScreen.size === 0;
        bar.classList.toggle("is-visible", show);
        bar.setAttribute("aria-hidden", String(!show));
        bar.inert = !show;
      };
      const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => { if (e.isIntersecting) onScreen.add(e.target); else onScreen.delete(e.target); });
        update();
      });
      watched.forEach((el) => io.observe(el));
      window.addEventListener("scroll", () => {
        const s = window.scrollY > 300;
        if (s !== scrolled) { scrolled = s; update(); }
      }, { passive: true });
    }
  }

  /* ====================================================================== */
  Pricing.init();
  initChrome();
  initReel();
  initEqualiser();
  initMarquee();
  initBuy();
})();
