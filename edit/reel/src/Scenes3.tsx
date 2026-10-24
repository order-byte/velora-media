import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, interpolate, Easing } from "remotion";
import { C, inter, serif, mono, ICam, ICheck, IX, IDown, IStopwatch, IMic, IFilm, IUser, IBolt, ITrend } from "./lib";
import { Cream, Navy, NeonTile, Glass, Typed, PanUp, k, EXPO, INOUT } from "./Fx";
import { Mini } from "./Scenes";

/* pain_1 — cream card: circular b-roll + typed label (B&W section) */
export const ShootCream: React.FC = () => {
  const f = useCurrentFrame();
  const a = k(f, 0, 14);
  const ring = k(f, 10, 40, INOUT);
  return (
    <Cream>
      <div style={{ position: "absolute", left: 540 - 270, top: 430, width: 540, height: 540, borderRadius: "50%", overflow: "hidden", boxShadow: "0 40px 90px rgba(60,40,20,0.28), inset 0 0 0 1px rgba(0,0,0,0.05)", transform: `scale(${0.88 + 0.12 * a})`, opacity: a, filter: a < 0.98 ? `blur(${(1 - a) * 16}px)` : undefined }}>
        <OffthreadVideo src={staticFile("broll/shoot_youtuber.mp4")} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) contrast(1.1)" }} />
      </div>
      <svg width="640" height="640" viewBox="0 0 640 640" style={{ position: "absolute", left: 220, top: 380 }}>
        <circle cx="320" cy="320" r="306" fill="none" stroke="rgba(40,30,20,0.12)" strokeWidth="8" />
        <circle cx="320" cy="320" r="306" fill="none" stroke="#2a211a" strokeWidth="8" strokeLinecap="round" strokeDasharray={2 * Math.PI * 306} strokeDashoffset={2 * Math.PI * 306 * (1 - ring)} transform="rotate(-90 320 320)" />
      </svg>
      <div style={{ position: "absolute", top: 1060, left: 0, right: 0, textAlign: "center" }}>
        <div style={{ fontFamily: inter, fontWeight: 800, fontSize: 92, color: "#2a211a", letterSpacing: "-0.04em" }}><Typed text="Shoot" start={6} cps={0.5} /></div>
        <div style={{ marginTop: 10, fontFamily: mono, fontWeight: 700, fontSize: 46, color: "#6b5a4a", letterSpacing: "0.1em", opacity: k(f, 18, 28) }}>00:10:00</div>
      </div>
    </Cream>
  );
};

/* pain_3 — posting calendar on frosted glass over the speaker */
export const PostGlass: React.FC = () => {
  const days = ["M", "T", "W", "T", "F", "S", "S"];
  const ok = [true, false, false, true, false, false, false];
  const f = useCurrentFrame();
  return (
    <Glass x={90} y={110} w={900} delay={0} pad={30} dark>
      <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 28, letterSpacing: "0.16em", color: "rgba(255,255,255,0.75)", textAlign: "center", marginBottom: 20 }}>POSTING THIS WEEK</div>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        {days.map((d, i) => {
          const a = k(f, 4 + i * 3, 14 + i * 3);
          return (
            <div key={i} style={{ width: 104, height: 128, borderRadius: 22, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 4,
              background: ok[i] ? "rgba(255,255,255,0.92)" : "rgba(255,77,77,0.9)", opacity: a, transform: `translateY(${(1 - a) * 24}px)`, filter: a < 0.98 ? `blur(${(1 - a) * 8}px)` : undefined }}>
              <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 28, color: ok[i] ? C.ink : "#fff" }}>{d}</div>
              {ok[i] ? <ICheck size={48} color="#111" stroke={3.2} /> : <IX size={48} color="#fff" stroke={3.2} />}
            </div>
          );
        })}
      </div>
    </Glass>
  );
};

/* pain_4 — growth chart on glass */
export const GrowthGlass: React.FC = () => {
  const f = useCurrentFrame();
  const p = k(f, 4, 30, INOUT);
  const pts = [[0, 40], [80, 50], [160, 36], [240, 70], [320, 96], [400, 124], [480, 152], [560, 196]];
  const d = pts.map((q, i) => `${i ? "L" : "M"}${q[0]},${q[1]}`).join(" ");
  return (
    <Glass x={140} y={110} w={800} delay={0} pad={32} dark>
      <div style={{ display: "flex", alignItems: "center", gap: 14, fontFamily: inter, fontWeight: 800, fontSize: 44, color: "#fff" }}>
        Growth <span style={{ color: C.red, display: "flex", alignItems: "center", gap: 8 }}><IDown size={46} color={C.red} stroke={3} />slow</span>
      </div>
      <svg width="736" height="230" viewBox="0 0 560 210" style={{ marginTop: 6 }}>
        {[50, 100, 150, 200].map((y) => <line key={y} x1="0" x2="560" y1={y} y2={y} stroke="rgba(255,255,255,0.12)" />)}
        <path d={d} fill="none" stroke={C.red} strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="900" strokeDashoffset={900 * (1 - p)} style={{ filter: "drop-shadow(0 0 10px rgba(255,77,77,0.6))" }} />
      </svg>
    </Glass>
  );
};

