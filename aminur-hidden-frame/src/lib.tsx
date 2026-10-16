import React from "react";
import { AbsoluteFill, Freeze, Img, OffthreadVideo, staticFile } from "remotion";
import { CAPTIONS } from "./data";
import { C, FONT_DISPLAY, FONT_TEXT, H, TOTAL_FRAMES, W } from "./theme";

// ---------- timing helpers (t = seconds on the edit timeline) ----------
export const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const prog = (t: number, t0: number, d: number) => clamp((t - t0) / d);
export const easeOut = (x: number) => 1 - Math.pow(1 - x, 3);
export const easeIn = (x: number) => x * x * x;
export const easeInOut = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
export const expoOut = (x: number) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
export const lerp = (a: number, b: number, x: number) => a + (b - a) * x;
export const within = (t: number, a: number, b: number) => t >= a && t < b;
// smooth 0 -> 1 reveal starting at t0 (exponential ease-out, no overshoot)
export const reveal = (t: number, t0: number, d = 0.5) => (t < t0 ? 0 : expoOut(prog(t, t0, d)));
export const pop = (t: number, t0: number, d = 0.4) => reveal(t, t0, d);

// deterministic pseudo-random in [0,1) (renders must be repeatable frame by frame)
export const rnd = (n: number) => {
  const x = Math.sin(n * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};

// ---------- footage ----------
// Face sits around (540, 640) in the source frame; zooms pivot there. The F1-car mic sits near (570, 960).
export const FACE = { x: 540, y: 640 };
export const MIC = { x: 570, y: 960 };

type FootageProps = {
  frame: number; // source frame of selects.mp4 to show
  scale?: number;
  ox?: number;
  oy?: number;
  tx?: number;
  ty?: number;
  rotate?: number;
  filter?: string;
  person?: boolean; // alpha cut-out layer instead of the full frame
  shadow?: boolean; // soft contact shadow under a cut-out
};

export const Footage: React.FC<FootageProps> = ({
  frame,
  scale = 1,
  ox = FACE.x,
  oy = FACE.y,
  tx = 0,
  ty = 0,
  rotate = 0,
  filter,
  person = false,
  shadow = false,
}) => {
  const f = [filter ?? "", shadow ? "drop-shadow(0 30px 50px rgba(0,0,0,0.65)) drop-shadow(0 0 2px rgba(255,255,255,0.18))" : ""]
    .join(" ")
    .trim();
  return (
    <AbsoluteFill
      style={{
        transform: `translate(${tx}px, ${ty}px) rotate(${rotate}deg) scale(${scale})`,
        transformOrigin: `${ox}px ${oy}px`,
        filter: f || undefined,
      }}
    >
      <Freeze frame={Math.max(0, Math.round(frame))}>
        <OffthreadVideo
          src={staticFile(person ? "media/person.webm" : "media/selects.mp4")}
          transparent={person}
          muted
          style={{ width: W, height: H }}
        />
      </Freeze>
    </AbsoluteFill>
  );
};

// Dark stage with a soft key light behind the subject (premium backdrop for cut-outs and type cards).
export const Stage: React.FC<{ cx?: number; cy?: number; light?: number }> = ({ cx = 50, cy = 40, light = 0.1 }) => (
  <AbsoluteFill style={{ background: C.stage }}>
    <AbsoluteFill
      style={{ background: `radial-gradient(ellipse 85% 55% at ${cx}% ${cy}%, rgba(255,255,255,${light}) 0%, rgba(255,255,255,0) 72%)` }}
    />
  </AbsoluteFill>
);

// Light paper (kept only for the hidden frame card).
export const Paper: React.FC<{ tint?: string; style?: React.CSSProperties }> = ({ tint, style }) => (
  <AbsoluteFill style={{ backgroundColor: tint ?? C.gray1, ...style }}>
    <Img src={staticFile("textures/paper.jpg")} style={{ width: W, height: H, mixBlendMode: "multiply", opacity: tint ? 0.35 : 1 }} />
  </AbsoluteFill>
);

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.7 }) => (
  <AbsoluteFill
    style={{ background: `radial-gradient(ellipse 75% 60% at 50% 42%, rgba(0,0,0,0) 45%, rgba(0,0,0,${strength}) 100%)` }}
  />
);

