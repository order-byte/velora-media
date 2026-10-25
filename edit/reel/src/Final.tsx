import React from "react";
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, interpolate, Easing } from "remotion";
import { inter, serif, ICam, IScissors, ICheck, IX, IUser, ISend, IMic, IFilm, IBolt, ITrend, IHeart, ICursor, IPhone, IMail } from "./lib";
import META from "./sfx-meta.json";
import TRACK from "./track.json";

/* =============================== timing (seconds, from the cut's transcript) */
export const FINAL_DUR = 65.0;
const F = 30;
const fr = (s: number) => Math.round(s * F);
const EX = Easing.bezier(0.16, 1, 0.3, 1);
const IO = Easing.bezier(0.65, 0, 0.35, 1);
const k = (f: number, a: number, b: number, e = EX) => interpolate(f, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: e });
const Seq: React.FC<{ a: number; b: number; children: React.ReactNode; name?: string }> = ({ a, b, children, name }) => (
  <Sequence from={fr(a)} durationInFrames={Math.max(1, fr(b) - fr(a))} name={name} layout="absolute-fill">{children}</Sequence>
);
const LIME = "#C8F31E";
const INK = "#121212";

/* =============================== camera: smooth tracked moves + parallax */
type Key = [number, number, number, number]; // t, scale, x, y  (subject space)
const CAM_RAW: Key[] = [
  [0, 1.28, 0, -40], [1.35, 1.36, -10, -60], [1.45, 1.46, -20, -90], [4.1, 1.5, -20, -100],
  [8.4, 1.22, 0, -20], [10.4, 1.3, 10, -40], [12.0, 1.44, 0, -90], [13.4, 1.48, 0, -100],
  [17.3, 1.2, 0, -10], [17.45, 1.34, -30, -60], [20.5, 1.42, -30, -80],
  [20.6, 1.26, 0, -30], [23.5, 1.34, 0, -50],
  [32.0, 1.24, 0, -20], [33.9, 1.32, 0, -50], [34.0, 1.18, 40, 0], [38.6, 1.26, 40, -20],
  [38.7, 1.34, 0, -60], [41.3, 1.4, 0, -80],
  [41.4, 1.2, 0, 0], [44.7, 1.28, 0, -30], [44.8, 1.36, -10, -70], [46.0, 1.42, -10, -90],
  [47.5, 1.2, 0, 0], [51.5, 1.3, 0, -30], [51.6, 1.36, 0, -60], [54.0, 1.4, 0, -70], [54.1, 1.5, -10, -110], [55.8, 1.56, -10, -120],
  [55.9, 1.24, 0, -20], [59.0, 1.3, 0, -40],
  [62.2, 1.2, 0, -10], [62.27, 1.12, 0, 30], [65, 1.2, 0, 0],
];
// zoom keyframes (scale only); position comes from the face-tracking camera below
const CAM: Key[] = CAM_RAW.map(([t, sc]) => [t, 1.12 + (sc - 1.2) * 0.5, 0, 0]);
const camAt = (t: number) => {
  let i = CAM.findIndex((c) => c[0] > t); if (i === -1) i = CAM.length; const a = CAM[Math.max(0, i - 1)], b = CAM[Math.min(CAM.length - 1, i)];
  if (a === b) return a;
  const p = interpolate(t, [a[0], b[0]], [0, 1], { easing: b[0] - a[0] < 0.2 ? EX : IO, extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return [t, a[1] + (b[1] - a[1]) * p, 0, 0] as Key;
};
/* CapCut-style camera tracking: the frame follows the face (face stays locked), with a little handheld life.
   TRACK = smoothed face position per frame + that shot's rest position. The set moves a bit less (parallax). */
const LOCK = 0.9;
const camStyle = (frame: number, depth = 1): React.CSSProperties => {
  const t = frame / F;
  const [fx, fy, f0x, f0y] = (TRACK as number[][])[Math.min(TRACK.length - 1, Math.max(0, frame))];
  const s = camAt(t)[1];
  const TAU = Math.PI * 2;
  let tx = LOCK * (f0x - fx) + 5 * Math.sin(TAU * 0.23 * t) + 3 * Math.sin(TAU * 0.61 * t + 1.3);
  let ty = LOCK * (f0y - fy) + 4 * Math.sin(TAU * 0.19 * t + 0.7) + 2.5 * Math.sin(TAU * 0.53 * t + 2.1);
  const rot = 0.3 * Math.sin(TAU * 0.17 * t + 0.4);
  const m = 14; // keep the frame edges covered
  tx = Math.max(-(1080 - fx) * (s - 1) + m, Math.min(fx * (s - 1) - m, tx));
  ty = Math.max(-(1920 - fy) * (s - 1) + m, Math.min(fy * (s - 1) - m, ty));
  const sd = 1 + (s - 1) * depth;
  return { transformOrigin: `${fx}px ${fy}px`, transform: `translate(${tx * depth}px, ${ty * depth}px) rotate(${rot * depth}deg) scale(${sd})` };
};

/* =============================== layers (natural colour: no grade, the creator grades it) */
const Plate: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#0d1a10" }}>
      <AbsoluteFill style={camStyle(f, 0.8)}>
        <Img src={staticFile("plate4.png")} style={{ width: 1080, height: 1920 }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
const Subject: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill style={camStyle(f, 1)}>
        <OffthreadVideo src={staticFile("subject_raw.webm")} transparent muted style={{ width: 1080, height: 1920 }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* =============================== big words behind the subject (ref: text-behind-person) */
type Big = { t: number; e: number; text: string; sub?: string; y?: number; size?: number; font?: "sans" | "serif"; color?: string; glitch?: boolean; box?: boolean };
const BIGS: Big[] = [
  { t: 0.38, e: 1.36, text: "20", sub: "creators", y: 170, size: 420, color: "#fff" },
  { t: 1.4, e: 2.55, text: "$200", y: 230, size: 330, color: LIME },
  { t: 3.55, e: 4.15, text: "editing", y: 250, size: 260, font: "serif", color: "#fff" },
  { t: 8.95, e: 10.5, text: "POST?", y: 230, size: 280, color: "#fff" },
  { t: 10.85, e: 12.0, text: "GROWTH", sub: "slow ↓", y: 250, size: 230, color: "#fff" },
  { t: 12.05, e: 13.45, text: "BURNOUT", y: 260, size: 210, color: "#FF4B4B", glitch: true },
  { t: 17.95, e: 18.75, text: "SHOOT", y: 250, size: 250, color: "#fff" },
  { t: 19.35, e: 20.55, text: "humara", sub: "kaam", y: 230, size: 230, font: "serif", color: "#fff" },
  { t: 20.85, e: 21.75, text: "STYLE?", y: 250, size: 250, color: LIME },
  { t: 22.35, e: 23.6, text: "TRENDING", y: 270, size: 180, color: "#fff" },
  { t: 32.35, e: 33.05, text: "CONTENT", y: 260, size: 190, color: "#fff" },
  { t: 33.35, e: 33.95, text: "style", y: 230, size: 280, font: "serif", color: LIME },
  { t: 39.35, e: 41.3, text: "SCROLL", sub: "stop", y: 230, size: 240, color: "#fff" },
  { t: 44.15, e: 44.75, text: "KHATAM", y: 260, size: 200, color: "#FF4B4B" },
  { t: 45.65, e: 46.0, text: "editing", y: 250, size: 250, font: "serif", color: "#fff" },
  { t: 46.55, e: 47.5, text: "$200", sub: "per month", y: 210, size: 330, color: LIME, box: true },
  { t: 47.95, e: 49.05, text: "10", sub: "creators", y: 170, size: 420, color: "#fff" },
  { t: 52.15, e: 53.95, text: "20", sub: "slots left", y: 170, size: 420, color: LIME },
  { t: 54.95, e: 55.8, text: "FIRST", sub: "serve", y: 250, size: 260, color: "#fff" },
  { t: 63.75, e: 65.0, text: "humne", sub: "yeh video bhi", y: 230, size: 250, font: "serif", color: "#fff" },
];
const BigWord: React.FC<{ b: Big }> = ({ b }) => {
  const f = useCurrentFrame(); const d = fr(b.e - b.t);
  const a = k(f, 0, 9); const out = k(f, d - 5, d, Easing.in(Easing.cubic));
  const sub = k(f, 5, 14);
  const gl = b.glitch && f < 8 ? (f % 2 ? 14 : -14) : 0;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 150, textAlign: "center", opacity: a * (1 - out), filter: `blur(${(1 - a) * 18 + out * 14}px)`, transform: `translateY(${(1 - a) * 40 - out * 30}px) scale(${1.08 - 0.08 * a})` }}>
      <div style={{ height: 110, fontFamily: serif, fontStyle: "italic", fontSize: 104, lineHeight: "110px", color: "#fff", opacity: b.sub ? sub : 0, filter: `blur(${(1 - sub) * 10}px)`, textShadow: "0 6px 30px rgba(0,0,0,0.35)" }}>{b.sub ?? ""}</div>
      <div style={{ position: "relative", display: "inline-block" }}>
        {b.box && <div style={{ position: "absolute", left: -30, right: -30, top: "16%", bottom: "8%", background: "rgba(18,18,18,0.92)", borderRadius: 30, transform: `scaleX(${k(f, 2, 12, IO)})`, transformOrigin: "left" }} />}
        <span style={{ position: "relative", fontFamily: b.font === "serif" ? serif : inter, fontStyle: b.font === "serif" ? "italic" : "normal", fontWeight: b.font === "serif" ? 400 : 900,
          fontSize: b.size ?? 240, lineHeight: 0.92, letterSpacing: b.font === "serif" ? "-0.02em" : "-0.055em", color: b.color ?? "#fff", whiteSpace: "nowrap",
          textShadow: gl ? `${gl}px 0 rgba(0,255,255,0.7), ${-gl}px 0 rgba(255,0,80,0.8)` : "0 10px 50px rgba(0,0,0,0.25)" }}>{b.text}</span>
      </div>
    </div>
  );
};

/* =============================== small kinetic captions in front (ref 1) */
type Wd = [string, number];
const CAPS: Wd[][] = [
  [["Sirf", 0.0], ["20", 0.4], ["creators,", 0.7]], [["$200,", 1.4]], [["aur", 2.6], ["poore", 2.8], ["mahine", 3.0], ["ki", 3.4], ["editing.", 3.6]],
  [["Shoot", 4.2], ["karte", 4.5], ["ho", 4.9], ["10", 5.3], ["minute,", 5.5]], [["edit", 5.9], ["karte", 6.3], ["ho,", 6.7]], [["poori", 7.0], ["raat", 7.2], ["chali", 7.4], ["jaati", 7.7], ["hai.", 8.0]],
  [["Consistently", 8.5], ["post", 9.0], ["nahi", 9.4], ["kar", 9.6], ["paate", 9.8], ["ho,", 10.2]], [["aur", 10.6], ["growth", 10.65], ["slow", 10.9], ["ho", 11.2], ["jaata", 11.4], ["hai,", 11.7]],
  [["aur", 12.0], ["burnout", 12.1], ["full", 12.6], ["ho", 12.8], ["jaata", 12.9], ["hai.", 13.2]],
  [["Isliye", 13.5], ["Aminur", 13.9], ["Rex", 14.3], ["Team", 14.6], ["laaya", 14.8], ["hai", 15.1]], [["Monthly", 15.3], ["Editing", 16.2], ["Package.", 16.6]],
  [["Tum", 17.4], ["sirf", 17.6], ["shoot", 18.0], ["karo,", 18.3]], [["baaki", 18.8], ["sab", 19.2], ["humara", 19.4], ["kaam.", 20.2]],
  [["Aur", 20.6], ["style?", 20.9]], [["Jo", 21.8], ["abhi", 22.0], ["trend", 22.4], ["kar", 22.6], ["raha", 23.0], ["hai,", 23.4], ["sab —", 23.6]],
  [["Talking", 23.9], ["head,", 24.4]], [["Podcast", 25.1], ["clips,", 25.4]], [["Documentary", 26.7], ["style,", 27.0]], [["Cinematic", 28.1], ["vlog,", 28.4]], [["Motion", 29.5], ["graphics,", 29.7]], [["Faceless", 30.9], ["story.", 31.4]],
  [["Tumhara", 32.1], ["content,", 32.4], ["tumhara", 33.1], ["style.", 33.4]],
  [["Sirf", 34.1], ["yeh", 34.4], ["bata", 34.6], ["do", 34.7], ["ki", 35.0]], [["YouTube", 35.1], ["video", 35.4], ["chahiye,", 35.7], ["ya", 36.2], ["Shorts,", 36.4]], [["ya", 37.0], ["YouTube", 37.05], ["Shorts", 37.5], ["dono", 37.8], ["chahiye.", 38.1]],
  [["Hum", 38.7], ["bas", 38.9], ["usse", 39.1], ["scroll", 39.4], ["stopping", 39.8], ["bana", 40.5], ["dete", 40.8], ["hain.", 41.1]],
  [["Har", 41.4], ["reel", 41.7], ["ke", 41.9], ["liye", 42.1], ["alag", 42.4], ["pay", 42.8]], [["karne", 43.1], ["ka", 43.4], ["jhanjhat", 43.6], ["bhi", 44.1], ["khatam", 44.2], ["ho", 44.5], ["gaya.", 44.6]],
  [["Poore", 44.8], ["mahine", 45.1], ["ki", 45.5], ["editing,", 45.7]], [["sirf", 46.0], ["$200.", 46.6]],
  [["Abhi", 47.6], ["10", 48.0], ["creators", 48.3]], [["humare", 49.1], ["saath", 49.5], ["monthly", 49.8], ["package", 50.1], ["pe", 50.4]], [["kaam", 50.7], ["kar", 50.9], ["rahe", 51.1], ["hain.", 51.4]],
  [["Aur", 51.6], ["bas", 51.8], ["20", 52.2], ["slots", 52.7], ["bache", 53.3], ["hain —", 53.7]], [["first", 54.1], ["come,", 54.4], ["first", 55.0], ["serve.", 55.3]],
  [["Comment", 55.9], ["karo", 56.2], ["“EDIT”", 56.6]], [["DM", 57.2], ["mein", 57.5], ["saari", 57.6], ["information", 57.9], ["bhej", 58.3], ["denge.", 58.7]],
  [["Ya", 59.1], ["seedha", 59.2], ["bio", 59.7], ["mein", 60.0], ["check", 60.2], ["karo,", 60.4]], [["wahan", 60.9], ["pe", 61.0], ["contact", 61.2], ["number", 61.6], ["hai.", 61.9]],
  [["Aur", 62.3], ["haan,", 62.4]], [["yeh", 63.0], ["video", 63.3], ["bhi", 63.5], ["humne", 63.8], ["hi", 64.1], ["edit", 64.2], ["kiya", 64.4], ["hai.", 64.7]],
];
const PHR = CAPS.map((ws, i) => ({ ws, s: ws[0][1], e: CAPS[i + 1] ? Math.min(CAPS[i + 1][0][1] - 0.02, ws[ws.length - 1][1] + 0.9) : FINAL_DUR }));
const HL = /^(\$?\d+[,.]?|“EDIT”|creators,?|editing[,.]?|burnout|shoot|style[?.,]?|content,?|stopping|khatam|slots|serve\.|bio|humne)$/i;
const Captions: React.FC<{ hide: [number, number][] }> = ({ hide }) => {
  const f = useCurrentFrame(); const t = f / F;
  if (hide.some(([a, b]) => t >= a && t < b)) return null;
  const p = PHR.find((x) => t >= x.s - 0.04 && t < x.e); if (!p) return null;
  return (
    <div style={{ position: "absolute", left: 70, right: 70, top: 1250, textAlign: "center" }}>
      {p.ws.map(([w, s], i) => {
        const a = interpolate(t, [s - 0.04, s + 0.14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EX });
        const hl = HL.test(w);
        return (
          <span key={i} style={{ display: "inline-block", margin: "0 10px", fontFamily: inter, fontWeight: hl ? 800 : 600, fontSize: 58, letterSpacing: "-0.02em",
            color: hl ? LIME : "#fff", opacity: a, filter: `blur(${(1 - a) * 10}px)`, transform: `translateY(${(1 - a) * 14}px)`, textShadow: "0 3px 16px rgba(0,0,0,0.55)" }}>{w}</span>
        );
      })}
    </div>
  );
};

/* =============================== motion-graphics scenes (light, Apple-like; refs: Built-to-Break / Google / Drive) */
const Light: React.FC<{ children?: React.ReactNode; dur: number }> = ({ children, dur }) => {
  const f = useCurrentFrame(); const a = k(f, 0, 8); const o = k(f, dur - 6, dur, Easing.in(Easing.cubic));
  return (
    <AbsoluteFill style={{ background: "radial-gradient(120% 80% at 50% 40%, #FFFFFF 0%, #F2F3F5 70%, #E9EBEE 100%)", opacity: Math.min(1, a * 1.5) * (1 - o * 0.85), transform: `scale(${1.06 - 0.06 * a + o * 0.08})`, filter: a < 0.98 || o > 0 ? `blur(${(1 - a) * 18 + o * 16}px)` : undefined }}>
      {children}
    </AbsoluteFill>
  );
};
const Word: React.FC<{ text: string; at: number; style?: React.CSSProperties }> = ({ text, at, style }) => {
  const f = useCurrentFrame(); const a = k(f, at, at + 9);
  return <span style={{ display: "inline-block", opacity: a, filter: `blur(${(1 - a) * 12}px)`, transform: `translateY(${(1 - a) * 18}px)`, ...style }}>{text}</span>;
};
const Ring: React.FC<{ p: number; color: string; size?: number }> = ({ p, color, size = 92 }) => {
  const r = 20, c = 2 * Math.PI * r;
  return <svg width={size} height={size} viewBox="0 0 48 48"><circle cx="24" cy="24" r={r} stroke="rgba(0,0,0,0.08)" strokeWidth="6" fill="none" /><circle cx="24" cy="24" r={r} stroke={color} strokeWidth="6" fill="none" strokeDasharray={c} strokeDashoffset={c * (1 - p)} strokeLinecap="round" transform="rotate(-90 24 24)" /></svg>;
};
const TimerPill: React.FC<{ at: number; icon: React.ReactNode; label: string; value: (p: number) => string; color: string; dur: number }> = ({ at, icon, label, value, color, dur }) => {
  const f = useCurrentFrame(); const a = k(f, at, at + 10); const p = k(f, at + 4, at + 4 + dur, IO);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 26, padding: "22px 40px 22px 24px", borderRadius: 999, background: "#1b1b1d", boxShadow: "0 30px 70px rgba(0,0,0,0.18)", opacity: a, filter: `blur(${(1 - a) * 10}px)`, transform: `translateY(${(1 - a) * 30}px) scale(${0.94 + 0.06 * a})` }}>
      <div style={{ position: "relative", width: 92, height: 92 }}><Ring p={p} color={color} /><div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>{icon}</div></div>
      <div>
        <div style={{ fontFamily: inter, fontWeight: 800, fontSize: 64, color: "#fff", letterSpacing: "-0.03em", lineHeight: 1 }}>{value(p)}</div>
        <div style={{ fontFamily: inter, fontWeight: 500, fontSize: 30, color: "rgba(255,255,255,0.6)", marginTop: 6 }}>{label}</div>
      </div>
    </div>
  );
};
/* 4.2–8.4: shoot 10 min vs edit all night */
const ShootVsEdit: React.FC<{ dur: number }> = ({ dur }) => {
  const editAt = fr(5.9 - 4.15), nightAt = fr(7.0 - 4.15);
  return (
    <Light dur={dur}>
      <div style={{ position: "absolute", top: 560, left: 0, right: 0, textAlign: "center", fontFamily: inter, fontWeight: 800, fontSize: 104, color: INK, letterSpacing: "-0.04em" }}>
        <Word text="Shoot" at={0} /> <Word text="vs" at={editAt - 6} style={{ color: "#9a9a9a", fontFamily: serif, fontStyle: "italic", fontWeight: 400, fontSize: 120 }} /> <Word text="Edit" at={editAt} />
      </div>
      <div style={{ position: "absolute", top: 820, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 120, transform: "scale(1.55)", transformOrigin: "50% 0" }}>
        <TimerPill at={3} icon={<ICam size={40} color="#fff" />} label="shoot" color="#3DDC84" dur={18} value={(p) => `${Math.round(p * 10)} min`} />
        <TimerPill at={editAt} icon={<IScissors size={40} color="#fff" />} label={"edit · poori raat"} color="#FF4B4B" dur={nightAt - editAt + 22} value={(p) => `${Math.round(p * 12)}h`} />
      </div>
    </Light>
  );
};
/* 13.5–17.3: Google-style search → Aminur Rex Team → Monthly Editing Package */
const SearchScene: React.FC<{ dur: number }> = ({ dur }) => {
  const f = useCurrentFrame();
  const q = "best video editor for creators";
  const n = Math.max(0, Math.min(q.length, Math.floor((f - 4) * 1.6)));
  const res = k(f, fr(13.9 - 13.45), fr(13.9 - 13.45) + 10);
  const pkg = k(f, fr(15.3 - 13.45), fr(15.3 - 13.45) + 10);
  const hl = k(f, fr(16.2 - 13.45), fr(16.2 - 13.45) + 12, IO);
  return (
    <Light dur={dur}>
      <div style={{ position: "absolute", top: 520, left: 70, right: 70, height: 140, borderRadius: 70, background: "#fff", boxShadow: "0 18px 50px rgba(0,0,0,0.10), 0 0 0 2px rgba(0,0,0,0.04)", display: "flex", alignItems: "center", padding: "0 40px", gap: 24 }}>
        <svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#888" strokeWidth="2.4"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>
        <span style={{ fontFamily: inter, fontWeight: 500, fontSize: 50, color: INK }}>{q.slice(0, n)}<span style={{ opacity: f % 14 < 7 ? 1 : 0, color: "#3b82f6" }}>|</span></span>
      </div>
      <div style={{ position: "absolute", top: 720, left: 70, right: 70, borderRadius: 40, background: "#fff", boxShadow: "0 30px 80px rgba(0,0,0,0.12)", padding: 40, opacity: res, filter: `blur(${(1 - res) * 12}px)`, transform: `translateY(${(1 - res) * 40}px)` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          <div style={{ width: 130, height: 130, borderRadius: "50%", overflow: "hidden", background: LIME }}><Img src={staticFile("thumbs/avatar.png")} style={{ width: "100%", height: "100%", objectFit: "cover" }} /></div>
          <div>
            <div style={{ fontFamily: inter, fontWeight: 800, fontSize: 60, color: INK, letterSpacing: "-0.03em" }}>Aminur Rex Team</div>
            <div style={{ fontFamily: inter, fontWeight: 500, fontSize: 32, color: "#1a73e8" }}>@aminur_rex · Video editing for creators</div>
          </div>
        </div>
      </div>
      <div style={{ position: "absolute", top: 1010, left: 0, right: 0, textAlign: "center", opacity: pkg, filter: `blur(${(1 - pkg) * 12}px)`, transform: `translateY(${(1 - pkg) * 30}px)` }}>
        <div style={{ fontFamily: serif, fontStyle: "italic", fontSize: 150, lineHeight: 1, color: INK, letterSpacing: "-0.02em" }}>Monthly Editing</div>
        <div style={{ position: "relative", display: "inline-block", marginTop: 10 }}>
          <div style={{ position: "absolute", left: -24, right: -24, top: 18, bottom: 4, background: LIME, borderRadius: 18, transform: `scaleX(${hl})`, transformOrigin: "left" }} />
          <span style={{ position: "relative", fontFamily: inter, fontWeight: 900, fontSize: 150, lineHeight: 1.05, color: INK, letterSpacing: "-0.05em" }}>PACKAGE</span>
        </div>
      </div>
      <div style={{ position: "absolute", left: 860, top: 860, transform: `translate(${(1 - res) * 120}px, ${(1 - res) * 80}px)`, opacity: res, filter: "drop-shadow(0 6px 10px rgba(0,0,0,0.25))" }}><ICursor size={70} color="#111" stroke={1.4} /></div>
    </Light>
  );
};
/* 23.6–32.0: style folder with cursor + preview sticker (ref: Drive list) */
const STYLES: { name: string; t: number; icon: React.ReactNode; thumb: string }[] = [
  { name: "Talking head", t: 23.9, icon: <IUser size={40} color="#5f6368" />, thumb: "thumbs/me_21.jpg" },
  { name: "Podcast clips", t: 25.1, icon: <IMic size={40} color="#5f6368" />, thumb: "thumbs/podcast_man.jpg" },
  { name: "Documentary", t: 26.7, icon: <IFilm size={40} color="#5f6368" />, thumb: "thumbs/city_night.jpg" },
  { name: "Cinematic vlog", t: 28.1, icon: <IHeart size={40} color="#5f6368" />, thumb: "thumbs/vlog_street.jpg" },
  { name: "Motion graphics", t: 29.5, icon: <IBolt size={40} color="#5f6368" />, thumb: "thumbs/coast_aerial.jpg" },
  { name: "Faceless story", t: 30.9, icon: <ITrend size={40} color="#5f6368" />, thumb: "thumbs/hands_typing.jpg" },
];
const StyleFolder: React.FC<{ dur: number; t0: number }> = ({ dur, t0 }) => {
  const f = useCurrentFrame(); const t = t0 + f / F;
  const card = k(f, 0, 12);
  let sel = -1; STYLES.forEach((s, i) => { if (t >= s.t - 0.05) sel = i; });
  const rowY = (i: number) => 330 + i * 118;
  const cy = sel < 0 ? rowY(0) - 60 : rowY(sel) + 40;
  const prevCy = sel <= 0 ? rowY(0) - 60 : rowY(sel - 1) + 40;
  const moveP = sel < 0 ? 0 : k(f, fr(STYLES[sel].t - 0.05 - t0), fr(STYLES[sel].t - 0.05 - t0) + 8, IO);
  const cursorY = prevCy + (cy - prevCy) * moveP;
  return (
    <Light dur={dur}>
      <div style={{ position: "absolute", top: 160, left: 0, right: 0, textAlign: "center", fontFamily: inter, fontWeight: 700, fontSize: 60, color: INK, letterSpacing: "-0.03em", opacity: card }}>Jo abhi <span style={{ fontFamily: serif, fontStyle: "italic", fontWeight: 400, fontSize: 84 }}>trend</span> kar raha hai</div>
      <div style={{ position: "absolute", left: 110, right: 110, top: 270, borderRadius: 44, background: "#fff", boxShadow: "0 40px 100px rgba(0,0,0,0.12)", padding: "30px 0", opacity: card, transform: `translateY(${(1 - card) * 60}px)`, filter: `blur(${(1 - card) * 12}px)` }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 40px 18px", fontFamily: inter, fontWeight: 600, fontSize: 40, color: "#9aa0a6" }}>
          <span>Styles</span><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#9aa0a6" strokeWidth="2.4"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>
        </div>
        {STYLES.map((s, i) => {
          const on = i === sel; const vis = k(f, 4 + i * 3, 12 + i * 3);
          return (
            <div key={s.name} style={{ display: "flex", alignItems: "center", gap: 26, height: 118, padding: "0 40px", background: on ? "rgba(26,115,232,0.12)" : "transparent", opacity: vis, transition: "none" }}>
              <div style={{ width: 66, height: 66, borderRadius: 16, background: on ? "#1a73e8" : "#f1f3f4", display: "flex", alignItems: "center", justifyContent: "center" }}>{on ? React.cloneElement(s.icon as React.ReactElement, { color: "#fff" }) : s.icon}</div>
              <span style={{ fontFamily: inter, fontWeight: on ? 700 : 500, fontSize: 50, color: on ? "#1a73e8" : INK }}>{s.name}</span>
            </div>
          );
        })}
      </div>
      {sel >= 0 && (() => {
        const s = STYLES[sel]; const p = k(f, fr(s.t - t0), fr(s.t - t0) + 10);
        return (
          <div key={sel} style={{ position: "absolute", left: 600, top: 1110, width: 330, height: 520, borderRadius: 32, overflow: "hidden", border: "8px solid #fff", boxShadow: "0 30px 70px rgba(0,0,0,0.25)", transform: `rotate(${4 - 2 * p}deg) scale(${0.85 + 0.15 * p})`, opacity: p }}>
            <Img src={staticFile(s.thumb)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          </div>
        );
      })()}
      <div style={{ position: "absolute", left: 760, top: cursorY, filter: "drop-shadow(0 6px 10px rgba(0,0,0,0.25))", opacity: card }}><ICursor size={70} color="#111" stroke={1.4} /></div>
    </Light>
  );
};

/* stickers around the subject (refs: floating glossy chips / photo stickers) */
const Sticker: React.FC<{ at: number; x: number; y: number; rot?: number; children: React.ReactNode; out?: number }> = ({ at, x, y, rot = 0, children, out }) => {
  const f = useCurrentFrame(); const a = k(f, at, at + 10); const o = out ? k(f, out, out + 6, Easing.in(Easing.cubic)) : 0;
  const float = Math.sin((f - at) / 18) * 6;
  return <div style={{ position: "absolute", left: x, top: y + float, opacity: a * (1 - o), transform: `rotate(${rot * a}deg) scale(${(0.7 + 0.3 * a) * (1 - o * 0.2)})`, filter: a < 0.98 ? `blur(${(1 - a) * 10}px)` : undefined }}>{children}</div>;
};
const Chip: React.FC<{ children: React.ReactNode; bg?: string; color?: string; size?: number }> = ({ children, bg = "#fff", color = INK, size = 44 }) => (
  <div style={{ display: "inline-flex", alignItems: "center", gap: 16, padding: `${size * 0.42}px ${size * 0.7}px`, borderRadius: 26, background: bg, color, fontFamily: inter, fontWeight: 800, fontSize: size, letterSpacing: "-0.02em",
    boxShadow: "0 24px 50px rgba(0,0,0,0.28), inset 0 2px 0 rgba(255,255,255,0.6)" }}>{children}</div>
);
const PlayIcon: React.FC<{ s?: number }> = ({ s = 54 }) => (
  <div style={{ width: s * 1.4, height: s, borderRadius: s * 0.28, background: "linear-gradient(180deg,#ff4d4d,#d91c1c)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "inset 0 2px 0 rgba(255,255,255,0.4)" }}>
    <div style={{ width: 0, height: 0, borderLeft: `${s * 0.36}px solid #fff`, borderTop: `${s * 0.22}px solid transparent`, borderBottom: `${s * 0.22}px solid transparent`, marginLeft: s * 0.06 }} />
  </div>
);
const FormatChips: React.FC = () => {
  const o = (t: number) => fr(t - 34.0);
  return (
    <>
      <Sticker at={o(35.1)} x={50} y={250} rot={-6}><Chip><PlayIcon /> YouTube</Chip></Sticker>
      <Sticker at={o(36.4)} x={650} y={330} rot={5}><Chip bg="#111" color="#fff"><span style={{ width: 40, height: 52, borderRadius: 10, border: "5px solid #fff", display: "inline-block" }} /> Shorts</Chip></Sticker>
      <Sticker at={o(37.8)} x={380} y={120} rot={-2}><Chip bg={LIME}>Dono ✓</Chip></Sticker>
    </>
  );
};
const Invoices: React.FC = () => {
  const f = useCurrentFrame(); const o = (t: number) => fr(t - 41.35);
  const cross = (t: number) => k(f, o(t), o(t) + 6, IO);
  const inv = (i: number, x: number, y: number, rot: number, at: number) => (
    <Sticker key={i} at={o(at)} x={x} y={y} rot={rot} out={o(44.45)}>
      <div style={{ position: "relative", width: 300, borderRadius: 22, background: "#fff", padding: "22px 26px", boxShadow: "0 24px 50px rgba(0,0,0,0.3)" }}>
        <div style={{ fontFamily: inter, fontWeight: 600, fontSize: 22, color: "#999", letterSpacing: "0.1em" }}>INVOICE #{String(i).padStart(3, "0")}</div>
        <div style={{ fontFamily: inter, fontWeight: 800, fontSize: 40, color: INK, marginTop: 6 }}>Reel {String(i).padStart(2, "0")}</div>
        <div style={{ fontFamily: inter, fontWeight: 700, fontSize: 22, color: "#FF4B4B", marginTop: 6 }}>PAYMENT DUE</div>
        <svg width="300" height="160" viewBox="0 0 300 160" style={{ position: "absolute", left: 0, top: 0 }}>
          <path d="M40 30 L260 130" stroke="#FF4B4B" strokeWidth="12" strokeLinecap="round" strokeDasharray="250" strokeDashoffset={250 * (1 - cross(44.15))} />
          <path d="M260 30 L40 130" stroke="#FF4B4B" strokeWidth="12" strokeLinecap="round" strokeDasharray="250" strokeDashoffset={250 * (1 - cross(44.25))} />
        </svg>
      </div>
    </Sticker>
  );
  return <>{inv(1, 60, 470, -8, 41.7)}{inv(2, 700, 560, 7, 42.4)}{inv(3, 80, 820, 5, 42.8)}{inv(4, 690, 900, -6, 43.6)}</>;
};
const CreatorStickers: React.FC = () => {
  const o = (t: number) => fr(t - 47.55);
  const pos: [number, number, number][] = [[60, 420, -6], [820, 450, 6], [40, 760, 4], [860, 800, -5], [120, 1060, -3], [800, 1120, 5], [260, 330, 3], [640, 330, -4], [30, 1380, 6], [880, 1400, -6]];
  const rings = [LIME, "#60A5FA", "#F472B6", "#FBBF24", "#34D399"];
  return <>{pos.map(([x, y, r], i) => (
    <Sticker key={i} at={o(48.0) + i * 2} x={x} y={y} rot={r} out={o(51.45)}>
      <div style={{ width: 150, height: 150, borderRadius: "50%", background: "#1f2023", border: `8px solid ${rings[i % 5]}`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 20px 40px rgba(0,0,0,0.35)" }}><IUser size={70} color="#fff" /></div>
    </Sticker>))}</>;
};
const SlotGrid: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <Sticker at={2} x={140} y={1430} out={fr(53.9 - 51.55)}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(15, 44px)", gap: 10, padding: 22, borderRadius: 26, background: "rgba(18,18,18,0.82)", boxShadow: "0 20px 50px rgba(0,0,0,0.35)" }}>
        {Array.from({ length: 30 }, (_, i) => <div key={i} style={{ width: 44, height: 44, borderRadius: 12, background: i < 10 ? "#555" : "transparent", border: i < 10 ? "none" : `3px solid ${LIME}`, opacity: k(f, 4 + i * 0.7, 10 + i * 0.7) }} />)}
      </div>
    </Sticker>
  );
};

/* CTA: comment "EDIT" (ref: Comment "Pack"), DM banner, bio */
const CommentCTA: React.FC<{ dur: number }> = ({ dur }) => {
  const f = useCurrentFrame(); const o = (t: number) => fr(t - 55.85);
  const n = Math.max(0, Math.min(4, Math.floor((f - o(56.6)) / 2.5)));
  const a = k(f, 0, 10); const out = k(f, dur - 6, dur, Easing.in(Easing.cubic));
  return (
    <div style={{ position: "absolute", left: 90, right: 90, top: 1240, opacity: a * (1 - out), transform: `translateY(${(1 - a) * 60}px)`, filter: a < 0.98 ? `blur(${(1 - a) * 10}px)` : undefined }}>
      <div style={{ borderRadius: 36, background: "rgba(255,255,255,0.97)", padding: "28px 34px", boxShadow: "0 30px 70px rgba(0,0,0,0.3)", display: "flex", alignItems: "center", gap: 22 }}>
        <div style={{ width: 80, height: 80, borderRadius: "50%", overflow: "hidden", background: LIME, flexShrink: 0 }}><Img src={staticFile("thumbs/avatar.png")} style={{ width: "100%", height: "100%", objectFit: "cover" }} /></div>
        <div style={{ flex: 1, fontFamily: inter, fontWeight: 800, fontSize: 52, color: INK }}>{"EDIT".slice(0, n)}<span style={{ opacity: f % 12 < 6 ? 1 : 0, color: "#1a73e8" }}>|</span>{n === 0 && <span style={{ color: "#aaa", fontWeight: 500 }}> Add a comment…</span>}</div>
        <div style={{ width: 84, height: 84, borderRadius: "50%", background: "#1a73e8", display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${f > o(57.0) && f < o(57.0) + 5 ? 0.85 : 1})` }}><ISend size={42} color="#fff" /></div>
      </div>
    </div>
  );
};
const DM: React.FC = () => {
  const f = useCurrentFrame(); const a = k(f, 0, 12);
  return (
    <div style={{ position: "absolute", left: 50, right: 50, top: 80 + (a - 1) * 260, borderRadius: 44, background: "rgba(30,30,32,0.92)", padding: "30px 34px", display: "flex", gap: 26, alignItems: "center", boxShadow: "0 30px 80px rgba(0,0,0,0.4)" }}>
      <div style={{ width: 110, height: 110, borderRadius: "50%", overflow: "hidden", background: LIME, flexShrink: 0 }}><Img src={staticFile("thumbs/avatar.png")} style={{ width: "100%", height: "100%", objectFit: "cover" }} /></div>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: inter, fontWeight: 800, fontSize: 42, color: "#fff" }}><span>aminur_rex</span><span style={{ fontWeight: 500, fontSize: 30, color: "#aaa" }}>now</span></div>
        <div style={{ fontFamily: inter, fontWeight: 500, fontSize: 38, color: "#ddd", marginTop: 6 }}>Here's the full Monthly Editing Package</div>
      </div>
    </div>
  );
};
const Bio: React.FC<{ dur: number }> = ({ dur }) => {
  const f = useCurrentFrame(); const o = (t: number) => fr(t - 59.05);
  const a = k(f, 0, 12); const out = k(f, dur - 6, dur, Easing.in(Easing.cubic));
  const hl = k(f, o(61.2), o(61.2) + 8); const tap = k(f, o(61.2), o(61.2) + 12);
  const T = (st: React.CSSProperties, c: React.ReactNode) => <div style={{ fontFamily: inter, color: "#f5f5f5", ...st }}>{c}</div>;
  return (
    <div style={{ position: "absolute", left: 60, right: 60, top: 1010, borderRadius: 44, background: "rgba(12,15,20,0.96)", padding: 44, boxShadow: "0 40px 100px rgba(0,0,0,0.45)", opacity: a * (1 - out), transformOrigin: "50% 0", transform: `translateY(${(1 - a) * 60}px) scale(${(0.96 + 0.04 * a) * 0.82})`, filter: a < 0.98 || out > 0 ? `blur(${(1 - a) * 12 + out * 12}px)` : undefined }}>
      <div style={{ display: "flex", alignItems: "center", gap: 36 }}>
        <div style={{ width: 180, height: 180, borderRadius: "50%", overflow: "hidden", background: LIME, flexShrink: 0 }}><Img src={staticFile("thumbs/avatar.png")} style={{ width: "100%", height: "100%", objectFit: "cover" }} /></div>
        <div style={{ flex: 1 }}>
          {T({ fontWeight: 800, fontSize: 52 }, "aminur_rex")}
          <div style={{ display: "flex", gap: 34, marginTop: 10 }}>{[["126", "posts"], ["2,554", "followers"], ["405", "following"]].map(([nn, l]) => <div key={l}>{T({ fontWeight: 800, fontSize: 40 }, nn)}{T({ fontWeight: 500, fontSize: 26, color: "#bbb" }, l)}</div>)}</div>
        </div>
      </div>
      <div style={{ marginTop: 26, lineHeight: 1.45 }}>
        {T({ fontWeight: 700, fontSize: 36 }, "Aminur Rahaman | Video Editor")}
        {T({ fontWeight: 500, fontSize: 34 }, "4+ Years of Video Editing 🎬")}
        {T({ fontWeight: 500, fontSize: 34 }, "1000+ Videos Delivered for Clients")}
        <div style={{ position: "relative", marginTop: 8 }}>
          <div style={{ position: "absolute", left: -16, right: 20, top: -8, bottom: -8, borderRadius: 16, border: `4px solid ${LIME}`, opacity: hl, boxShadow: `0 0 30px rgba(200,243,30,0.35)` }} />
          {T({ fontWeight: 500, fontSize: 34 }, "📞 Book a call for…")}
          {T({ fontWeight: 700, fontSize: 34, color: "#8ab4ff" }, "🔗 superprofile.bio/bookings/graphicorev2")}
        </div>
      </div>
      <div style={{ display: "flex", gap: 16, marginTop: 30 }}>{["Follow", "Message", "Contact"].map((b, i) => <div key={b} style={{ flex: 1, height: 84, borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: inter, fontWeight: 700, fontSize: 34, color: "#fff", background: i === 0 ? "#0095F6" : "#262a31", boxShadow: i === 2 ? `0 0 0 ${5 * tap}px ${LIME}` : "none" }}>{b}</div>)}</div>
    </div>
  );
};

/* end: zoom out into the edit timeline */
const Timeline: React.FC = () => {
  const f = useCurrentFrame(); const a = k(f, 0, 14);
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top: 1470, opacity: a, transform: `translateY(${(1 - a) * 80}px)` }}>
      <div style={{ borderRadius: 30, background: "rgba(16,16,18,0.9)", padding: 24, boxShadow: "0 30px 70px rgba(0,0,0,0.4)" }}>
        {["#8a6a2a", "#6a4a7e", "#2f6b55", "#2e5a7a"].map((c, r) => (
          <div key={r} style={{ position: "relative", height: 46, marginBottom: 10, background: "#1c1c20", borderRadius: 8 }}>
            {Array.from({ length: 14 }, (_, i) => <div key={i} style={{ position: "absolute", top: 5, bottom: 5, left: `${(i * 7.1 + (r * 3) % 5)}%`, width: `${4 + ((i * 7 + r * 3) % 4)}%`, background: c, borderRadius: 5 }} />)}
          </div>
        ))}
        <div style={{ position: "absolute", top: 14, bottom: 14, left: `${8 + a * 80}%`, width: 4, background: "#ff3b30" }} />
      </div>
      <div style={{ marginTop: 18, textAlign: "center", fontFamily: inter, fontWeight: 800, fontSize: 52, color: "#fff" }}>Edited by <span style={{ color: LIME }}>Aminur Rex Team</span></div>
    </div>
  );
};

const LightLeak: React.FC<{ dur?: number }> = ({ dur = 20 }) => {
  const f = useCurrentFrame(); const p = k(f, 0, dur, IO); const o = interpolate(f, [0, dur * 0.35, dur], [0, 0.5, 0], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", opacity: o, background: `radial-gradient(60% 40% at ${-20 + 140 * p}% ${25 + 20 * p}%, rgba(255,200,140,0.9) 0%, rgba(255,200,140,0) 70%)` }} />;
};
const Finish: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill style={{ background: "radial-gradient(120% 85% at 50% 42%, rgba(0,0,0,0) 60%, rgba(0,0,0,0.35) 100%)" }} />
  </AbsoluteFill>
);

/* =============================== sound */
type Fx = [string, number, number?, number?, number?];
const FX: Fx[] = [
  ...BIGS.map((b, i) => [i % 2 ? "swoosh_short" : "whoosh_air", b.t - 0.08, 0.22, 0.6] as Fx),
  ["impact_logo", 0.0, 0.3], ["coins_clink", 1.45, 0.22], ["pop_light", 3.6, 0.25],
  ["sweep_fast", 4.12, 0.32], ["tick_counter", 4.5, 0.25], ["tick_timer", 5.9, 0.18, 2.2], ["sweep_fast2", 8.35, 0.28],
  ["glitch_quick", 12.05, 0.35], ["bass_short", 12.05, 0.35, 0.6],
  ["whoosh_cine", 13.4, 0.3], ...Array.from({ length: 10 }, (_, i) => ["key_single", 13.6 + i * 0.07, 0.18] as Fx), ["notif_correct", 13.9, 0.3], ["click_check", 16.2, 0.28], ["whoosh_air", 17.25, 0.25, 0.6],
  ["sweep_fast", 23.5, 0.3], ...STYLES.map((s) => ["click_tone", s.t, 0.22, 0.5] as Fx), ...STYLES.map((s) => ["pop_light", s.t + 0.05, 0.18] as Fx), ["whoosh_air", 31.95, 0.25, 0.6],
  ["pop_hard", 35.1, 0.22], ["pop_hard", 36.4, 0.22], ["notif_correct", 37.8, 0.25],
  ["sweep_air", 39.35, 0.22, 1.2], ["impact_zoom", 39.8, 0.25, 0.8],
  ...[41.7, 42.4, 42.8, 43.6].map((t) => ["pop_dry", t, 0.22] as Fx), ["glitch_text", 44.15, 0.25], ["swoosh_short", 44.3, 0.22],
  ["riser", 45.3, 0.2, 1.2, 5.38 - 1.2], ["impact_deep", 46.55, 0.28, 1.2], ["slot_payout", 46.7, 0.2],
  ...Array.from({ length: 10 }, (_, i) => ["pop_light", 48.0 + i * 0.067, 0.14] as Fx),
  ["tick_timer", 51.6, 0.16, 2.2], ["bass_short", 52.2, 0.22, 0.5],
  ["whoosh_air", 55.85, 0.22, 0.6], ...[0, 1, 2, 3].map((i) => ["key_single", 56.6 + i * 0.085, 0.3] as Fx), ["pop_hard", 57.0, 0.2], ["notif_positive", 57.2, 0.3],
  ["swoosh_short", 59.0, 0.22], ["click_tone", 61.2, 0.25], ["whoosh_cine", 62.25, 0.28], ["reveal", 63.8, 0.22], ["impact_deep", 64.6, 0.2, 0.8],
];
const Sound: React.FC = () => (
  <>
    <Audio src={staticFile("voice.m4a")} />
    <Audio src={staticFile("music_final.mp3")} startFrom={fr(15)} volume={(f) => interpolate(f, [0, 8, fr(FINAL_DUR) - 24, fr(FINAL_DUR)], [0, 0.12, 0.12, 0], { extrapolateRight: "clamp" })} />
    {FX.map(([n, t, v = 0.3, max, off = 0], i) => {
      const d = Math.min(max ?? 99, ((META as Record<string, number>)[n] ?? 1) - off);
      return <Sequence key={i} from={Math.max(0, fr(t))} durationInFrames={Math.max(2, fr(d))} name={`sfx ${n}`}><Audio src={staticFile(`sfx/${n}.mp3`)} volume={v} startFrom={fr(off)} /></Sequence>;
    })}
  </>
);

/* =============================== composition */
const SCENES = { shoot: [4.15, 8.4], search: [13.45, 17.3], styles: [23.55, 32.0] } as const;
const HIDE: [number, number][] = [[...SCENES.shoot], [...SCENES.search], [...SCENES.styles], [55.85, 57.15], [59.05, 62.2]] as any;

export const FinalClean: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Plate />
    <Subject />
    <Audio src={staticFile("voice.m4a")} />
  </AbsoluteFill>
);

export const Final: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Plate />
    {BIGS.map((b, i) => <Seq key={i} a={b.t} b={b.e} name={`big ${b.text}`}><BigWord b={b} /></Seq>)}
    <Subject />

    <Seq a={34.0} b={38.65} name="format chips"><FormatChips /></Seq>
    <Seq a={41.35} b={44.8} name="invoices"><Invoices /></Seq>
    <Seq a={47.55} b={51.6} name="creators"><CreatorStickers /></Seq>
    <Seq a={51.55} b={54.0} name="slots"><SlotGrid /></Seq>

    <Captions hide={HIDE} />

    <Seq a={SCENES.shoot[0]} b={SCENES.shoot[1]} name="shoot vs edit"><ShootVsEdit dur={fr(SCENES.shoot[1] - SCENES.shoot[0])} /></Seq>
    <Seq a={SCENES.search[0]} b={SCENES.search[1]} name="search"><SearchScene dur={fr(SCENES.search[1] - SCENES.search[0])} /></Seq>
    <Seq a={SCENES.styles[0]} b={SCENES.styles[1]} name="styles"><StyleFolder dur={fr(SCENES.styles[1] - SCENES.styles[0])} t0={SCENES.styles[0]} /></Seq>

    <Seq a={55.85} b={57.15} name="comment"><CommentCTA dur={fr(1.3)} /></Seq>
    <Seq a={57.15} b={59.05} name="dm"><DM /></Seq>
    <Seq a={59.05} b={62.2} name="bio"><Bio dur={fr(3.15)} /></Seq>
    <Seq a={63.0} b={65.0} name="timeline"><Timeline /></Seq>

    <Seq a={0} b={0.8}><LightLeak dur={22} /></Seq>
    <Seq a={17.3} b={18.0}><LightLeak dur={18} /></Seq>
    <Seq a={46.5} b={47.3}><LightLeak dur={20} /></Seq>
    <Sound />
  </AbsoluteFill>
);
