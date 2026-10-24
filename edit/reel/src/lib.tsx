import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";
import FONTS from "./fonts.json";
import T from "./timeline.json";

// fonts ship with the project (public/fonts) so rendering needs no network
for (const ft of FONTS) loadFont({ family: ft.family, url: staticFile(ft.file), weight: ft.weight, style: ft.style as "normal" | "italic" });
export const inter = "Inter";
export const serif = "Instrument Serif";
export const mono = "JetBrains Mono";

export const FPS = 30;
export const DURATION = Math.ceil(T.duration * FPS);
export type Word = { w: string; s: number; e: number };
export type Clip = { id: string; text: string; oStart: number; oEnd: number; words: Word[] };
export const CLIPS = T.clips as Clip[];
export const SUBS = T.subclips as { clip: string; oStart: number; oEnd: number }[];

export const clip = (id: string) => CLIPS.find((c) => c.id === id)!;
export const S = (id: string) => clip(id).oStart;
export const E = (id: string) => clip(id).oEnd;
export const fr = (sec: number) => Math.round(sec * FPS);
/** start time of the n-th word in a clip whose text begins with `w` */
export const W = (id: string, w: string, n = 0) => {
  const hits = clip(id).words.filter((x) => norm(x.w).startsWith(w.toLowerCase()));
  return (hits[n] || hits[0] || clip(id).words[0]).s;
};
export const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9$]/g, "");

export const C = {
  purple: "#A855F7",
  purpleDeep: "#7C3AED",
  green: "#3DFF8F",
  red: "#FF4D4D",
  paper: "#F3F1EC",
  ink: "#121014",
  white: "#FFFFFF",
  amber: "#FFB938",
};

export const useSpring = (delayFrames = 0, config: any = { damping: 14, stiffness: 160, mass: 0.7 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delayFrames, fps, config });
};
export const ease = (frame: number, a: number, b: number, from = 0, to = 1, e = Easing.bezier(0.22, 1, 0.36, 1)) =>
  interpolate(frame, [a, b], [from, to], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: e });

export const Fill: React.FC<{ style?: React.CSSProperties; children?: React.ReactNode }> = ({ style, children }) => (
  <div style={{ position: "absolute", inset: 0, ...style }}>{children}</div>
);

/** iOS-like pill */
export const Pill: React.FC<{ delay?: number; children: React.ReactNode; bg?: string; color?: string; style?: React.CSSProperties; size?: number }> = ({
  delay = 0, children, bg = "rgba(20,18,24,0.82)", color = "#fff", style, size = 40,
}) => {
  const s = useSpring(delay);
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: size * 0.35, padding: `${size * 0.38}px ${size * 0.62}px`, borderRadius: 999,
      background: bg, color, fontFamily: inter, fontWeight: 700, fontSize: size, letterSpacing: "-0.01em",
      boxShadow: "0 18px 50px rgba(0,0,0,0.28), inset 0 0 0 1.5px rgba(255,255,255,0.12)", backdropFilter: "blur(18px)",
      transform: `scale(${0.6 + 0.4 * s}) translateY(${(1 - s) * 30}px)`, opacity: Math.min(1, s * 1.4), ...style,
    }}>{children}</div>
  );
};

/** Section label like "01 · TALKING HEAD" */
export const StyleTag: React.FC<{ n: string; label: string; light?: boolean }> = ({ n, label, light }) => {
  const s = useSpring(0);
  return (
    <div style={{ position: "absolute", top: 210, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
      <div style={{
        fontFamily: mono, fontWeight: 700, fontSize: 34, letterSpacing: "0.12em", color: light ? C.ink : "#fff",
        background: light ? "rgba(255,255,255,0.9)" : "rgba(10,8,12,0.65)", padding: "16px 28px", borderRadius: 14,
        boxShadow: "0 12px 40px rgba(0,0,0,0.3)", transform: `translateY(${(1 - s) * -40}px)`, opacity: s,
      }}>
        <span style={{ color: C.purple }}>{n}</span>&nbsp;·&nbsp;{label}
      </div>
    </div>
  );
};

/* ---------- icons (inline SVG, stroke-based) ---------- */
type IP = { size?: number; color?: string; stroke?: number };
const Svg: React.FC<IP & { children: React.ReactNode }> = ({ size = 48, color = "currentColor", stroke = 2.4, children }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">{children}</svg>
);
export const ICam = (p: IP) => <Svg {...p}><path d="M23 7l-7 5 7 5V7z" /><rect x="1" y="5" width="15" height="14" rx="2" /></Svg>;
export const IScissors = (p: IP) => <Svg {...p}><circle cx="6" cy="6" r="3" /><circle cx="6" cy="18" r="3" /><path d="M20 4L8.12 15.88M14.47 14.48L20 20M8.12 8.12L12 12" /></Svg>;
export const IClock = (p: IP) => <Svg {...p}><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></Svg>;
export const IMoon = (p: IP) => <Svg {...p}><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" /></Svg>;
export const ICheck = (p: IP) => <Svg {...p}><path d="M20 6L9 17l-5-5" /></Svg>;
export const IX = (p: IP) => <Svg {...p}><path d="M18 6L6 18M6 6l12 12" /></Svg>;
export const ITrend = (p: IP) => <Svg {...p}><path d="M23 6l-9.5 9.5-5-5L1 18" /><path d="M17 6h6v6" /></Svg>;
export const IDown = (p: IP) => <Svg {...p}><path d="M23 18l-9.5-9.5-5 5L1 6" /><path d="M17 18h6v-6" /></Svg>;
export const ISend = (p: IP) => <Svg {...p}><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" /></Svg>;
export const IHeart = (p: IP) => <Svg {...p}><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 000-7.78z" /></Svg>;
export const IMsg = (p: IP) => <Svg {...p}><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" /></Svg>;
export const IPhone = (p: IP) => <Svg {...p}><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.13.96.36 1.9.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0122 16.92z" /></Svg>;
export const IMail = (p: IP) => <Svg {...p}><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><path d="M22 6l-10 7L2 6" /></Svg>;
export const IUser = (p: IP) => <Svg {...p}><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" /></Svg>;
export const IBolt = (p: IP) => <Svg {...p}><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" /></Svg>;
export const IMic = (p: IP) => <Svg {...p}><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" /><path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8" /></Svg>;
export const IFilm = (p: IP) => <Svg {...p}><rect x="2" y="2" width="20" height="20" rx="2.18" /><path d="M7 2v20M17 2v20M2 12h20M2 7h5M2 17h5M17 17h5M17 7h5" /></Svg>;
export const IPin = (p: IP) => <Svg {...p}><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" /><circle cx="12" cy="10" r="3" /></Svg>;
export const IFlame = (p: IP) => <Svg {...p}><path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 002.5 2.5z" /></Svg>;
export const IBattery = (p: IP) => <Svg {...p}><rect x="1" y="6" width="18" height="12" rx="2" /><path d="M23 13v-2" /></Svg>;
export const IStopwatch = (p: IP) => <Svg {...p}><circle cx="12" cy="13" r="8" /><path d="M12 9v4l2 2M9 2h6M12 2v3" /></Svg>;
export const ICursor = (p: IP) => <Svg {...p}><path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z" /></Svg>;