// ---------- type ----------
export const display = (size: number, color = C.white, weight = 800): React.CSSProperties => ({
  fontFamily: FONT_DISPLAY,
  fontWeight: weight,
  fontSize: size,
  lineHeight: 0.9,
  letterSpacing: "-0.04em",
  color,
  whiteSpace: "nowrap",
});
export const text = (size: number, color = C.white, weight = 600): React.CSSProperties => ({
  fontFamily: FONT_TEXT,
  fontWeight: weight,
  fontSize: size,
  lineHeight: 1.12,
  letterSpacing: "-0.01em",
  color,
});
// tracked small caps label
export const label = (size: number, color = C.white, spacing = 0.24): React.CSSProperties => ({
  fontFamily: FONT_TEXT,
  fontWeight: 700,
  fontSize: size,
  letterSpacing: `${spacing}em`,
  textTransform: "uppercase",
  color,
  whiteSpace: "nowrap",
});

// Absolutely positioned element that blurs and rises into place at t0.
export const PopWord: React.FC<{
  t: number;
  t0: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
  from?: number;
  rise?: number;
  d?: number;
}> = ({ t, t0, style, children, from = 0.94, rise = 34, d = 0.45 }) => {
  if (t < t0) return null;
  const p = reveal(t, t0, d);
  return (
    <div
      style={{
        position: "absolute",
        ...style,
        transform: `${style?.transform ?? ""} translateY(${(1 - p) * rise}px) scale(${lerp(from, 1, p)})`,
        opacity: clamp(prog(t, t0, 0.12)),
        filter: p < 0.98 ? `blur(${(1 - p) * 14}px)` : undefined,
      }}
    >
      {children}
    </div>
  );
};

// Same reveal, laid out inline so rows of words space themselves.
export const PopInline: React.FC<{ t: number; t0: number; style?: React.CSSProperties; children: React.ReactNode; d?: number }> = ({
  t,
  t0,
  style,
  children,
  d = 0.45,
}) => {
  const p = reveal(t, t0, d);
  return (
    <span
      style={{
        display: "inline-block",
        ...style,
        transform: `translateY(${(1 - p) * 34}px) scale(${lerp(0.94, 1, p)})`,
        opacity: t < t0 ? 0 : clamp(prog(t, t0, 0.12)),
        filter: p > 0 && p < 0.98 ? `blur(${(1 - p) * 14}px)` : undefined,
      }}
    >
      {children}
    </span>
  );
};

// Mask reveal: the line slides up out of an invisible slot (classic title reveal).
export const MaskLine: React.FC<{ t: number; t0: number; d?: number; style?: React.CSSProperties; children: React.ReactNode }> = ({
  t,
  t0,
  d = 0.55,
  style,
  children,
}) => {
  const p = reveal(t, t0, d);
  return (
    <div style={{ position: "absolute", overflow: "hidden", paddingBottom: "0.08em", ...style }}>
      <div style={{ transform: `translateY(${(1 - p) * 110}%)`, opacity: t < t0 ? 0 : 1 }}>{children}</div>
    </div>
  );
};

// Accent chip (flat Atomic yellow, ink text).
export const Label: React.FC<{
  bg?: string;
  color?: string;
  rotate?: number;
  pad?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ bg = C.yellow, color = C.ink, rotate = 0, pad = "0.04em 0.2em 0.08em", style, children }) => (
  <span style={{ display: "inline-block", background: bg, color, padding: pad, borderRadius: 8, transform: `rotate(${rotate}deg)`, ...style }}>
    {children}
  </span>
);

