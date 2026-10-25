import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, staticFile, useCurrentFrame, interpolate, Easing, random } from "remotion";
import {
  C, inter, serif, mono, FPS, fr, ease, useSpring, Fill, Pill, StyleTag, SUBS, SCN,
  ICam, IScissors, IMoon, ICheck, IX, IDown, IFlame, IBattery, IStopwatch, ISend, IHeart, IMsg, IUser, IBolt, ITrend, IFilm, IPin, ICursor, IPhone, IMail, IMic,
} from "./lib";
import { Talking } from "./Base";
import { Captions2 } from "./Captions2";
import { Captions4 } from "./Captions4";

/* ------------------------------------------------ shared pieces */
export const VideoCard: React.FC<{ src: string; x: number; y: number; w: number; h: number; r?: number; rot?: number; delay?: number; filter?: string; startFrom?: number; rate?: number; shadow?: boolean }> = ({
  src, x, y, w, h, r = 40, rot = 0, delay = 0, filter, startFrom = 0, rate = 1, shadow = true,
}) => {
  const s = useSpring(delay);
  return (
    <div style={{
      position: "absolute", left: x, top: y, width: w, height: h, borderRadius: r, overflow: "hidden",
      boxShadow: shadow ? "0 40px 110px rgba(0,0,0,0.35), 0 8px 24px rgba(0,0,0,0.2)" : "none",
      transform: `rotate(${rot * s}deg) scale(${0.82 + 0.18 * s})`, opacity: Math.min(1, s * 1.5),
    }}>
      <OffthreadVideo src={staticFile(src)} muted startFrom={startFrom} playbackRate={rate} style={{ width: "100%", height: "100%", objectFit: "cover", filter }} />
    </div>
  );
};

/** talking head rendered inside a box, synced to the global timeline (offset = sequence start in frames) */
export const Mini: React.FC<{ x: number; y: number; w: number; h: number; r?: number; offset: number; delay?: number; ring?: string }> = ({ x, y, w, h, r = 36, offset, delay = 0, ring }) => {
  const s = useSpring(delay);
  const sc = Math.max(w / 1080, h / 1920);
  return (
    <div style={{
      position: "absolute", left: x, top: y, width: w, height: h, borderRadius: r, overflow: "hidden",
      boxShadow: `0 30px 90px rgba(0,0,0,0.35)${ring ? `, 0 0 0 8px ${ring}` : ""}`, transform: `scale(${0.8 + 0.2 * s})`, opacity: Math.min(1, s * 1.5),
    }}>
      <div style={{ position: "absolute", width: 1080, height: 1920, left: (w - 1080 * sc) / 2, top: (h - 1920 * sc) / 2, transform: `scale(${sc})`, transformOrigin: "0 0" }}>
        <Talking muted offset={offset} />
      </div>
    </div>
  );
};

const Paper: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: `radial-gradient(120% 80% at 50% 30%, #FBFAF7 0%, ${C.paper} 60%, #E7E3DB 100%)` }}>{children}</AbsoluteFill>
);
const Dark: React.FC<{ children?: React.ReactNode; glow?: string }> = ({ children, glow = "rgba(168,85,247,0.28)" }) => (
  <AbsoluteFill style={{ background: `radial-gradient(90% 60% at 50% 38%, ${glow} 0%, rgba(12,10,16,0) 62%), radial-gradient(120% 90% at 50% 40%, #0c0a10 0%, #060508 100%)`, backgroundColor: "#08070b" }}>{children}</AbsoluteFill>
);

export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.18 }) => {
  const f = useCurrentFrame();
  return (
    <svg width="1080" height="1920" style={{ position: "absolute", inset: 0, opacity, mixBlendMode: "overlay", pointerEvents: "none" }}>
      <filter id={`g${f % 6}`}><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={f % 6} /><feColorMatrix type="saturate" values="0" /></filter>
      <rect width="1080" height="1920" filter={`url(#g${f % 6})`} />
    </svg>
  );
};

/** Flash frame used on hard transitions */
export const Flash: React.FC<{ color?: string; dur?: number }> = ({ color = "#fff", dur = 5 }) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{ background: color, opacity: interpolate(f, [0, dur], [0.85, 0], { extrapolateRight: "clamp" }), pointerEvents: "none" }} />;
};

/** Big word overlay */
export const Hero: React.FC<{ text: string; y?: number; size?: number; font?: "serif" | "sans"; color?: string; glow?: string; sub?: string; dur?: number; italicCaps?: boolean }> = ({
  text, y = 230, size = 210, font = "sans", color = "#fff", glow, sub, dur = 40, italicCaps,
}) => {
  const f = useCurrentFrame();
  const s = useSpring(0, { damping: 11, stiffness: 190, mass: 0.6 });
  const out = interpolate(f, [dur - 6, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: y, left: 0, right: 0, textAlign: "center", opacity: out }}>
      <div style={{
        display: "inline-block", fontFamily: font === "serif" ? serif : inter, fontStyle: font === "serif" || italicCaps ? "italic" : "normal",
        fontWeight: font === "serif" ? 400 : 900, fontSize: size, lineHeight: 1, letterSpacing: font === "serif" ? "-0.01em" : "-0.045em", color,
        textTransform: italicCaps ? "uppercase" : "none",
        textShadow: glow ? `0 0 40px ${glow}, 0 0 90px ${glow}, 0 10px 30px rgba(0,0,0,0.5)` : "0 10px 40px rgba(0,0,0,0.55)",
        transform: `scale(${0.4 + 0.6 * s}) rotate(${(1 - s) * -6}deg)`, filter: `blur(${(1 - Math.min(1, s)) * 12}px)`,
      }}>{text}</div>
      {sub && <div style={{ marginTop: 14, fontFamily: mono, fontWeight: 700, fontSize: 36, letterSpacing: "0.14em", color: "rgba(255,255,255,0.85)", opacity: s }}>{sub}</div>}
    </div>
  );
};

/** Slot-machine number: digits roll and land staggered */
export const SlotNumber: React.FC<{ value: string; size: number; color: string; glow?: string; land: number }> = ({ value, size, color, glow, land }) => {
  const f = useCurrentFrame();
  return (
    <div style={{ display: "inline-flex", fontFamily: inter, fontWeight: 900, fontSize: size, lineHeight: 1, letterSpacing: "-0.05em", color, filter: glow ? `drop-shadow(0 0 22px ${glow}) drop-shadow(0 0 60px ${glow})` : undefined }}>
      {value.split("").map((ch, i) => {
        if (!/[0-9]/.test(ch)) return <span key={i}>{ch}</span>;
        const target = Number(ch) + 30;
        const endF = land + i * 4;
        const pos = interpolate(f, [0, endF], [0, target], { extrapolateRight: "clamp", easing: Easing.bezier(0.15, 0.85, 0.25, 1) });
        const blur = Math.min(3.5, Math.abs(interpolate(f, [endF - 6, endF], [3.5, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })));
        const mask = "linear-gradient(180deg, transparent 0%, #000 22%, #000 78%, transparent 100%)";
        return (
          <span key={i} style={{ display: "inline-block", height: size, overflow: "hidden", position: "relative", width: size * 0.62, WebkitMaskImage: f < endF ? mask : undefined, maskImage: f < endF ? mask : undefined }}>
            <span style={{ position: "absolute", left: 0, top: -(pos % 10) * size, filter: `blur(${f < endF ? blur : 0}px)` }}>
              {Array.from({ length: 11 }, (_, k) => <div key={k} style={{ height: size }}>{k % 10}</div>)}
            </span>
          </span>
        );
      })}
    </div>
  );
};

