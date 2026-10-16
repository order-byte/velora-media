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
export const backOut = (x: number, s = 1.9) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2);
export const lerp = (a: number, b: number, x: number) => a + (b - a) * x;
export const within = (t: number, a: number, b: number) => t >= a && t < b;
// 0 -> 1 pop with overshoot, starting at t0
export const pop = (t: number, t0: number, d = 0.16) => (t < t0 ? 0 : backOut(prog(t, t0, d)));

// deterministic pseudo-random in [0,1) (renders must be repeatable frame by frame)
export const rnd = (n: number) => {
  const x = Math.sin(n * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};

// ---------- footage ----------
// Face sits around (540, 640) in the source frame; zooms pivot there.
export const FACE = { x: 540, y: 640 };

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
  sticker?: number; // white sticker outline width (person layer only)
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
  sticker = 0,
}) => {
  const outline = sticker
    ? [
        `drop-shadow(${sticker}px 0 0 ${C.white})`,
        `drop-shadow(-${sticker}px 0 0 ${C.white})`,
        `drop-shadow(0 ${sticker}px 0 ${C.white})`,
        `drop-shadow(0 -${sticker}px 0 ${C.white})`,
      ].join(" ")
    : "";
  return (
    <AbsoluteFill
      style={{
        transform: `translate(${tx}px, ${ty}px) rotate(${rotate}deg) scale(${scale})`,
        transformOrigin: `${ox}px ${oy}px`,
        filter: [filter ?? "", outline].join(" ").trim() || undefined,
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

export const Paper: React.FC<{ tint?: string; style?: React.CSSProperties }> = ({ tint, style }) => (
  <AbsoluteFill style={{ backgroundColor: tint ?? C.gray1, ...style }}>
    <Img
      src={staticFile("textures/paper.jpg")}
      style={{ width: W, height: H, mixBlendMode: "multiply", opacity: tint ? 0.55 : 1 }}
    />
  </AbsoluteFill>
);

// ---------- type ----------
export const display = (size: number, color = C.white, weight = 900): React.CSSProperties => ({
  fontFamily: FONT_DISPLAY,
  fontWeight: weight,
  fontSize: size,
  lineHeight: 0.86,
  letterSpacing: "-0.045em",
  color,
  whiteSpace: "nowrap",
});
export const text = (size: number, color = C.white, weight = 700): React.CSSProperties => ({
  fontFamily: FONT_TEXT,
  fontWeight: weight,
  fontSize: size,
  lineHeight: 1.08,
  letterSpacing: "-0.02em",
  color,
});

// Word that pops in at t0 (scale + rise), stays after.
export const PopWord: React.FC<{
  t: number;
  t0: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
  from?: number;
  rise?: number;
}> = ({ t, t0, style, children, from = 0.55, rise = 24 }) => {
  if (t < t0) return null;
  const p = pop(t, t0, 0.14);
  return (
    <div
      style={{
        position: "absolute",
        ...style,
        transform: `${style?.transform ?? ""} translateY(${(1 - clamp(p)) * rise}px) scale(${lerp(from, 1, p)})`,
        opacity: clamp(prog(t, t0, 0.05)),
      }}
    >
      {children}
    </div>
  );
};

// Same pop, but laid out inline so rows of words space themselves.
export const PopInline: React.FC<{ t: number; t0: number; style?: React.CSSProperties; children: React.ReactNode; from?: number }> = ({
  t,
  t0,
  style,
  children,
  from = 0.55,
}) => {
  const p = pop(t, t0, 0.14);
  return (
    <span
      style={{
        display: "inline-block",
        ...style,
        transform: `translateY(${(1 - clamp(p)) * 24}px) scale(${lerp(from, 1, p)})`,
        opacity: t < t0 ? 0 : clamp(prog(t, t0, 0.05)),
      }}
    >
      {children}
    </span>
  );
};

// Highlighter label (V7 reference): ink on a flat accent block, slightly rotated.
export const Label: React.FC<{
  bg?: string;
  color?: string;
  rotate?: number;
  pad?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ bg = C.yellow, color = C.ink, rotate = -2, pad = "0.02em 0.16em 0.06em", style, children }) => (
  <span
    style={{
      display: "inline-block",
      background: bg,
      color,
      padding: pad,
      transform: `rotate(${rotate}deg)`,
      ...style,
    }}
  >
    {children}
  </span>
);

// ---------- captions ----------
type CaptionOpts = { y?: number; hide?: boolean; accent?: string | null; boxed?: boolean; left?: boolean; width?: number };

export const Captions: React.FC<{ t: number; opts?: CaptionOpts }> = ({ t, opts }) => {
  if (opts?.hide) return null;
  const chunk = CAPTIONS.find((c) => t >= c.start && t < c.end);
  if (!chunk || chunk.hide) return null;
  const y = opts?.y ?? 1190;
  const accent = opts?.accent === undefined ? C.yellow : opts.accent;
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
        alignItems: "center",
        columnGap: 20,
        rowGap: 6,
        ...text(84, C.white, 800),
        letterSpacing: "-0.03em",
        textShadow: "0 5px 0 rgba(0,0,0,0.38)",
      }}
    >
      {chunk.words.map((w, i) => {
        if (t < w.t - 0.02) return null;
        const p = pop(t, w.t - 0.02, 0.12);
        const em = w.em && accent;
        const boxed = opts?.boxed && !em;
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              transform: `translateY(${(1 - clamp(p)) * 18}px) scale(${lerp(0.6, 1, p)})`,
              ...(boxed ? { background: C.black, padding: "0 14px 4px", textShadow: "none" } : {}),
              ...(em
                ? {
                    background: accent as string,
                    color: accent === C.yellow ? C.ink : C.white,
                    padding: "0 14px 4px",
                    textShadow: "none",
                    transform: `translateY(${(1 - clamp(p)) * 18}px) scale(${lerp(0.6, 1, p)}) rotate(-2deg)`,
                  }
                : {}),
            }}
          >
            {w.w}
          </span>
        );
      })}
    </div>
  );
};

