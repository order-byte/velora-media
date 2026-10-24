import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";
import { C, inter, mono } from "./lib";

export const EXPO = Easing.bezier(0.16, 1, 0.3, 1);
export const INOUT = Easing.bezier(0.65, 0, 0.35, 1);
export const k = (f: number, a: number, b: number, e = EXPO) => interpolate(f, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: e });

/** Scene wrapper: zoom-blur in, optional zoom-blur out (frames relative to the sequence) */
export const ZoomIn: React.FC<{ dur: number; children: React.ReactNode; out?: boolean; from?: number; bg?: string }> = ({ dur, children, out = true, from = 1.14, bg }) => {
  const f = useCurrentFrame();
  const a = k(f, 0, 9);
  const z = out ? k(f, dur - 7, dur, Easing.in(Easing.cubic)) : 0;
  const scale = from - (from - 1) * a + z * 0.18;
  const blur = (1 - a) * 22 + z * 18;
  return (
    <AbsoluteFill style={{ opacity: Math.min(1, a * 1.6) * (1 - z * 0.9), transform: `scale(${scale})`, filter: blur > 0.3 ? `blur(${blur}px)` : undefined, background: bg }}>
      {children}
    </AbsoluteFill>
  );
};

/** Expanding light ring + white bloom (ref: ring-burst transition) */
export const LightRing: React.FC<{ color?: string }> = ({ color = "#fff" }) => {
  const f = useCurrentFrame();
  const p = k(f, 0, 14);
  const bloom = interpolate(f, [4, 8, 16], [0, 0.9, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const r = 80 + p * 1400;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", left: 540 - r, top: 960 - r, width: 2 * r, height: 2 * r, borderRadius: "50%",
        border: `${Math.max(2, 40 * (1 - p))}px solid ${color}`, opacity: 1 - p, filter: "blur(6px)", boxShadow: `0 0 80px ${color}, inset 0 0 80px ${color}` }} />
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 50%, #fff 0%, rgba(255,255,255,0.6) 35%, rgba(255,255,255,0) 70%)", opacity: bloom }} />
    </AbsoluteFill>
  );
};

/** Two-frame colour inversion + RGB split, used as a glitch cut */
export const InvertFlash: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const f = useCurrentFrame();
  const on = f < 3;
  return (
    <AbsoluteFill style={{ filter: on ? "invert(1) hue-rotate(180deg) saturate(2)" : undefined, transform: on ? `translateX(${f % 2 ? 18 : -18}px)` : undefined }}>
      {children}
    </AbsoluteFill>
  );
};

/** Light leak sweeping across the frame */
export const LightLeak: React.FC<{ dur?: number; color?: string }> = ({ dur = 18, color = "255,190,120" }) => {
  const f = useCurrentFrame();
  const p = k(f, 0, dur, INOUT);
  const o = interpolate(f, [0, dur * 0.3, dur], [0, 0.55, 0], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", opacity: o, background: `radial-gradient(60% 40% at ${-20 + 140 * p}% ${30 + 20 * p}%, rgba(${color},0.9) 0%, rgba(${color},0) 70%)` }} />;
};

/** Frosted glass panel */
export const Glass: React.FC<{ x: number; y: number; w: number; h?: number; delay?: number; children: React.ReactNode; r?: number; pad?: number; dark?: boolean }> = ({ x, y, w, h, delay = 0, children, r = 40, pad = 34, dark }) => {
  const f = useCurrentFrame();
  const a = k(f, delay, delay + 12);
  return (
    <div style={{
      position: "absolute", left: x, top: y, width: w, height: h, borderRadius: r, padding: pad,
      background: dark ? "rgba(14,12,20,0.55)" : "rgba(255,255,255,0.14)", backdropFilter: "blur(26px) saturate(1.4)",
      border: "1.5px solid rgba(255,255,255,0.32)", boxShadow: "0 30px 80px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.35)",
      opacity: a, transform: `translateY(${(1 - a) * 40}px) scale(${0.94 + 0.06 * a})`, filter: a < 0.98 ? `blur(${(1 - a) * 14}px)` : undefined,
    }}>{children}</div>
  );
};

export const Cream: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: "radial-gradient(110% 70% at 50% 35%, #F6F1EA 0%, #EDE5DA 60%, #E2D8CB 100%)" }}>{children}</AbsoluteFill>
);
export const Navy: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: "radial-gradient(90% 60% at 50% 40%, #12164a 0%, #070a24 55%, #03040f 100%)" }}>{children}</AbsoluteFill>
);