// Glass pill with a dot, for small tracked labels.
export const Chip: React.FC<{ dot?: string; style?: React.CSSProperties; children: React.ReactNode; size?: number }> = ({
  dot = C.yellow,
  style,
  children,
  size = 28,
}) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 14,
      padding: "14px 24px 15px",
      borderRadius: 999,
      background: C.glass,
      border: `1px solid ${C.line}`,
      boxShadow: "0 20px 40px rgba(0,0,0,0.35)",
      ...label(size, C.white, 0.2),
      ...style,
    }}
  >
    {dot ? <span style={{ width: 12, height: 12, borderRadius: 6, background: dot, display: "inline-block" }} /> : null}
    {children}
  </div>
);

// ---------- captions (karaoke: spoken words white, the current word lights up) ----------
type CaptionOpts = { y?: number; hide?: boolean; accent?: string | null; boxed?: boolean; left?: boolean; width?: number };

export const Captions: React.FC<{ t: number; opts?: CaptionOpts }> = ({ t, opts }) => {
  if (opts?.hide) return null;
  const chunk = CAPTIONS.find((c) => t >= c.start && t < c.end);
  if (!chunk || chunk.hide) return null;
  const y = opts?.y ?? 1300;
  const accent = opts?.accent === undefined ? C.yellow : opts.accent;
  const enter = reveal(t, chunk.start - 0.02, 0.3);
  const current = [...chunk.words].reverse().find((w) => t >= w.t - 0.02);
  return (
    <div
      style={{
        position: "absolute",
        left: opts?.left ? 64 : 70,
        ...(opts?.width ? { width: opts.width } : { right: 70 }),
        top: y,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: opts?.left ? "flex-start" : "center",
        alignItems: "baseline",
        columnGap: 18,
        rowGap: 4,
        ...text(66, C.white, 700),
        letterSpacing: "-0.015em",
        textShadow: "0 2px 18px rgba(0,0,0,0.6), 0 1px 3px rgba(0,0,0,0.5)",
        opacity: enter,
        transform: `translateY(${(1 - enter) * 18}px)`,
        filter: enter < 0.98 ? `blur(${(1 - enter) * 8}px)` : undefined,
        ...(opts?.boxed ? { background: "rgba(10,10,11,0.55)", padding: "14px 22px 18px", borderRadius: 22 } : {}),
      }}
    >
      {chunk.words.map((w, i) => {
        const spoken = t >= w.t - 0.02;
        const isCurrent = current === w;
        const lit = accent && (isCurrent || (w.em && spoken));
        return (
          <span key={i} style={{ display: "inline-block", color: lit ? accent : C.white, opacity: spoken ? 1 : 0.38, transition: "none" }}>
            {w.w}
          </span>
        );
      })}
    </div>
  );
};

// ---------- frame counter (runs the whole reel; part of the hunt) ----------
export const FrameCounter: React.FC<{ frame: number; dark?: boolean; scramble?: boolean }> = ({ frame, scramble }) => {
  const digits = scramble
    ? [0, 1, 2, 3].map((i) => (rnd(frame * 7 + i) < 0.35 ? "?" : String(Math.floor(rnd(frame * 13 + i * 5) * 10)))).join("")
    : String(frame + 1).padStart(4, "0");
  return (
    <div
      style={{
        position: "absolute",
        left: 64,
        top: 236,
        display: "flex",
        alignItems: "center",
        gap: 12,
        ...label(22, "rgba(255,255,255,0.86)", 0.22),
        fontVariantNumeric: "tabular-nums",
        textShadow: "0 1px 8px rgba(0,0,0,0.6)",
      }}
    >
      <span style={{ width: 10, height: 10, borderRadius: 5, background: C.yellow, display: "inline-block" }} />
      FRAME {digits}
      <span style={{ opacity: 0.5 }}>/ {TOTAL_FRAMES}</span>
    </div>
  );
};