/* ================================================= 1 · HOOK */
export const HookSplit: React.FC<{ cut: number; words: { w: string; f: number; c?: string }[] }> = ({ cut, words }) => {
  const f = useCurrentFrame();
  const p = ease(f, cut, cut + 9);
  const sIn = useSpring(0, { damping: 15, stiffness: 120 });
  const lerp = (a: number, b: number) => a + (b - a) * p;
  const raw = { x: 44 - 620 * p, y: 760, w: 330, h: 587 };
  const ed = { x: lerp(400, 0), y: lerp(420, 0), w: lerp(636, 1080), h: lerp(1131, 1920), r: lerp(38, 0) };
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: "#0b0910", opacity: 1 - p }}>
        <div style={{ position: "absolute", inset: -80, filter: "blur(40px) brightness(0.35)", opacity: 0.9 }}><Talking muted offset={0} /></div>
      </AbsoluteFill>
      {/* RAW card */}
      <div style={{ position: "absolute", left: raw.x, top: raw.y, width: raw.w, opacity: 1 - p, transform: `translateY(${(1 - sIn) * 120}px) rotate(${-4 * p}deg)` }}>
        <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 30, letterSpacing: "0.18em", color: "rgba(255,255,255,0.7)", marginBottom: 14 }}>RAW</div>
        <div style={{ width: raw.w, height: raw.h, borderRadius: 26, overflow: "hidden", position: "relative", boxShadow: "0 30px 80px rgba(0,0,0,0.5)" }}>
          <div style={{ position: "absolute", width: 1080, height: 1920, transform: `scale(${raw.w / 1080})`, transformOrigin: "0 0" }}><Talking raw muted offset={0} /></div>
        </div>
      </div>
      {/* EDIT card -> grows to full screen on the cut */}
      <div style={{ position: "absolute", left: ed.x, top: ed.y - 50 * (1 - p), width: ed.w, transform: `translateY(${(1 - sIn) * 160}px)` }}>
        <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 30, letterSpacing: "0.18em", color: C.purple, marginBottom: 14, opacity: 1 - p, height: 50 * (1 - p) }}>EDIT</div>
        <div style={{ width: ed.w, height: ed.h, borderRadius: ed.r, overflow: "hidden", position: "relative", boxShadow: "0 40px 120px rgba(168,85,247,0.35)" }}>
          <div style={{ position: "absolute", width: 1080, height: 1920, transform: `scale(${ed.w / 1080})`, transformOrigin: "0 0" }}><Talking muted offset={0} /></div>
        </div>
      </div>
      {/* headline */}
      <div style={{ position: "absolute", top: 190, left: 40, right: 40, textAlign: "center", opacity: 1 - p }}>
        {words.map((w, i) => {
          const a = interpolate(f, [w.f - 1, w.f + 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
          return <span key={i} style={{ display: "inline-block", margin: "0 12px", fontFamily: inter, fontWeight: 900, fontSize: 92, letterSpacing: "-0.04em", color: w.c || "#fff", opacity: a, transform: `scale(${0.5 + 0.5 * a})`, textShadow: w.c === C.green ? `0 0 30px ${C.green}` : "0 6px 30px rgba(0,0,0,0.6)" }}>{w.w}</span>;
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Price200Hit: React.FC = () => {
  const f = useCurrentFrame();
  const out = interpolate(f, [26, 32], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: 150, left: 0, right: 0, textAlign: "center", opacity: out }}>
      <SlotNumber value="$200" size={250} color={C.green} glow="rgba(61,255,143,0.6)" land={8} />
    </div>
  );
};

/* ================================================= 2 · PAIN */
const TimerRing: React.FC<{ p: number; size?: number; color?: string }> = ({ p, size = 56, color = C.green }) => {
  const r = 20, c = 2 * Math.PI * r;
  return (
    <svg width={size} height={size} viewBox="0 0 48 48"><circle cx="24" cy="24" r={r} stroke="rgba(255,255,255,0.18)" strokeWidth="6" fill="none" />
      <circle cx="24" cy="24" r={r} stroke={color} strokeWidth="6" fill="none" strokeDasharray={c} strokeDashoffset={c * (1 - p)} strokeLinecap="round" transform="rotate(-90 24 24)" /></svg>
  );
};

export const PainShoot: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <Paper>
      <VideoCard src="broll/shoot_youtuber.mp4" x={150} y={330} w={780} h={1060} rot={-2.5} />
      <div style={{ position: "absolute", top: 170, left: 0, right: 0, display: "flex", justifyContent: "center", gap: 22 }}>
        <Pill delay={3} size={44}><ICam size={46} color={C.purple} /> SHOOT</Pill>
        <Pill delay={7} size={44}><TimerRing p={ease(f, 7, 40)} /> 10 MIN</Pill>
      </div>
    </Paper>
  );
};

export const PainEdit: React.FC<{ raatF: number }> = ({ raatF }) => {
  const f = useCurrentFrame();
  const mins = interpolate(f, [raatF - 4, raatF + 22], [23 * 60 + 47, 29 * 60 + 58], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const h24 = Math.floor(mins / 60) % 24, m = Math.floor(mins % 60);
  const label = `${((h24 + 11) % 12) + 1}:${String(m).padStart(2, "0")} ${h24 >= 12 ? "PM" : "AM"}`;
  return (
    <AbsoluteFill style={{ background: "#05060c" }}>
      <OffthreadVideo src={staticFile("broll/edit_rear.mp4")} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) brightness(0.62) contrast(1.15)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.1) 45%, rgba(0,0,0,0.7) 100%)" }} />
      <div style={{ position: "absolute", top: 170, left: 0, right: 0, display: "flex", justifyContent: "center", gap: 22 }}>
        <Pill delay={2} size={44}><IScissors size={44} color={C.purple} /> EDIT</Pill>
        <Pill delay={raatF - 2} size={44}><IMoon size={44} color={C.amber} /> ALL NIGHT</Pill>
      </div>
      <div style={{ position: "absolute", top: 380, left: 0, right: 0, textAlign: "center", fontFamily: mono, fontWeight: 700, fontSize: 150, color: "#fff", letterSpacing: "-0.02em", textShadow: "0 0 40px rgba(255,255,255,0.35)" }}>{label}</div>
    </AbsoluteFill>
  );
};

export const PainPost: React.FC = () => {
  const days = ["M", "T", "W", "T", "F", "S", "S"];
  const posted = [true, false, false, true, false, false, false];
  return (
    <div style={{ position: "absolute", top: 120, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 18 }}>
      <Pill size={32} delay={0}>POSTING THIS WEEK</Pill>
      <div style={{ display: "flex", gap: 16 }}>
        {days.map((d, i) => <DayTile key={i} d={d} ok={posted[i]} delay={4 + i * 3} />)}
      </div>
    </div>
  );
};
const DayTile: React.FC<{ d: string; ok: boolean; delay: number }> = ({ d, ok, delay }) => {
  const s = useSpring(delay, { damping: 12, stiffness: 220, mass: 0.5 });
  return (
    <div style={{
      width: 112, height: 138, borderRadius: 22, background: ok ? "rgba(255,255,255,0.92)" : "rgba(255,77,77,0.92)", display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", gap: 6, transform: `scale(${s}) translateY(${(1 - s) * 30}px)`, boxShadow: "0 16px 40px rgba(0,0,0,0.35)",
    }}>
      <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 30, color: ok ? C.ink : "#fff" }}>{d}</div>
      {ok ? <ICheck size={54} color="#14a85a" stroke={3.2} /> : <IX size={54} color="#fff" stroke={3.2} />}
    </div>
  );
};