// ---------- frame counter (runs the whole reel; part of the hunt) ----------
export const FrameCounter: React.FC<{ frame: number; dark?: boolean; scramble?: boolean }> = ({ frame, dark, scramble }) => (
  <div
    style={{
      position: "absolute",
      left: 64,
      top: 236,
      display: "flex",
      alignItems: "center",
      gap: 12,
      padding: "8px 16px 9px",
      background: dark ? C.white : C.black,
      color: dark ? C.black : C.white,
      ...text(26, dark ? C.black : C.white, 700),
      letterSpacing: "0.08em",
      fontVariantNumeric: "tabular-nums",
    }}
  >
    <span style={{ width: 12, height: 12, borderRadius: 6, background: dark ? C.black : C.white, display: "inline-block" }} />
    FRAME {scramble ? [0, 1, 2, 3].map((i) => (rnd(frame * 7 + i) < 0.35 ? "?" : String(Math.floor(rnd(frame * 13 + i * 5) * 10)))).join("") : String(frame + 1).padStart(4, "0")}
    <span style={{ opacity: 0.55 }}>/ {TOTAL_FRAMES}</span>
  </div>
);

// ---------- desktop UI props ----------
export const Cursor: React.FC<{ x: number; y: number; scale?: number; pressed?: boolean }> = ({ x, y, scale = 1.6, pressed }) => (
  <svg
    width={40 * scale}
    height={56 * scale}
    viewBox="0 0 40 56"
    style={{ position: "absolute", left: x, top: y, transform: `scale(${pressed ? 0.86 : 1})`, transformOrigin: "0 0" }}
  >
    <path d="M3 2 L3 44 L13 34 L20 51 L28 47 L21 31 L35 31 Z" fill={C.black} stroke={C.white} strokeWidth={3} strokeLinejoin="round" />
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
      background: C.white,
      border: `3px solid ${C.black}`,
      borderRadius: 16,
      overflow: "hidden",
      boxShadow: `10px 10px 0 ${C.black}`,
      ...style,
    }}
  >
    <div
      style={{
        height: 64,
        background: C.gray1,
        borderBottom: `3px solid ${C.black}`,
        display: "flex",
        alignItems: "center",
        padding: "0 22px",
        gap: 12,
      }}
    >
      {[0, 1, 2].map((i) => (
        <span key={i} style={{ width: 18, height: 18, borderRadius: 9, border: `3px solid ${C.black}`, background: i === 0 ? C.black : C.white }} />
      ))}
      <span style={{ ...text(28, C.black, 700), marginLeft: 14 }}>{title}</span>
    </div>
    {children}
  </div>
);

// Figma-style selection box with corner handles and a name tag.
export const Selection: React.FC<{ x: number; y: number; w: number; h: number; tag?: string; color?: string; p?: number }> = ({
  x,
  y,
  w,
  h,
  tag,
  color = C.yellow,
  p = 1,
}) => {
  const k = clamp(p);
  const cw = w * lerp(1.25, 1, easeOut(k));
  const ch = h * lerp(1.25, 1, easeOut(k));
  const cx = x + (w - cw) / 2;
  const cy = y + (h - ch) / 2;
  const hs = 22;
  return (
    <div style={{ position: "absolute", left: cx, top: cy, width: cw, height: ch, border: `5px solid ${color}`, opacity: k > 0 ? 1 : 0 }}>
      {[
        [-hs / 2 - 2.5, -hs / 2 - 2.5],
        [cw - hs / 2 - 7.5, -hs / 2 - 2.5],
        [-hs / 2 - 2.5, ch - hs / 2 - 7.5],
        [cw - hs / 2 - 7.5, ch - hs / 2 - 7.5],
      ].map(([l, tp], i) => (
        <span key={i} style={{ position: "absolute", left: l, top: tp, width: hs, height: hs, background: C.white, border: `4px solid ${color}` }} />
      ))}
      {tag ? (
        <span
          style={{
            position: "absolute",
            left: -5,
            top: -58,
            background: color,
            padding: "6px 14px 8px",
            ...text(30, color === C.yellow ? C.ink : C.white, 800),
            letterSpacing: "0.04em",
          }}
        >
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
