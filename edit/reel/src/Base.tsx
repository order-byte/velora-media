import React from "react";
import { OffthreadVideo, staticFile, useCurrentFrame, interpolate, Easing } from "remotion";
import { SUBS, FPS, C, inter, serif, CLIPS, norm } from "./lib";

/** Face sits at ~(420,760) in source pixels; zoom around it and lift it to the upper third. */
const ORIGIN = "420px 760px";
const ZOOMS = [1.24, 1.38];

/** Extra emphasis punches (seconds) -> quick zoom bump */
export const PUNCHES: number[] = [];

export const zoomAt = (t: number) => {
  const i = Math.max(0, SUBS.findIndex((s) => t >= s.oStart && t < s.oEnd));
  const sb = SUBS[i] || SUBS[SUBS.length - 1];
  const base = ZOOMS[i % 2];
  const k = (t - sb.oStart) / Math.max(0.1, sb.oEnd - sb.oStart);
  const push = 0.025 * k; // slow push-in through each cut
  // short settle at each cut: start 4% tighter, ease back in 5 frames
  const settle = interpolate(t - sb.oStart, [0, 5 / FPS], [0.04, 0], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  let bump = 0;
  for (const p of PUNCHES) {
    const d = t - p;
    if (d >= 0 && d < 0.5) bump = Math.max(bump, interpolate(d, [0, 0.08, 0.5], [0, 0.07, 0.0], { easing: Easing.out(Easing.quad) }));
  }
  return base + push + settle + bump;
};

export const Talking: React.FC<{ raw?: boolean; muted?: boolean; offset?: number }> = ({ raw, muted, offset = 0 }) => {
  const frame = useCurrentFrame();
  const t = (frame + offset) / FPS;
  const z = raw ? 1 : zoomAt(t);
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#000" }}>
      <OffthreadVideo
        src={staticFile(raw ? "base_raw.mp4" : "base.mp4")}
        muted={muted}
        startFrom={offset}
        style={{ position: "absolute", width: 1080, height: 1920, transformOrigin: ORIGIN, transform: raw ? "none" : `translateY(-90px) scale(${z})` }}
      />
    </div>
  );
};

/* ------------------------------ captions ------------------------------ */
type Emph = "purple" | "green" | "red" | "serif";
export const EMPH: Record<string, Record<string, Emph>> = {
  hook_a: { "20": "green", creators: "purple", $200: "green" },
  hook_b: { editing: "serif" },
  pain_1: { shoot: "purple", "10": "green", minute: "green" },
  pain_2: { edit: "purple", poori: "red", raat: "red" },
  pain_3: { consistently: "purple", nahi: "red" },
  pain_4: { growth: "purple", slow: "red", burnout: "red", full: "red" },
  offer_1: { aminur: "purple", rex: "purple", team: "purple", monthly: "green", editing: "green", package: "green" },
  offer_2: { shoot: "purple" },
  offer_3: { humara: "purple", kaam: "purple" },
  style_q: { style: "serif" },
  style_trend: { trend: "purple" },
  content: { content: "purple", style: "serif" },
  scroll: { scroll: "green", stop: "green" },
  reel: { reel: "purple", khatam: "red" },
  price: { editing: "purple", $200: "green" },
  proof_b: { "10": "green", creators: "purple", monthly: "purple", package: "purple" },
  slots: { "20": "green", slots: "green" },
  fcfs: { first: "purple", serve: "purple" },
  cta_1: { comment: "purple", edit: "green" },
  cta_2: { dm: "purple", information: "purple" },
  cta_3: { bio: "purple", contact: "green", number: "green" },
  kicker: { humne: "purple", edit: "green" },
};

type Chunk = { clip: string; words: { w: string; s: number; e: number }[]; s: number; e: number };
const buildChunks = (): Chunk[] => {
  const out: Chunk[] = [];
  for (const c of CLIPS) {
    let cur: Chunk | null = null;
    c.words.forEach((w, i) => {
      if (!cur) cur = { clip: c.id, words: [], s: w.s, e: w.e };
      cur.words.push(w); cur.e = w.e;
      const brk = /[,.?!…]$/.test(w.w) || cur.words.length >= 3 || i === c.words.length - 1;
      if (brk) { out.push(cur); cur = null; }
    });
  }
  // each chunk stays until the next one starts (max +0.35s after its last word)
  for (let i = 0; i < out.length; i++) {
    const nx = out[i + 1];
    out[i].e = nx ? Math.min(nx.s, out[i].e + 0.35) : out[i].e + 0.35;
  }
  return out;
};
const CHUNKS = buildChunks();

const color = (e: Emph | undefined, dark: boolean) =>
  e === "purple" ? C.purple : e === "green" ? (dark ? "#14a85a" : C.green) : e === "red" ? C.red : dark ? C.ink : "#fff";

/** Captions — hidden inside `hide` windows (seconds). `dark` = ink text for paper scenes. */
export const Captions: React.FC<{ hide: [number, number][]; darkIn?: [number, number][]; yIn?: { from: number; to: number; y: number }[]; offset?: number }> = ({ hide, darkIn = [], yIn = [], offset = 0 }) => {
  const frame = useCurrentFrame();
  const t = (frame + offset) / FPS;
  if (hide.some(([a, b]) => t >= a && t < b)) return null;
  const ch = CHUNKS.find((c) => t >= c.s - 0.04 && t < c.e);
  if (!ch) return null;
  const dark = darkIn.some(([a, b]) => t >= a && t < b);
  const y = (yIn.find((r) => t >= r.from && t < r.to) || { y: 1235 }).y;
  const em = EMPH[ch.clip] || {};
  return (
    <div style={{ position: "absolute", left: 70, right: 70, top: y, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 18px" }}>
      {ch.words.map((w, i) => {
        const k = norm(w.w);
        const e = em[k];
        const local = t - w.s;
        const pop = interpolate(local, [-0.04, 0.09], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(2)) });
        const spoken = local >= -0.04;
        const isSerif = e === "serif";
        const txt = w.w.replace(/[,.]$/, "").replace(/^'|'$/g, "");
        return (
          <span key={i} style={{
            fontFamily: isSerif ? serif : inter, fontStyle: isSerif ? "italic" : "normal",
            fontWeight: isSerif ? 400 : 800, fontSize: isSerif ? 92 : 70, lineHeight: 1.12, letterSpacing: isSerif ? "0" : "-0.02em",
            color: color(e, dark), opacity: spoken ? 1 : 0.0,
            transform: `scale(${0.7 + 0.3 * pop}) translateY(${(1 - pop) * 14}px)`, display: "inline-block",
            textShadow: dark ? "none" : e === "green" ? `0 0 28px rgba(61,255,143,0.55), 0 4px 18px rgba(0,0,0,0.6)` : "0 4px 22px rgba(0,0,0,0.55), 0 2px 4px rgba(0,0,0,0.5)",
          }}>{txt}</span>
        );
      })}
    </div>
  );
};
