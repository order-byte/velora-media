import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { CLIPS, FPS, C, inter, serif } from "./lib";

/**
 * Stacked "hierarchy" captions (Iman-style): small lead words above, one big keyword, small tail below.
 * Each word blurs + fades in on its spoken time; the keyword lands with a soft scale-down and, for
 * "bar" styles, a highlight bar sweeps behind it.
 */
export type KeyStyle = "white" | "bar" | "green" | "red" | "serif";
type Ref = [string, number]; // clip id, word index
export type Group = { lead: Ref[]; key: Ref[]; tail: Ref[]; style: KeyStyle; keyText?: string };

const R = (clip: string, ...idx: number[]): Ref[] => idx.map((i) => [clip, i] as Ref);
const word = ([c, i]: Ref) => CLIPS.find((x) => x.id === c)!.words[i];
const clean = (w: string) => w.replace(/[,.…—]+$/g, "").replace(/^'|'$/g, "");

export const GROUPS: Group[] = [
  { lead: R("hook_a", 0), key: R("hook_a", 1, 2), tail: [], style: "bar" },
  { lead: [], key: R("hook_a", 3), tail: [], style: "green" },
  { lead: R("hook_b", 0, 1, 2, 3), key: R("hook_b", 4), tail: [], style: "serif" },
  { lead: R("pain_1", 0, 1, 2), key: R("pain_1", 3, 4), tail: [], style: "white" },
  { lead: R("pain_2", 0, 1, 2), key: R("pain_2", 3, 4), tail: R("pain_2", 5, 6, 7), style: "red" },
  { lead: R("pain_3", 0), key: R("pain_3", 1, 2), tail: R("pain_3", 3, 4, 5), style: "red", keyText: "post nahi" },
  { lead: R("pain_4", 0, 1), key: R("pain_4", 2), tail: R("pain_4", 3, 4, 5), style: "red" },
  { lead: R("pain_4", 6), key: R("pain_4", 7), tail: R("pain_4", 8, 9, 10, 11), style: "red" },
  { lead: R("offer_1", 0), key: R("offer_1", 1, 2, 3), tail: R("offer_1", 4, 5), style: "bar" },
  { lead: [], key: R("offer_1", 6, 7, 8), tail: [], style: "white" },
  { lead: R("offer_2", 0, 1), key: R("offer_2", 2, 3), tail: [], style: "white" },
  { lead: R("offer_3", 0, 1), key: R("offer_3", 2, 3), tail: [], style: "bar" },
  { lead: R("style_q", 0), key: R("style_q", 1), tail: [], style: "serif" },
  { lead: R("style_trend", 0, 1), key: R("style_trend", 2), tail: R("style_trend", 3, 4, 5), style: "bar" },
  { lead: [], key: R("style_sab", 0), tail: [], style: "white" },
  { lead: R("content", 0), key: R("content", 1), tail: [], style: "white" },
  { lead: R("content", 2), key: R("content", 3), tail: [], style: "serif" },
  { lead: R("scroll", 0, 1, 2), key: R("scroll", 3, 4), tail: R("scroll", 5, 6, 7), style: "green", keyText: "scroll stop" },
  { lead: R("reel", 0, 1, 2, 3), key: R("reel", 4, 5), tail: R("reel", 6, 7, 8), style: "white", keyText: "alag pay" },
  { lead: R("reel", 9), key: R("reel", 10), tail: R("reel", 11, 12), style: "red" },
  { lead: R("price", 0, 1, 2), key: R("price", 3), tail: [], style: "serif" },
  { lead: R("proof_b", 0), key: R("proof_b", 1, 2), tail: R("proof_b", 3, 4), style: "green" },
  { lead: [], key: R("proof_b", 5, 6), tail: R("proof_b", 7, 8, 9, 10, 11), style: "bar" },
  { lead: R("slots", 0, 1), key: R("slots", 2, 3), tail: R("slots", 4, 5), style: "bar" },
  { lead: R("fcfs", 0, 1), key: R("fcfs", 2, 3), tail: [], style: "white" },
  { lead: R("cta_1", 0, 1), key: R("cta_1", 2), tail: [], style: "green", keyText: "“EDIT”" },
  { lead: R("cta_2", 0, 1, 2), key: R("cta_2", 3, 4), tail: R("cta_2", 5, 6), style: "bar" },
  { lead: R("cta_3", 0, 1), key: R("cta_3", 2), tail: R("cta_3", 3, 4, 5), style: "bar" },
  { lead: R("cta_3", 6, 7), key: R("cta_3", 8, 9), tail: R("cta_3", 10), style: "green" },
  { lead: R("kicker", 0, 1, 2, 3, 4), key: R("kicker", 5, 6), tail: R("kicker", 7, 8, 9), style: "bar" },
];