// ---------- desktop UI props (dark glass) ----------
export const Cursor: React.FC<{ x: number; y: number; scale?: number; pressed?: boolean }> = ({ x, y, scale = 1.5, pressed }) => (
  <svg
    width={40 * scale}
    height={56 * scale}
    viewBox="0 0 40 56"
    style={{ position: "absolute", left: x, top: y, transform: `scale(${pressed ? 0.88 : 1})`, transformOrigin: "0 0", filter: "drop-shadow(0 6px 10px rgba(0,0,0,0.45))" }}
  >
    <path d="M3 2 L3 44 L13 34 L20 51 L28 47 L21 31 L35 31 Z" fill={C.white} stroke={C.black} strokeWidth={2.5} strokeLinejoin="round" />
  </svg>
);

export const Window: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  title: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({ x, y, w, h, title, style, children }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      height: h,
      background: C.glass,
      border: `1px solid ${C.line}`,
      borderRadius: 30,
      overflow: "hidden",
      boxShadow: "0 50px 100px rgba(0,0,0,0.55)",
      ...style,
    }}
  >
    <div style={{ height: 60, borderBottom: `1px solid ${C.line}`, display: "flex", alignItems: "center", padding: "0 24px", gap: 10 }}>
      {[0, 1, 2].map((i) => (
        <span key={i} style={{ width: 14, height: 14, borderRadius: 7, background: "rgba(255,255,255,0.22)" }} />
      ))}
      <span style={{ ...text(24, C.muted, 600), marginLeft: 14 }}>{title}</span>
    </div>
    {children}
  </div>
);

// Thin selection box with corner handles and a name tag.
export const Selection: React.FC<{ x: number; y: number; w: number; h: number; tag?: string; color?: string; p?: number }> = ({
  x,
  y,
  w,
  h,
  tag,
  color = C.yellow,
  p = 1,
}) => {
  const k = expoOut(clamp(p));
  const cw = w * lerp(1.12, 1, k);
  const ch = h * lerp(1.12, 1, k);
  const cx = x + (w - cw) / 2;
  const cy = y + (h - ch) / 2;
  const hs = 16;
  return (
    <div style={{ position: "absolute", left: cx, top: cy, width: cw, height: ch, border: `3px solid ${color}`, borderRadius: 6, opacity: k }}>
      {[
        [-hs / 2 - 1.5, -hs / 2 - 1.5],
        [cw - hs / 2 - 4.5, -hs / 2 - 1.5],
        [-hs / 2 - 1.5, ch - hs / 2 - 4.5],
        [cw - hs / 2 - 4.5, ch - hs / 2 - 4.5],
      ].map(([l, tp], i) => (
        <span key={i} style={{ position: "absolute", left: l, top: tp, width: hs, height: hs, background: C.white, border: `3px solid ${color}`, borderRadius: 3 }} />
      ))}
      {tag ? (
        <span style={{ position: "absolute", left: -3, top: -50, background: color, padding: "6px 12px 7px", borderRadius: 6, ...label(20, color === C.yellow ? C.ink : C.white, 0.14) }}>
          {tag}
        </span>
      ) : null}
    </div>
  );
};

// One cell of the thumbnail sprite (8 x 6 grid of 216 x 384 frames from the selects).
export const Thumb: React.FC<{ i: number; w: number; style?: React.CSSProperties }> = ({ i, w, style }) => {
  const k = ((i % 48) + 48) % 48;
  const s = w / 216;
  return (
    <div style={{ width: w, height: 384 * s, overflow: "hidden", position: "relative", ...style }}>
      <Img
        src={staticFile("media/thumbs.jpg")}
        style={{ position: "absolute", width: 1728 * s, height: 2304 * s, left: -(k % 8) * 216 * s, top: -Math.floor(k / 8) * 384 * s, maxWidth: "none" }}
      />
    </div>
  );
};