/** Glowing neon app-style tile with a 3D flip-in */
export const NeonTile: React.FC<{ label: string; sub: string; color: string; delay: number; size?: number; children?: React.ReactNode }> = ({ label, sub, color, delay, size = 230, children }) => {
  const f = useCurrentFrame();
  const a = k(f, delay, delay + 14);
  return (
    <div style={{ width: size, textAlign: "center", opacity: a, transform: `perspective(900px) rotateY(${(1 - a) * -70}deg) translateY(${(1 - a) * 80}px)`, filter: a < 0.98 ? `blur(${(1 - a) * 12}px)` : undefined }}>
      <div style={{ width: size, height: size, borderRadius: size * 0.24, background: `linear-gradient(150deg, ${color}, ${color}cc)`, display: "flex", alignItems: "center", justifyContent: "center",
        boxShadow: `0 0 40px ${color}aa, 0 0 110px ${color}55, inset 0 6px 18px rgba(255,255,255,0.55), inset 0 -10px 24px rgba(0,0,0,0.25)`,
        fontFamily: inter, fontWeight: 900, fontSize: size * 0.36, color: "#fff", letterSpacing: "-0.04em", textShadow: "0 2px 10px rgba(0,0,0,0.25)" }}>{children ?? label}</div>
      <div style={{ marginTop: 18, fontFamily: inter, fontWeight: 700, fontSize: 34, color: "#fff", opacity: 0.92 }}>{sub}</div>
    </div>
  );
};

/** Typed line with a caret */
export const Typed: React.FC<{ text: string; start: number; cps?: number; style?: React.CSSProperties }> = ({ text, start, cps = 1.4, style }) => {
  const f = useCurrentFrame();
  const n = Math.max(0, Math.min(text.length, Math.floor((f - start) * cps)));
  return <span style={style}>{text.slice(0, n)}<span style={{ opacity: n < text.length && f % 10 < 6 ? 1 : 0 }}>|</span></span>;
};

/** Vertical camera pan with directional motion blur (frames relative) */
export const PanUp: React.FC<{ at: number; dist?: number; children: React.ReactNode }> = ({ at, dist = 1400, children }) => {
  const f = useCurrentFrame();
  const p = k(f, at, at + 9, Easing.in(Easing.cubic));
  const v = p > 0 && p < 1 ? 24 : 0;
  return (
    <AbsoluteFill style={{ transform: `translateY(${-p * dist}px)`, filter: v ? "url(#vblur)" : undefined, opacity: 1 - p * 0.3 }}>
      <svg width="0" height="0" style={{ position: "absolute" }}><filter id="vblur"><feGaussianBlur stdDeviation={`0 ${v}`} /></filter></svg>
      {children}
    </AbsoluteFill>
  );
};

export const Label: React.FC<{ text: string; color?: string; delay?: number }> = ({ text, color = C.purple, delay = 0 }) => {
  const f = useCurrentFrame();
  const a = k(f, delay, delay + 10);
  return (
    <div style={{ position: "absolute", top: 230, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: a, transform: `translateY(${(1 - a) * -30}px)`, filter: a < 0.98 ? `blur(${(1 - a) * 10}px)` : undefined }}>
      <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 32, letterSpacing: "0.16em", color: "#fff", padding: "14px 26px", borderRadius: 999, background: "rgba(10,10,20,0.55)", border: `2px solid ${color}`, boxShadow: `0 0 30px ${color}66`, backdropFilter: "blur(14px)" }}>{text}</div>
    </div>
  );
};