export type Timed = Group & { s: number; e: number; keyS: number };
const t0 = (refs: Ref[]) => (refs.length ? word(refs[0]).s : Infinity);
export const TIMED: Timed[] = GROUPS.map((g) => {
  const all = [...g.lead, ...g.key, ...g.tail];
  return { ...g, s: Math.min(...all.map((r) => word(r).s)), e: Math.max(...all.map((r) => word(r).e)), keyS: t0(g.key) };
}).map((g, i, arr) => ({ ...g, e: arr[i + 1] ? Math.min(arr[i + 1].s - 0.02, g.e + 0.45) : g.e + 0.45 }));

/** keyword reveal times, used to place a soft swish under each one */
export const KEY_TIMES = TIMED.map((g) => ({ t: g.keyS, style: g.style }));

const reveal = (t: number, at: number, dur = 0.22) =>
  interpolate(t, [at - 0.03, at - 0.03 + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });

const Small: React.FC<{ refs: Ref[]; t: number; size?: number }> = ({ refs, t, size = 50 }) => (
  <div style={{ display: "flex", justifyContent: "center", flexWrap: "wrap", gap: "0 14px", minHeight: refs.length ? undefined : 0 }}>
    {refs.map((r, i) => {
      const w = word(r); const a = reveal(t, w.s);
      return <span key={i} style={{ fontFamily: inter, fontWeight: 700, fontSize: size, letterSpacing: "-0.02em", color: "rgba(255,255,255,0.94)", opacity: a, filter: `blur(${(1 - a) * 10}px)`, transform: `translateY(${(1 - a) * 18}px)`, display: "inline-block", textShadow: "0 3px 18px rgba(0,0,0,0.55)" }}>{clean(w.w)}</span>;
    })}
  </div>
);

export const Captions2: React.FC<{ hide: [number, number][]; y?: { from: number; to: number; y: number }[]; offset?: number }> = ({ hide, y = [], offset = 0 }) => {
  const frame = useCurrentFrame();
  const t = (frame + offset) / FPS;
  if (hide.some(([a, b]) => t >= a && t < b)) return null;
  const g = TIMED.find((x) => t >= x.s - 0.04 && t < x.e);
  if (!g) return null;
  const top = (y.find((r) => t >= r.from && t < r.to) || { y: 1060 }).y;
  const out = interpolate(t, [g.e - 0.12, g.e], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const k = reveal(t, g.keyS, 0.28);
  const txt = g.keyText ?? g.key.map((r) => clean(word(r).w)).join(" ");
  const isSerif = g.style === "serif";
  const upper = g.style !== "serif";
  const display = upper ? txt.toUpperCase() : txt;
  const base = isSerif ? 190 : 150;
  const size = Math.min(base, (isSerif ? 1500 : 1180) / Math.max(4, display.length));
  const color = g.style === "green" ? C.green : g.style === "red" ? C.red : g.style === "bar" ? "#FFE14D" : "#fff";
  const bar = interpolate(t, [g.keyS + 0.05, g.keyS + 0.3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.65, 0, 0.35, 1) });
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top, display: "flex", flexDirection: "column", alignItems: "center", opacity: out, filter: `blur(${(1 - out) * 8}px)` }}>
      <Small refs={g.lead} t={t} />
      <div style={{ position: "relative", marginTop: g.lead.length ? -2 : 0, opacity: k, transform: `scale(${1.22 - 0.22 * k})`, filter: `blur(${(1 - k) * 16}px)` }}>
        {g.style === "bar" && <div style={{ position: "absolute", left: -22, right: -22, top: "18%", bottom: "8%", background: C.purpleDeep, borderRadius: 14, transformOrigin: "left center", transform: `scaleX(${bar}) skewX(-6deg)`, boxShadow: "0 12px 40px rgba(124,58,237,0.5)" }} />}
        <span style={{
          position: "relative", display: "inline-block", fontFamily: isSerif ? serif : inter, fontStyle: isSerif ? "italic" : "normal",
          fontWeight: isSerif ? 400 : 900, fontSize: size, lineHeight: 1.02, letterSpacing: isSerif ? "-0.01em" : "-0.04em", color, whiteSpace: "nowrap",
          textShadow: g.style === "green" ? "0 0 30px rgba(61,255,143,0.55), 0 0 80px rgba(61,255,143,0.3)" : g.style === "red" ? "0 0 30px rgba(255,77,77,0.45), 0 6px 26px rgba(0,0,0,0.5)" : "0 6px 30px rgba(0,0,0,0.5)",
        }}>{display}</span>
      </div>
      <Small refs={g.tail} t={t} size={44} />
    </div>
  );
};