export const PainGrowth: React.FC<{ burnF: number }> = ({ burnF }) => {
  const f = useCurrentFrame();
  const p = ease(f, 2, 24);
  const pts = [[0, 40], [80, 52], [160, 38], [240, 70], [320, 96], [400, 120], [480, 150], [560, 190]];
  const d = pts.map((q, i) => `${i ? "L" : "M"}${q[0]},${q[1]}`).join(" ");
  const out = interpolate(f, [burnF - 3, burnF], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s = useSpring(0);
  return (
    <div style={{ position: "absolute", top: 130, left: 170, width: 740, height: 360, borderRadius: 36, background: "rgba(255,255,255,0.95)", boxShadow: "0 30px 80px rgba(0,0,0,0.35)", opacity: out * s, transform: `scale(${0.85 + 0.15 * s})`, padding: 34 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14, fontFamily: inter, fontWeight: 800, fontSize: 46, color: C.ink }}>
        GROWTH <span style={{ color: C.red, display: "flex", alignItems: "center", gap: 8 }}><IDown size={50} color={C.red} stroke={3} />SLOW</span>
      </div>
      <svg width="672" height="220" viewBox="0 0 560 210" style={{ marginTop: 10 }}>
        <path d={d} fill="none" stroke={C.red} strokeWidth="9" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="900" strokeDashoffset={900 * (1 - p)} />
      </svg>
    </div>
  );
};

export const Burnout: React.FC = () => {
  const f = useCurrentFrame();
  const jit = f < 8 ? (random(`j${f}`) - 0.5) * 40 : 0;
  const batt = interpolate(f, [4, 40], [0.6, 0.04], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#120507" }}>
      <OffthreadVideo src={staticFile("broll/exhausted.mp4")} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(0.9) contrast(1.25) brightness(0.55)", transform: `translateX(${jit}px)` }} />
      <AbsoluteFill style={{ background: "radial-gradient(80% 60% at 50% 45%, rgba(255,40,40,0.0) 0%, rgba(160,0,0,0.55) 100%)" }} />
      <div style={{ position: "absolute", top: 240, left: 0, right: 0, textAlign: "center" }}>
        <div style={{ fontFamily: inter, fontWeight: 900, fontSize: 190, letterSpacing: "-0.05em", color: C.red, transform: `translateX(${-jit * 0.6}px)`, textShadow: `${f < 10 ? 8 : 0}px 0 rgba(0,255,255,0.6), ${f < 10 ? -8 : 0}px 0 rgba(255,0,80,0.8), 0 0 60px rgba(255,40,40,0.6)` }}>BURNOUT</div>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 16, marginTop: 20 }}>
          <div style={{ position: "relative", width: 230, height: 110 }}>
            <IBattery size={230} color="#fff" stroke={1.6} />
            <div style={{ position: "absolute", left: 30, top: 66, height: 98 / 1, width: 0 }} />
            <div style={{ position: "absolute", left: 29, top: 76, width: 152 * batt, height: 78, borderRadius: 6, background: C.red, marginTop: -20 }} />
          </div>
          <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 64, color: "#fff" }}>{Math.round(batt * 100)}%</div>
        </div>
      </div>
      <Grain opacity={0.22} />
    </AbsoluteFill>
  );
};