/* frosted tag in the top band (offer_2, fcfs) */
export const GlassTag: React.FC<{ icon: React.ReactNode; text: string; sub?: string }> = ({ icon, text, sub }) => (
  <Glass x={110} y={140} w={860} delay={0} pad={28} dark>
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 22 }}>
      {icon}
      <div>
        <div style={{ fontFamily: inter, fontWeight: 900, fontSize: 76, letterSpacing: "-0.04em", color: "#fff", lineHeight: 1 }}>{text}</div>
        {sub && <div style={{ fontFamily: inter, fontWeight: 600, fontSize: 36, color: "rgba(255,255,255,0.75)", marginTop: 8 }}>{sub}</div>}
      </div>
    </div>
  </Glass>
);

/* offer_3 — white scene: speaker card + typed checklist, ends with a push into the text */
export const WeEdit: React.FC<{ offset: number; dur: number }> = ({ offset, dur }) => {
  const f = useCurrentFrame();
  const items = ["Cutting & pacing", "Captions", "Motion graphics", "Sound design", "Colour grade"];
  const push = k(f, dur - 9, dur, Easing.in(Easing.cubic));
  return (
    <AbsoluteFill style={{ background: "#fff" }}>
      <AbsoluteFill style={{ transform: `scale(${1 + push * 1.4})`, transformOrigin: "50% 62%", filter: push > 0.02 ? `blur(${push * 18}px)` : undefined }}>
        <Mini x={250} y={140} w={580} h={640} r={40} offset={offset} delay={0} />
        <div style={{ position: "absolute", top: 860, left: 150, right: 80 }}>
          {items.map((t, i) => {
            const st = 4 + i * 6;
            const a = k(f, st, st + 8);
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 22, height: 96, opacity: a, transform: `translateX(${(1 - a) * -30}px)` }}>
                <div style={{ width: 62, height: 62, borderRadius: 18, background: C.purpleDeep, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 10px 26px rgba(124,58,237,0.35)" }}><ICheck size={40} color="#fff" stroke={3.4} /></div>
                <Typed text={t} start={st + 2} cps={1.6} style={{ fontFamily: inter, fontWeight: 800, fontSize: 60, letterSpacing: "-0.03em", color: C.purpleDeep }} />
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* style_trend + sab — navy neon tiles, then the camera pans up into the montage */
export const NavyStyles: React.FC<{ panAt: number; trendF: number }> = ({ panAt, trendF }) => {
  const f = useCurrentFrame();
  const tiles: [string, string, string, React.ReactNode][] = [
    ["TH", "Talking head", "#7C3AED", <IUser size={96} color="#fff" stroke={2.4} />], ["Pc", "Podcast", "#22D3EE", <IMic size={96} color="#fff" stroke={2.4} />],
    ["Dc", "Documentary", "#F59E0B", <IFilm size={96} color="#fff" stroke={2.4} />], ["Cv", "Cinematic", "#EC4899", <span style={{ fontFamily: serif, fontStyle: "italic", fontWeight: 400 }}>Cv</span>],
    ["Mg", "Motion", "#22C55E", <IBolt size={96} color="#fff" stroke={2.4} />], ["Fs", "Faceless", "#3B82F6", <ITrend size={96} color="#fff" stroke={2.4} />],
  ];
  const glow = k(f, trendF, trendF + 10);
  return (
    <Navy>
      <PanUp at={panAt}>
        <div style={{ position: "absolute", top: 230, left: 0, right: 0, textAlign: "center", fontFamily: inter, fontWeight: 900, fontSize: 96, letterSpacing: "-0.04em", color: "#67E8F9",
          textShadow: `0 0 ${20 + 30 * glow}px rgba(103,232,249,${0.4 + 0.5 * glow})`, opacity: glow, filter: glow < 0.98 ? `blur(${(1 - glow) * 12}px)` : undefined }}>Trending now</div>
        <div style={{ position: "absolute", top: 470, left: 0, right: 0, display: "grid", gridTemplateColumns: "repeat(3, 250px)", justifyContent: "center", gap: "70px 50px" }}>
          {tiles.map(([l, s, c, ic], i) => <NeonTile key={i} label={l} sub={s} color={c} delay={2 + i * 4} size={230}>{ic}</NeonTile>)}
        </div>
      </PanUp>
    </Navy>
  );
};

/* reel — invoices with an ink headline (captions are hidden on this white scene) */
export const InvoiceHead: React.FC<{ killF: number }> = ({ killF }) => {
  const f = useCurrentFrame();
  const a = k(f, 2, 14), b = k(f, killF - 2, killF + 8);
  return (
    <div style={{ position: "absolute", top: 1330, left: 0, right: 0, textAlign: "center" }}>
      <div style={{ fontFamily: inter, fontWeight: 800, fontSize: 64, letterSpacing: "-0.03em", color: C.ink, opacity: a * (1 - b), filter: a < 0.98 ? `blur(${(1 - a) * 10}px)` : undefined }}>Har reel ka <span style={{ color: C.purpleDeep }}>alag bill?</span></div>
    </div>
  );
};