/* ================================================= 3 · OFFER */
export const OfferBrand: React.FC<{ nameF: number; pkgF: number; offset: number }> = ({ nameF, pkgF, offset }) => {
  const f = useCurrentFrame();
  const logo = useSpring(2, { damping: 10, stiffness: 150, mass: 0.7 });
  const name = "Aminur Rex Team";
  const hl = ease(f, pkgF + 10, pkgF + 22);
  const pkgIn = (k: number) => interpolate(f, [pkgF + k * 4, pkgF + k * 4 + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  return (
    <Paper>
      <div style={{ position: "absolute", top: 150, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ transform: `scale(${logo}) rotate(${(1 - logo) * -25}deg)`, borderRadius: "50%", boxShadow: "0 30px 70px rgba(120,160,0,0.35)" }}><Avatar size={190} /></div>
        <div style={{ marginTop: 34, fontFamily: inter, fontWeight: 900, fontSize: 104, letterSpacing: "-0.05em", color: C.ink, whiteSpace: "nowrap" }}>
          {name.split("").map((ch, i) => {
            const a = interpolate(f, [nameF + i * 1.2, nameF + i * 1.2 + 7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return <span key={i} style={{ display: "inline-block", opacity: a, filter: `blur(${(1 - a) * 14}px)`, transform: `translateY(${(1 - a) * 24}px)`, whiteSpace: "pre" }}>{ch}</span>;
          })}
        </div>
      </div>
      <div style={{ position: "absolute", top: 640, left: 0, right: 0, textAlign: "center", lineHeight: 1.02 }}>
        <div style={{ fontFamily: inter, fontWeight: 800, fontSize: 104, letterSpacing: "-0.045em", color: C.ink, opacity: pkgIn(0), transform: `scale(${0.6 + 0.4 * pkgIn(0)})` }}>Monthly</div>
        <div style={{ position: "relative", display: "inline-block", margin: "6px 0", opacity: pkgIn(1), transform: `scale(${0.6 + 0.4 * pkgIn(1)})` }}>
          <div style={{ position: "absolute", left: -24, right: -24, top: 22, bottom: 8, background: C.purple, borderRadius: 14, transformOrigin: "left", transform: `scaleX(${hl})` }} />
          <span style={{ position: "relative", fontFamily: serif, fontStyle: "italic", fontSize: 170, color: hl > 0.5 ? "#fff" : C.ink }}>Editing</span>
        </div>
        <div style={{ fontFamily: inter, fontWeight: 800, fontSize: 104, letterSpacing: "-0.045em", color: C.ink, opacity: pkgIn(2), transform: `scale(${0.6 + 0.4 * pkgIn(2)})` }}>Package</div>
      </div>
      <Mini x={345} y={1250} w={390} h={520} r={34} offset={offset} delay={6} ring="rgba(168,85,247,0.9)" />
    </Paper>
  );
};

export const BigLine: React.FC<{ text: string; icon?: React.ReactNode; y?: number; size?: number; color?: string }> = ({ text, icon, y = 160, size = 120, color = "#fff" }) => {
  const s = useSpring(0, { damping: 12, stiffness: 180, mass: 0.6 });
  return (
    <div style={{ position: "absolute", top: y, left: 0, right: 0, display: "flex", alignItems: "center", justifyContent: "center", gap: 24, transform: `scale(${0.5 + 0.5 * s})`, opacity: Math.min(1, s * 1.6) }}>
      {icon}
      <span style={{ fontFamily: inter, fontWeight: 900, fontSize: size, letterSpacing: "-0.05em", color, textShadow: "0 10px 40px rgba(0,0,0,0.55)" }}>{text}</span>
    </div>
  );
};

export const WeDo: React.FC = () => {
  const items = ["Cutting & pacing", "Captions", "Motion graphics", "Sound design", "Colour grade"];
  return (
    <AbsoluteFill style={{ background: "#07060a" }}>
      <OffthreadVideo src={staticFile("broll/editor_office.mp4")} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.42) saturate(0.8)" }} />
      <BigLine text="WE DO THE REST." y={190} size={104} />
      <div style={{ position: "absolute", top: 400, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
        {items.map((t, i) => <Pill key={i} delay={6 + i * 5} size={46} bg="rgba(255,255,255,0.94)" color={C.ink}><ICheck size={46} color="#14a85a" stroke={3.4} />{t}</Pill>)}
      </div>
    </AbsoluteFill>
  );
};

/* ================================================= 4 · STYLES */
export const QBubble: React.FC = () => {
  const s = useSpring(3, { damping: 8, stiffness: 160, mass: 0.6 });
  const f = useCurrentFrame();
  return (
    <div style={{ position: "absolute", top: 120, left: 0, right: 0, display: "flex", justifyContent: "center", alignItems: "center", gap: 26 }}>
      <span style={{ fontFamily: serif, fontStyle: "italic", fontSize: 230, color: "#fff", textShadow: "0 10px 40px rgba(0,0,0,0.5)", transform: `scale(${0.5 + 0.5 * s})`, display: "inline-block" }}>style</span>
      <div style={{ width: 190, height: 190, borderRadius: "50%", background: `radial-gradient(circle at 35% 30%, #D8B4FE, ${C.purple} 45%, #5B21B6 100%)`, display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: inter, fontWeight: 900, fontSize: 130, color: "#fff", boxShadow: "0 30px 80px rgba(124,58,237,0.6), inset -12px -16px 30px rgba(0,0,0,0.25)", transform: `scale(${s}) rotate(${Math.sin(f / 6) * 6}deg)` }}>?</div>
    </div>
  );
};

const STYLE_THUMBS = ["thumbs/me_21.jpg", "thumbs/podcast_man.jpg", "thumbs/city_night.jpg", "thumbs/vlog_street.jpg", "thumbs/coast_aerial.jpg", "thumbs/hands_typing.jpg"];
const STYLE_NAMES = ["Talking head", "Podcast", "Documentary", "Cinematic", "Motion", "Faceless"];

export const Trending: React.FC = () => (
  <div style={{ position: "absolute", top: 110, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 22 }}>
    <Pill size={40} delay={0}><IFlame size={42} color="#FF7A1A" /> TRENDING NOW</Pill>
    <div style={{ display: "flex", gap: 12 }}>
      {STYLE_THUMBS.map((src, i) => <Thumb key={i} src={src} delay={4 + i * 2} w={150} h={250} />)}
    </div>
  </div>
);
const Thumb: React.FC<{ src: string; delay: number; w: number; h: number; label?: string; dark?: boolean }> = ({ src, delay, w, h, label, dark }) => {
  const s = useSpring(delay, { damping: 12, stiffness: 200, mass: 0.5 });
  return (
    <div style={{ width: w, transform: `scale(${s}) translateY(${(1 - s) * 40}px)`, opacity: Math.min(1, s * 1.5) }}>
      <div style={{ width: w, height: h, borderRadius: 18, overflow: "hidden", boxShadow: "0 16px 40px rgba(0,0,0,0.4)", border: "3px solid rgba(255,255,255,0.85)" }}>
        <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>
      {label && <div style={{ marginTop: 12, textAlign: "center", fontFamily: inter, fontWeight: 800, fontSize: 32, color: dark ? C.ink : "#fff" }}>{label}</div>}
    </div>
  );
};

const RecFrame: React.FC = () => {
  const f = useCurrentFrame();
  const c = "rgba(255,255,255,0.9)";
  const corner = (st: React.CSSProperties) => <div style={{ position: "absolute", width: 90, height: 90, ...st }} />;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {corner({ left: 60, top: 330, borderLeft: `6px solid ${c}`, borderTop: `6px solid ${c}` })}
      {corner({ right: 60, top: 330, borderRight: `6px solid ${c}`, borderTop: `6px solid ${c}` })}
      {corner({ left: 60, bottom: 300, borderLeft: `6px solid ${c}`, borderBottom: `6px solid ${c}` })}
      {corner({ right: 60, bottom: 300, borderRight: `6px solid ${c}`, borderBottom: `6px solid ${c}` })}
      <div style={{ position: "absolute", left: 90, top: 360, display: "flex", alignItems: "center", gap: 12, fontFamily: mono, fontWeight: 700, fontSize: 34, color: "#fff" }}>
        <div style={{ width: 22, height: 22, borderRadius: "50%", background: C.red, opacity: Math.floor(f / 8) % 2 ? 1 : 0.25 }} /> REC
      </div>
      <div style={{ position: "absolute", right: 90, top: 360, fontFamily: mono, fontWeight: 700, fontSize: 34, color: "#fff" }}>4K · 60</div>
    </AbsoluteFill>
  );
};

export const DemoTalking: React.FC<{ offset: number }> = ({ offset }) => {
  const a = useSpring(2), b = useSpring(6);
  return (
    <AbsoluteFill>
      <Talking muted offset={offset} />
      <RecFrame />
      {!SCN.minimal && <div style={{ position: "absolute", top: 1120, left: 0, right: 0, textAlign: "center", fontFamily: inter, fontWeight: 900, fontStyle: "italic", fontSize: 130, lineHeight: 0.95, letterSpacing: "-0.04em", textTransform: "uppercase" }}>
        <div style={{ color: "#fff", transform: `scale(${a})`, textShadow: "0 8px 30px rgba(0,0,0,0.6)" }}>Talking</div>
        <div style={{ color: C.purple, transform: `scale(${b})`, textShadow: "0 8px 30px rgba(0,0,0,0.6)" }}>Head</div>
      </div>}
      <StyleTag n="01" label="TALKING HEAD" />
    </AbsoluteFill>
  );
};

export const DemoPodcast: React.FC = () => {
  const f = useCurrentFrame();
  const bars = Array.from({ length: 28 }, (_, i) => 18 + Math.abs(Math.sin(f / 2.2 + i * 0.7) * Math.cos(f / 3.1 + i)) * 90);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <div style={{ position: "absolute", left: 0, top: 0, width: 1080, height: 950, overflow: "hidden" }}>
        <OffthreadVideo src={staticFile("broll/podcast_man.mp4")} muted style={{ width: "100%", height: 1920, objectFit: "cover", marginTop: -420, filter: "contrast(1.08) saturate(1.05)" }} />
      </div>
      <div style={{ position: "absolute", left: 0, top: 970, width: 1080, height: 950, overflow: "hidden" }}>
        <OffthreadVideo src={staticFile("broll/podcast_woman.mp4")} muted style={{ width: "100%", height: 1920, objectFit: "cover", marginTop: -460, filter: "contrast(1.08) saturate(1.05)" }} />
      </div>
      <div style={{ position: "absolute", top: 900, left: 0, right: 0, height: 140, display: "flex", alignItems: "center", justifyContent: "center", gap: 7, background: "linear-gradient(180deg, transparent, rgba(0,0,0,0.85) 40%, rgba(0,0,0,0.85) 60%, transparent)" }}>
        {bars.map((h, i) => <div key={i} style={{ width: 12, height: h, borderRadius: 6, background: i % 5 === 0 ? C.purple : "#fff" }} />)}
      </div>
      {!SCN.minimal && <div style={{ position: "absolute", left: 60, top: 790 }}><Pill size={34} delay={3}><IMic size={34} color={C.purple} /> HOST</Pill></div>}
      {!SCN.minimal && <div style={{ position: "absolute", right: 60, top: 1080 }}><Pill size={34} delay={6}><IMic size={34} color={C.green} /> GUEST</Pill></div>}
      <StyleTag n="02" label="PODCAST CLIPS" />
    </AbsoluteFill>
  );
};

export const DemoDoc: React.FC = () => {
  const f = useCurrentFrame();
  const pin = useSpring(5, { damping: 9, stiffness: 180, mass: 0.6 });
  const text = "CHAPTER 01";
  const n = Math.floor(interpolate(f, [8, 26], [0, text.length], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const bars = ease(f, 0, 10) * 210;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <OffthreadVideo src={staticFile("broll/city_night.mp4")} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: "sepia(0.55) contrast(1.2) brightness(0.8) saturate(0.7)", transform: `scale(${1.1 + f * 0.002})` }} />
      <svg width="1080" height="1920" style={{ position: "absolute", inset: 0, opacity: 0.25 }}>
        {Array.from({ length: 12 }, (_, i) => <line key={`v${i}`} x1={i * 90} y1="0" x2={i * 90} y2="1920" stroke="#f3e2b8" strokeWidth="1.5" />)}
        {Array.from({ length: 22 }, (_, i) => <line key={`h${i}`} x1="0" y1={i * 90} x2="1080" y2={i * 90} stroke="#f3e2b8" strokeWidth="1.5" />)}
      </svg>
      <div style={{ position: "absolute", left: 540 - 60, top: 860 - 120 * pin, transform: `scale(${pin})` }}><IPin size={120} color={C.red} stroke={2.6} /></div>
      <div style={{ position: "absolute", left: 540 - 90, top: 880, width: 180, height: 60, borderRadius: "50%", border: `4px solid ${C.red}`, opacity: (1 - ((f % 20) / 20)) * pin, transform: `scale(${0.5 + (f % 20) / 20})` }} />
      <div style={{ position: "absolute", top: 1180, left: 0, right: 0, textAlign: "center" }}>
        <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 54, letterSpacing: "0.3em", color: "#f3e2b8" }}>{text.slice(0, n)}<span style={{ opacity: f % 10 < 5 ? 1 : 0 }}>▌</span></div>
        <div style={{ marginTop: 18, fontFamily: serif, fontStyle: "italic", fontSize: 92, color: "#fff", opacity: ease(f, 20, 34) }}>The story behind it</div>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: bars, background: "#000" }} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: bars, background: "#000" }} />
      <Grain opacity={0.3} />
      <StyleTag n="03" label="DOCUMENTARY" />
    </AbsoluteFill>
  );
};

export const DemoCine: React.FC = () => {
  const f = useCurrentFrame();
  const bars = ease(f, 0, 12) * 330;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <OffthreadVideo src={staticFile("broll/vlog_street.mp4")} muted playbackRate={1.4} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "contrast(1.12) saturate(1.25) sepia(0.18) hue-rotate(-8deg) brightness(0.95)", transform: `scale(${1.15 - f * 0.002})` }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,60,80,0.25), rgba(255,140,60,0.12))", mixBlendMode: "soft-light" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: bars, background: "#000" }} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: bars, background: "#000" }} />
      {!SCN.minimal && <div style={{ position: "absolute", top: 860, left: 0, right: 0, textAlign: "center", fontFamily: serif, fontStyle: "italic", fontSize: 180, color: "#fff",
        letterSpacing: `${interpolate(f, [0, 36], [0.25, 0.02], { extrapolateRight: "clamp" })}em`, opacity: ease(f, 4, 16), textShadow: "0 10px 40px rgba(0,0,0,0.5)" }}>cinematic</div>}
      <StyleTag n="04" label="CINEMATIC VLOG" />
    </AbsoluteFill>
  );
};

export const DemoMotion: React.FC = () => {
  const f = useCurrentFrame();
  const word = "MOTION";
  const icons = [IBolt, IHeart, ITrend, IFilm, IMsg, ICam];
  return (
    <Dark>
      <div style={{ position: "absolute", left: 540, top: 900, width: 0, height: 0 }}>
        {[300, 420].map((r, k) => <div key={k} style={{ position: "absolute", left: -r, top: -r, width: 2 * r, height: 2 * r, borderRadius: "50%", border: "2px dashed rgba(255,255,255,0.18)" }} />)}
        {icons.map((Ic, i) => {
          const a = (i / icons.length) * Math.PI * 2 + f / 18;
          const r = i % 2 ? 420 : 300;
          const s = interpolate(f, [2 + i * 2, 10 + i * 2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
          return <div key={i} style={{ position: "absolute", left: Math.cos(a) * r - 50, top: Math.sin(a) * r - 50, width: 100, height: 100, borderRadius: 30, background: i % 2 ? C.purple : "#fff", display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${s})`, boxShadow: "0 12px 30px rgba(0,0,0,0.4)" }}><Ic size={54} color={i % 2 ? "#fff" : C.ink} /></div>;
        })}
      </div>
      <div style={{ position: "absolute", top: 820, left: 0, right: 0, textAlign: "center", fontFamily: inter, fontWeight: 900, fontSize: 170, letterSpacing: "-0.05em", color: "#fff" }}>
        {word.split("").map((ch, i) => {
          const a = interpolate(f, [i * 2, i * 2 + 9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
          const dx = (random(`x${i}`) - 0.5) * 900, dy = (random(`y${i}`) - 0.5) * 900;
          return <span key={i} style={{ display: "inline-block", transform: `translate(${dx * (1 - a)}px, ${dy * (1 - a)}px) rotate(${(1 - a) * 90}deg)`, opacity: a }}>{ch}</span>;
        })}
      </div>
      <div style={{ position: "absolute", top: 1010, left: 0, right: 0, textAlign: "center", fontFamily: serif, fontStyle: "italic", fontSize: 96, color: C.purple, opacity: ease(f, 12, 22) }}>graphics</div>
      <StyleTag n="05" label="MOTION GRAPHICS" />
    </Dark>
  );
};

export const DemoFaceless: React.FC = () => {
  const f = useCurrentFrame();
  const words = [{ w: "No", t: 2 }, { w: "face.", t: 7 }, { w: "Just", t: 14 }, { w: "story.", t: 19, c: C.purple }];
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <OffthreadVideo src={staticFile("broll/hands_typing.mp4")} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.45) contrast(1.1) saturate(0.7)" }} />
      {!SCN.minimal && <div style={{ position: "absolute", top: 800, left: 60, right: 60, textAlign: "center" }}>
        {words.map((w, i) => {
          const a = interpolate(f, [w.t, w.t + 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
          return <span key={i} style={{ display: "inline-block", margin: "0 16px", fontFamily: inter, fontWeight: 900, fontSize: 140, letterSpacing: "-0.05em", color: w.c || "#fff", opacity: a, transform: `scale(${0.6 + 0.4 * a})` }}>{w.w}</span>;
        })}
      </div>}
      <StyleTag n="06" label="FACELESS STORY" />
    </AbsoluteFill>
  );
};

export const ContentGrid: React.FC<{ shuffleF: number }> = ({ shuffleF }) => {
  const f = useCurrentFrame();
  const sh = ease(f, shuffleF, shuffleF + 10);
  return (
    <Paper>
      <div style={{ position: "absolute", top: 190, left: 0, right: 0, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "40px 36px", padding: "0 70px" }}>
        {STYLE_THUMBS.map((src, i) => (
          <div key={i} style={{ transform: `rotate(${Math.sin(i * 2.1) * 4 * sh}deg) translateY(${Math.sin(i * 1.7) * 18 * sh}px)` }}>
            <Thumb src={src} delay={i * 2} w={280} h={440} label={STYLE_NAMES[i]} dark />
          </div>
        ))}
      </div>
    </Paper>
  );
};

/* ScrollStop: a feed that flies past and slams to a stop on our reel */
export const ScrollStop: React.FC<{ stopF: number }> = ({ stopF }) => {
  const f = useCurrentFrame();
  const itemH = 1180;
  const feed = ["thumbs/vlogger_face.jpg", "thumbs/desert_road.jpg", "thumbs/phone_scroll.jpg", "thumbs/coast_aerial.jpg", "thumbs/bts_recording.jpg", "thumbs/podcast_woman.jpg", "thumbs/editor_office.jpg", "thumbs/me_33.jpg"];
  const k = feed.length - 1;
  const pos = interpolate(f, [0, stopF], [0, k * itemH], { extrapolateRight: "clamp", easing: Easing.bezier(0.3, 0.0, 0.2, 1) });
  const vel = Math.abs(interpolate(f + 1, [0, stopF], [0, k * itemH], { extrapolateRight: "clamp", easing: Easing.bezier(0.3, 0.0, 0.2, 1) }) - pos);
  const shake = f >= stopF && f < stopF + 8 ? (random(`s${f}`) - 0.5) * 30 : 0;
  const done = ease(f, stopF, stopF + 8);
  const phoneS = useSpring(0, { damping: 15, stiffness: 140 });
  return (
    <Dark glow="rgba(61,255,143,0.16)">
      <div style={{ position: "absolute", left: 230, top: 170, width: 620, height: 1240, borderRadius: 70, background: "#000", padding: 14, boxShadow: "0 50px 140px rgba(0,0,0,0.7), 0 0 0 3px #2a2630", transform: `translate(${shake}px, ${shake * 0.4}px) scale(${0.85 + 0.15 * phoneS})` }}>
        <div style={{ position: "relative", width: "100%", height: "100%", borderRadius: 58, overflow: "hidden", background: "#111" }}>
          <div style={{ position: "absolute", left: 0, top: -pos, width: "100%", filter: `blur(${Math.min(14, vel / 12)}px)` }}>
            {feed.map((src, i) => (
              <div key={i} style={{ position: "relative", height: itemH, width: "100%" }}>
                <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                <div style={{ position: "absolute", right: 24, bottom: 160, display: "flex", flexDirection: "column", gap: 34, alignItems: "center" }}>
                  <IHeart size={60} color="#fff" /><IMsg size={58} color="#fff" /><ISend size={56} color="#fff" />
                </div>
              </div>
            ))}
          </div>
          <div style={{ position: "absolute", left: 0, right: 0, top: 540, textAlign: "center", fontFamily: inter, fontWeight: 900, fontSize: 130, color: C.green, opacity: done, transform: `scale(${0.6 + 0.4 * done})`, textShadow: `0 0 40px ${C.green}` }}>STOP.</div>
        </div>
      </div>
      <div style={{ position: "absolute", top: 1480, left: 0, right: 0, textAlign: "center", opacity: done, transform: `translateY(${(1 - done) * 40}px)` }}>
        <div style={{ fontFamily: inter, fontWeight: 900, fontSize: 104, letterSpacing: "-0.05em", color: "#fff" }}>Scroll-stopping.</div>
      </div>
    </Dark>
  );
};

/* ================================================= 5 · PRICE */
export const Invoices: React.FC<{ drops: number[]; killF: number }> = ({ drops, killF }) => {
  const f = useCurrentFrame();
  const away = ease(f, killF + 4, killF + 14, 0, 1, Easing.in(Easing.cubic));
  const stamp = interpolate(f, [killF, killF + 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  return (
    <Paper>
      {drops.map((d, i) => {
        const a = interpolate(f, [d, d + 7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
        const rot = [-6, 4, -3, 7][i % 4];
        return (
          <div key={i} style={{
            position: "absolute", left: 200 + (i % 2) * 40, top: 260 + i * 150 - away * (900 + i * 120), width: 680, height: 260, borderRadius: 28, background: "#fff",
            boxShadow: "0 24px 60px rgba(0,0,0,0.16)", padding: "30px 40px", transform: `rotate(${rot + away * (i % 2 ? 30 : -30)}deg) scale(${0.7 + 0.3 * a})`, opacity: a * (1 - away),
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontFamily: mono, fontWeight: 700, fontSize: 30, color: "#8a8292" }}><span>INVOICE</span><span>#{String(i + 1).padStart(3, "0")}</span></div>
            <div style={{ marginTop: 18, fontFamily: inter, fontWeight: 800, fontSize: 60, color: C.ink, letterSpacing: "-0.03em" }}>Reel {String(i + 1).padStart(2, "0")}</div>
            <div style={{ marginTop: 8, display: "inline-block", fontFamily: mono, fontWeight: 700, fontSize: 28, color: C.red, border: `3px solid ${C.red}`, borderRadius: 10, padding: "4px 12px" }}>PAYMENT DUE</div>
          </div>
        );
      })}
      <div style={{ position: "absolute", top: 560, left: 0, right: 0, textAlign: "center", transform: `rotate(-8deg) scale(${2.2 - 1.2 * stamp})`, opacity: stamp }}>
        <span style={{ display: "inline-block", fontFamily: inter, fontWeight: 900, fontSize: 150, color: C.red, border: `14px solid ${C.red}`, borderRadius: 30, padding: "10px 46px", letterSpacing: "-0.03em" }}>KHATAM</span>
        <div style={{ marginTop: 40, transform: "rotate(8deg)", fontFamily: inter, fontWeight: 800, fontSize: 64, color: C.ink }}>No per-reel bills.</div>
      </div>
    </Paper>
  );
};

export const PriceReveal: React.FC = () => {
  const f = useCurrentFrame();
  const sub = ease(f, 14, 24);
  return (
    <Dark glow="rgba(61,255,143,0.22)">
      {Array.from({ length: 26 }, (_, i) => {
        const a = random(`a${i}`) * Math.PI * 2, d = 200 + random(`d${i}`) * 520;
        const p = ease(f, 12, 40);
        return <div key={i} style={{ position: "absolute", left: 540 + Math.cos(a) * d * p, top: 860 + Math.sin(a) * d * p, width: 10, height: 10, borderRadius: 5, background: i % 3 ? C.green : "#fff", opacity: (1 - p) * (p > 0 ? 1 : 0) }} />;
      })}
      <div style={{ position: "absolute", top: 560, left: 0, right: 0, textAlign: "center", fontFamily: mono, fontWeight: 700, fontSize: 40, letterSpacing: "0.2em", color: "rgba(255,255,255,0.75)", opacity: ease(f, 0, 8) }}>MONTHLY EDITING PACKAGE</div>
      <div style={{ position: "absolute", top: 660, left: 0, right: 0, textAlign: "center" }}>
        <SlotNumber value="$200" size={330} color={C.green} glow="rgba(61,255,143,0.55)" land={12} />
      </div>
      <div style={{ position: "absolute", top: 1030, left: 0, right: 0, textAlign: "center", fontFamily: serif, fontStyle: "italic", fontSize: 110, color: "#fff", opacity: sub, transform: `translateY(${(1 - sub) * 30}px)` }}>per month</div>
    </Dark>
  );
};

/* ================================================= 6 · PROOF */
export const CreatorsOrbit: React.FC<{ offset: number; countEnd: number }> = ({ offset, countEnd }) => {
  const f = useCurrentFrame();
  const n = Math.round(interpolate(f, [4, countEnd], [0, 10], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const rings = ["#A855F7", "#3DFF8F", "#FFB938", "#60A5FA", "#F472B6"];
  return (
    <Dark>
      <div style={{ position: "absolute", top: 120, left: 0, right: 0, textAlign: "center" }}>
        <span style={{ fontFamily: inter, fontWeight: 900, fontSize: 250, color: C.green, letterSpacing: "-0.05em", textShadow: `0 0 50px rgba(61,255,143,0.6)` }}>{n}</span>
        <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 38, letterSpacing: "0.16em", color: "#fff", marginTop: -10 }}>CREATORS · MONTHLY PACKAGE</div>
      </div>
      <div style={{ position: "absolute", left: 540, top: 900 }}>
        <div style={{ position: "absolute", left: -330, top: -330, width: 660, height: 660, borderRadius: "50%", border: "2px dashed rgba(255,255,255,0.2)" }} />
        {Array.from({ length: 10 }, (_, i) => {
          const a = (i / 10) * Math.PI * 2 - Math.PI / 2 + f / 60;
          const show = i < n;
          const s = show ? interpolate(f, [4 + ((countEnd - 4) * i) / 10, 10 + ((countEnd - 4) * i) / 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) }) : 0;
          return (
            <div key={i} style={{ position: "absolute", left: Math.cos(a) * 330 - 58, top: Math.sin(a) * 330 - 58, width: 116, height: 116, borderRadius: "50%", background: "#1d1a24", border: `6px solid ${rings[i % 5]}`, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${s})` }}>
              <IUser size={58} color="#fff" />
            </div>
          );
        })}
      </div>
      <Mini x={540 - 170} y={900 - 170} w={340} h={340} r={170} offset={offset} delay={0} ring="rgba(168,85,247,0.95)" />
    </Dark>
  );
};

export const Slots: React.FC = () => {
  const f = useCurrentFrame();
  const badge = useSpring(2, { damping: 10, stiffness: 180 });
  return (
    <Dark glow="rgba(255,77,77,0.18)">
      <div style={{ position: "absolute", top: 170, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
        <div style={{ fontFamily: inter, fontWeight: 900, fontSize: 70, letterSpacing: "-0.03em", color: "#fff", background: C.red, borderRadius: 999, padding: "20px 48px", transform: `scale(${badge * (1 + Math.sin(f / 4) * 0.025)})`, boxShadow: "0 20px 60px rgba(255,77,77,0.45)" }}>ONLY 20 SLOTS LEFT</div>
      </div>
      <div style={{ position: "absolute", top: 380, left: 0, right: 0, display: "grid", gridTemplateColumns: "repeat(5, 150px)", gap: 24, justifyContent: "center" }}>
        {Array.from({ length: 30 }, (_, i) => {
          const s = interpolate(f, [i * 0.8, i * 0.8 + 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
          const taken = i < 10;
          const pulse = taken ? 0 : (Math.sin(f / 5 + i * 0.6) + 1) / 2;
          return (
            <div key={i} style={{ width: 150, height: 150, borderRadius: 28, transform: `scale(${s})`, display: "flex", alignItems: "center", justifyContent: "center",
              background: taken ? C.purple : "rgba(255,255,255,0.04)", border: taken ? "none" : `4px dashed rgba(61,255,143,${0.4 + 0.5 * pulse})`, boxShadow: taken ? "0 10px 30px rgba(124,58,237,0.4)" : `0 0 ${24 * pulse}px rgba(61,255,143,0.35)` }}>
              {taken ? <ICheck size={70} color="#fff" stroke={3.4} /> : <span style={{ fontFamily: mono, fontWeight: 700, fontSize: 28, color: C.green }}>OPEN</span>}
            </div>
          );
        })}
      </div>
    </Dark>
  );
};

/* ================================================= 7 · CTA */
export const CommentSheet: React.FC<{ typeF: number }> = ({ typeF }) => {
  const f = useCurrentFrame();
  const s = useSpring(0, { damping: 16, stiffness: 140 });
  const word = "EDIT";
  const n = Math.max(0, Math.min(4, Math.floor((f - typeF) / 2.5)));
  const sent = f > typeF + 14;
  const tap = interpolate(f, [typeF + 12, typeF + 16, typeF + 22], [1, 0.85, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top: 1040 + (1 - s) * 900, height: 560, borderRadius: 48, background: "#1c1c1e", boxShadow: "0 -20px 80px rgba(0,0,0,0.4)", padding: "26px 44px" }}>
      <div style={{ width: 90, height: 10, borderRadius: 5, background: "#48484a", margin: "0 auto 26px" }} />
      <div style={{ textAlign: "center", fontFamily: inter, fontWeight: 800, fontSize: 44, color: "#fff" }}>Comments</div>
      <div style={{ marginTop: 40, textAlign: "center", fontFamily: inter, fontWeight: 700, fontSize: 52, color: "#fff" }}>
        Comment <span style={{ color: C.purple }}>"EDIT"</span> to get the package
      </div>
      {sent && (
        <div style={{ marginTop: 30, display: "flex", alignItems: "center", gap: 20, opacity: ease(f, typeF + 14, typeF + 20) }}>
          <div style={{ width: 70, height: 70, borderRadius: "50%", background: "#e9e4ef", display: "flex", alignItems: "center", justifyContent: "center" }}><IUser size={40} color="#8a8292" /></div>
          <div style={{ fontFamily: inter, fontSize: 44, color: "#fff" }}><b>you</b> <span style={{ color: C.purple, fontWeight: 800 }}>EDIT</span></div>
        </div>
      )}
      <div style={{ position: "absolute", left: 44, right: 44, bottom: 40, display: "flex", alignItems: "center", gap: 20 }}>
        <div style={{ flex: 1, height: 100, borderRadius: 50, border: "3px solid #3a3a3c", display: "flex", alignItems: "center", padding: "0 34px", fontFamily: inter, fontWeight: 800, fontSize: 50, color: "#fff" }}>
          {sent ? <span style={{ color: "#aaa", fontWeight: 500 }}>Add a comment…</span> : <>{word.slice(0, n)}<span style={{ opacity: f % 12 < 6 ? 1 : 0, color: C.purple }}>|</span></>}
        </div>
        <div style={{ width: 100, height: 100, borderRadius: "50%", background: C.purple, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${tap})` }}><ISend size={50} color="#fff" /></div>
      </div>
    </div>
  );
};

export const DMBanner: React.FC = () => {
  const s = useSpring(0, { damping: 14, stiffness: 160 });
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top: 70 + (s - 1) * 300, height: 200, borderRadius: 44, background: "rgba(30,28,36,0.88)", backdropFilter: "blur(20px)", boxShadow: "0 30px 80px rgba(0,0,0,0.45)", display: "flex", alignItems: "center", gap: 28, padding: "0 36px" }}>
      <Avatar size={120} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: inter, fontWeight: 800, fontSize: 42, color: "#fff" }}><span>aminur_rex</span><span style={{ fontWeight: 500, fontSize: 32, color: "#aaa" }}>now</span></div>
        <div style={{ fontFamily: inter, fontWeight: 500, fontSize: 38, color: "#ddd", marginTop: 6 }}>Here's the full Monthly Editing Package 📩</div>
      </div>
    </div>
  );
};

const Avatar: React.FC<{ size: number; ring?: string }> = ({ size, ring }) => (
  <div style={{ width: size, height: size, borderRadius: "50%", overflow: "hidden", flexShrink: 0, background: "#C4F417", boxShadow: ring ? `0 0 0 6px ${ring}` : undefined }}>
    <Img src={staticFile("thumbs/avatar.png")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: "scale(1.05)" }} />
  </div>
);

/** Full-screen dark Instagram profile, matching @aminur_rex */
export const BioCard: React.FC<{ tapF: number; offset: number }> = ({ tapF, offset }) => {
  const f = useCurrentFrame();
  const s = useSpring(0, { damping: 16, stiffness: 150 });
  const cx = interpolate(f, [tapF - 20, tapF], [900, 520], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const cy = interpolate(f, [tapF - 20, tapF], [1180, 900], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const tapped = f >= tapF;
  const ripple = ease(f, tapF, tapF + 14);
  const hl = ease(f, 8, 18);
  const pulse = (Math.sin(f / 4) + 1) / 2;
  const grid = ["thumbs/me_14.jpg", "thumbs/vlog_street.jpg", "thumbs/city_night.jpg", "thumbs/me_43.jpg", "thumbs/podcast_man.jpg", "thumbs/coast_aerial.jpg"];
  const T = (st: React.CSSProperties, c: React.ReactNode) => <div style={{ fontFamily: inter, color: "#f5f5f5", ...st }}>{c}</div>;
  return (
    <AbsoluteFill style={{ background: "#0c0f14", transform: `translateY(${(1 - s) * 120}px)`, opacity: Math.min(1, s * 1.6) }}>
      {T({ position: "absolute", top: 150, left: 60, fontWeight: 800, fontSize: 56, letterSpacing: "-0.02em" }, "aminur_rex")}
      <div style={{ position: "absolute", top: 260, left: 60, right: 60, display: "flex", alignItems: "center", gap: 46 }}>
        <Avatar size={230} />
        <div style={{ flex: 1, display: "flex", justifyContent: "space-between" }}>
          {[["126", "posts"], ["2,554", "followers"], ["405", "following"]].map(([n, l]) => (
            <div key={l} style={{ textAlign: "center" }}>{T({ fontWeight: 800, fontSize: 54 }, n)}{T({ fontWeight: 500, fontSize: 34, color: "#c9c9c9" }, l)}</div>
          ))}
        </div>
      </div>
      <div style={{ position: "absolute", top: 530, left: 60, right: 60, lineHeight: 1.42 }}>
        {T({ fontWeight: 700, fontSize: 40 }, "Aminur Rahaman | Video Editor")}
        {T({ fontWeight: 500, fontSize: 38, color: "#a8a8a8" }, "Reel creator")}
        {T({ fontWeight: 500, fontSize: 38 }, "4+ Years of Video Editing 🎬")}
        {T({ fontWeight: 500, fontSize: 38 }, "1000+ Videos Delivered for Clients")}
        {T({ fontWeight: 500, fontSize: 38 }, "Helping Brands & Creators Stand Out")}
        <div style={{ position: "relative", marginTop: 4 }}>
          <div style={{ position: "absolute", left: -18, right: 40, top: -8, bottom: -8, borderRadius: 18, border: `4px solid rgba(61,255,143,${0.5 + 0.5 * pulse})`, boxShadow: `0 0 ${20 + 20 * pulse}px rgba(61,255,143,0.35)`, opacity: hl, transform: `scale(${0.96 + 0.04 * hl})` }} />
          {T({ fontWeight: 500, fontSize: 38 }, "📞 Book a call for…")}
          {T({ fontWeight: 700, fontSize: 38, color: tapped ? "#a5b8ff" : "#7d9bff" }, "🔗 superprofile.bio/bookings/graphicorev2")}
        </div>
      </div>
      <div style={{ position: "absolute", top: 990, left: 60, right: 60, display: "flex", gap: 16 }}>
        {["Follow", "Message", "Contact"].map((b, i) => (
          <div key={b} style={{ flex: 1, height: 90, borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: inter, fontWeight: 700, fontSize: 38,
            background: i === 0 ? "#0095F6" : "#262a31", color: "#fff", boxShadow: i === 2 ? `0 0 0 ${tapped ? 5 : 0}px rgba(61,255,143,0.7)` : "none" }}>{b}</div>
        ))}
      </div>
      <div style={{ position: "absolute", top: 1230, left: 0, right: 0, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6 }}>
        {grid.map((g, i) => <div key={i} style={{ height: 470, overflow: "hidden" }}><Img src={staticFile(g)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /></div>)}
      </div>
      <div style={{ position: "absolute", left: cx - 60, top: cy - 60, width: 120, height: 120, borderRadius: "50%", border: "4px solid rgba(255,255,255,0.8)", opacity: tapped ? 1 - ripple : 0, transform: `scale(${0.4 + ripple})` }} />
      <div style={{ position: "absolute", left: cx, top: cy, transform: `scale(${tapped && f < tapF + 4 ? 0.85 : 1})`, filter: "drop-shadow(0 6px 10px rgba(0,0,0,0.6))" }}><ICursor size={84} color="#fff" stroke={1.6} /></div>
      <Mini x={770} y={1300} w={250} h={250} r={125} offset={offset} delay={4} ring="#C4F417" />
    </AbsoluteFill>
  );
};

/* ================================================= 8 · KICKER: zoom out into an editor timeline */
export const EditorReveal: React.FC<{ offset: number; captionsHide: [number, number][] }> = ({ offset, captionsHide }) => {
  const f = useCurrentFrame();
  const p = ease(f, 0, 14);
  const sc = 1 - 0.46 * p;
  const tl = ease(f, 6, 18);
  const tot = SUBS[SUBS.length - 1].oEnd;
  const t = (f + offset) / FPS;
  const tag = ease(f, 16, 26);
  return (
    <AbsoluteFill style={{ background: "#0f0d13" }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 90, background: "#17141c", display: "flex", alignItems: "center", gap: 14, padding: "0 30px", opacity: p }}>
        {["#ff5f57", "#febc2e", "#28c840"].map((c) => <div key={c} style={{ width: 22, height: 22, borderRadius: "50%", background: c }} />)}
        <div style={{ marginLeft: 20, fontFamily: mono, fontWeight: 500, fontSize: 28, color: "#9c94a6" }}>monthly-package-reel · Edit</div>
      </div>
      <div style={{ position: "absolute", left: 540 - 540 * sc, top: 110 * p, width: 1080, height: 1920, transform: `scale(${sc})`, transformOrigin: "0 0", borderRadius: 30 / sc * p, overflow: "hidden", boxShadow: p > 0.1 ? "0 0 0 4px #2a2533" : "none" }}>
        <Talking muted offset={offset} />
        {SCN.minimal ? <Captions4 hide={captionsHide} offset={offset} /> : <Captions2 hide={captionsHide} offset={offset} />}
      </div>
      <div style={{ position: "absolute", left: 30, right: 30, top: 1180, height: 600, opacity: tl, transform: `translateY(${(1 - tl) * 120}px)` }}>
        {[{ n: "V2", c: "#8a6a2a" }, { n: "V1", c: "#6a4a7e" }, { n: "A1", c: "#2f6b55" }, { n: "A2", c: "#2e5a7a" }].map((tr, k) => (
          <div key={tr.n} style={{ display: "flex", alignItems: "center", gap: 14, height: 92, marginBottom: 14 }}>
            <div style={{ width: 70, fontFamily: mono, fontWeight: 700, fontSize: 28, color: "#9c94a6" }}>{tr.n}</div>
            <div style={{ position: "relative", flex: 1, height: 80, background: "#1a1720", borderRadius: 10 }}>
              {SUBS.filter((_, i) => (k === 1 ? true : k === 0 ? i % 3 === 0 : k === 3 ? i % 2 === 1 : true)).map((sb, i) => (
                <div key={i} style={{ position: "absolute", top: 6, bottom: 6, left: `${(sb.oStart / tot) * 100}%`, width: `${Math.max(0.6, ((sb.oEnd - sb.oStart) / tot) * 100 - 0.3)}%`, background: tr.c, borderRadius: 6, opacity: 0.95 }} />
              ))}
            </div>
          </div>
        ))}
        <div style={{ position: "absolute", top: -10, bottom: 60, left: `calc(84px + (100% - 84px) * ${t / tot})`, width: 4, background: C.red }} />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 1700, textAlign: "center", fontFamily: inter, fontWeight: 900, fontSize: 64, letterSpacing: "-0.03em", color: "#fff", opacity: tag, transform: `translateY(${(1 - tag) * 30}px)` }}>
        Edited by <span style={{ color: C.purple }}>Aminur Rex Team</span>
      </div>
    </AbsoluteFill>
  );
};
