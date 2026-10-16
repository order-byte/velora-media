import React, { useEffect, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile, useCurrentFrame } from "remotion";
import { BARS as MUSIC_BARS, BEATS as MUSIC_BEATS } from "./beats";
import { clipAt } from "./data";
import {
  Captions,
  Chip,
  Cursor,
  Footage,
  FrameCounter,
  Label,
  MaskLine,
  MIC,
  PopInline,
  PopWord,
  Selection,
  Stage,
  Thumb,
  Vignette,
  Window,
  display,
  easeIn,
  easeInOut,
  easeOut,
  expoOut,
  label,
  lerp,
  prog,
  reveal,
  rnd,
  text,
  within,
} from "./lib";
import {
  C,
  DISPLAY_FONT_FILES,
  FONT_DISPLAY,
  FONT_TEXT,
  FPS,
  H,
  HIDDEN_FRAME,
  SECRET,
  SELECTS_FRAMES,
  TEXT_FONT_FILES,
  TOTAL_FRAMES,
  W,
} from "./theme";

// ---------- fonts ----------
let fontsReady: Promise<void> | null = null;
const loadFonts = () => {
  if (!fontsReady) {
    const faces = [
      ...DISPLAY_FONT_FILES.map((f) => new FontFace(FONT_DISPLAY, `url(${staticFile(f.file)})`, { weight: f.weight })),
      ...TEXT_FONT_FILES.map((f) => new FontFace(FONT_TEXT, `url(${staticFile(f.file)})`, { weight: f.weight })),
    ];
    fontsReady = Promise.all(faces.map((face) => face.load().then((l) => void document.fonts.add(l)))).then(() => undefined);
  }
  return fontsReady;
};

type BeatProps = { t: number; f: number };

// The matte ends where the table hides his body (source y ~1530). Cut-outs are pushed down by this much
// so that hard edge always sits below the bottom of the frame instead of mid-shot.
const BOTTOM_ANCHOR = 405;

// Snap-zoom at the start of a shot (jump cuts read as intentional) and a slow camera push through it.
const snapIn = (t: number, start: number) => 1 + 0.04 * (1 - expoOut(prog(t, start, 0.3)));
const push = (t: number, a: number, b: number, amt = 0.045) => 1 + amt * prog(t, a, b - a);

// Corner brackets (viewfinder) around a box.
const Brackets: React.FC<{ x: number; y: number; w: number; h: number; len?: number; color?: string; width?: number }> = ({
  x,
  y,
  w,
  h,
  len = 70,
  color = C.white,
  width = 4,
}) => {
  const b = `${width}px solid ${color}`;
  const box = (l: number, tp: number, st: React.CSSProperties, k: number) => (
    <div key={k} style={{ position: "absolute", left: l, top: tp, width: len, height: len, ...st }} />
  );
  return (
    <>
      {box(x, y, { borderLeft: b, borderTop: b }, 0)}
      {box(x + w - len, y, { borderRight: b, borderTop: b }, 1)}
      {box(x, y + h - len, { borderLeft: b, borderBottom: b }, 2)}
      {box(x + w - len, y + h - len, { borderRight: b, borderBottom: b }, 3)}
    </>
  );
};

// ============ 00 HOOK: "I hid one frame in this video." ============
// Low-key world, a giant ? standing behind him, the word FRAME hidden in a blur until he says it.
const Hook: React.FC<BeatProps> = ({ t, f }) => {
  const zoom = lerp(1.12, 1.2, easeInOut(prog(t, 0, 1.87)));
  const out = easeIn(prog(t, 1.68, 0.19)); // zoom-through into the next shot
  const sc = zoom * (1 + 0.22 * out);
  const flicker = 0.94 + 0.06 * rnd(f + 3);
  const look = `grayscale(0.8) contrast(1.45) brightness(${(0.58 * flicker).toFixed(3)})`;
  const hidden = t < 0.68;
  const frameP = reveal(t, 0.68, 0.5);
  const typed = "in this video.".slice(0, Math.max(0, Math.floor((t - 0.96) / 0.03)));
  const box = reveal(t, 0.68, 0.6);
  return (
    <>
      <AbsoluteFill style={{ background: C.stage }} />
      <AbsoluteFill style={{ filter: out > 0 ? `blur(${out * 14}px)` : undefined }}>
        <Footage frame={f} scale={sc} filter={look} />
        <div style={{ position: "absolute", left: 590, top: 170, ...display(940, C.yellow, 800), lineHeight: 1, transform: `scale(${sc * (1 + 0.02 * Math.sin(t * 7))}) rotate(7deg)`, transformOrigin: "50% 60%" }}>?</div>
        <Footage frame={f} scale={sc} filter={look} person />
      </AbsoluteFill>
      <Vignette strength={0.85} />
      {t >= 0.68 ? <Selection x={270} y={250} w={540} h={700} p={box} tag={within(t, 0.68, 1.1) ? "FRAME ????" : "1 FRAME · HIDDEN"} /> : null}
      <div style={{ position: "absolute", left: 90, top: 1050, display: "flex", gap: 30, ...display(140, C.white, 800) }}>
        <PopInline t={t} t0={-0.3}>I</PopInline>
        <PopInline t={t} t0={0.14}>HID</PopInline>
        <PopInline t={t} t0={0.4}>ONE</PopInline>
      </div>
      {t >= 0.4 ? (
        <div
          style={{
            position: "absolute",
            left: 84,
            top: 1180,
            ...display(250, hidden ? C.white : C.yellow, 800),
            opacity: hidden ? 0.42 : 1,
            filter: hidden ? "blur(22px)" : frameP < 0.98 ? `blur(${(1 - frameP) * 22}px)` : undefined,
            transform: `scale(${hidden ? 1.04 : lerp(1.04, 1, frameP)})`,
            transformOrigin: "left center",
          }}
        >
          FRAME
        </div>
      ) : null}
      <div style={{ position: "absolute", left: 94, top: 1430, ...label(40, C.white, 0.3) }}>
        {typed}
        {t >= 0.96 && Math.floor(t * 5) % 2 === 0 ? <span style={{ color: C.yellow }}>_</span> : null}
      </div>
    </>
  );
};

// ============ 01 FIND: "Dhoondh ke dikhao." (scanner over B/W) ============
const Find: React.FC<BeatProps> = ({ t, f }) => {
  const st = 1.8667;
  const settle = expoOut(prog(t, st, 0.35));
  const scanY = lerp(250, 1520, easeInOut(prog(t, st + 0.05, 0.95)));
  return (
    <>
      <Footage frame={f} scale={lerp(1.25, 1.02, settle)} filter={`grayscale(1) contrast(1.42) brightness(0.84) blur(${((1 - settle) * 10).toFixed(2)}px)`} />
      <Vignette strength={0.6} />
      {[360, 720].map((x) => (
        <div key={x} style={{ position: "absolute", left: x, top: 0, width: 1, height: H, background: "rgba(255,255,255,0.22)" }} />
      ))}
      {[640, 1280].map((y) => (
        <div key={y} style={{ position: "absolute", top: y, left: 0, height: 1, width: W, background: "rgba(255,255,255,0.22)" }} />
      ))}
      <Brackets x={56} y={300} w={968} h={1230} len={80} width={4} />
      <div style={{ position: "absolute", left: 0, top: scanY, width: W, height: 3, background: C.yellow, boxShadow: "0 0 28px 6px rgba(238,255,0,0.45)" }} />
      <div style={{ position: "absolute", left: 90, top: 1040, display: "flex", gap: 30, ...display(130, C.white, 800) }}>
        <PopInline t={t} t0={1.87}>DHOONDH</PopInline>
        <PopInline t={t} t0={2.17}>KE</PopInline>
      </div>
      <PopWord t={t} t0={2.29} style={{ left: 84, top: 1180, ...display(190, C.yellow, 800) }}>
        DIKHAO.
      </PopWord>
    </>
  );
};

// ============ 02 NAME: "I am Aminur, a video editor." (name behind the cut-out, on a lit stage) ============
const Name: React.FC<BeatProps> = ({ t, f }) => {
  const st = 2.9;
  const ps = 1.04 * snapIn(t, st) * push(t, st, 5.0, 0.03);
  const cur = easeInOut(prog(t, 3.95, 0.3));
  const clicked = t >= 4.3;
  return (
    <>
      <Stage cy={46} light={0.16} />
      <MaskLine t={t} t0={2.92} style={{ left: 0, width: W, top: 330, textAlign: "center" }}>
        <span style={{ ...label(34, C.muted, 0.42) }}>I am</span>
      </MaskLine>
      <MaskLine t={t} t0={3.2} d={0.6} style={{ left: 0, width: W, top: 395, textAlign: "center" }}>
        <span style={{ ...display(272, C.white, 800) }}>AMINUR</span>
      </MaskLine>
      <Footage frame={f} person scale={ps} ox={540} oy={1530} ty={BOTTOM_ANCHOR} shadow />
      <PopWord t={t} t0={3.92} style={{ left: 80, top: 1330 }}>
        <Chip dot={clicked ? C.ink : C.yellow} size={32} style={clicked ? { background: C.yellow, color: C.ink, border: "1px solid transparent" } : undefined}>
          Video Editor
        </Chip>
      </PopWord>
      {t >= 3.92 ? <Cursor x={lerp(900, 420, cur)} y={lerp(1580, 1360, cur)} pressed={within(t, 4.28, 4.38)} /> : null}
    </>
  );
};

// ============ 03 FRAMES: "Frames? Woh toh mera game hai." (film strip, then pole position on the F1-car mic) ============
const Frames: React.FC<BeatProps> = ({ t, f }) => {
  if (t < 5.58) {
    const xAt = (tt: number) => lerp(140, -460, easeOut(prog(tt, 5.0, 0.58)));
    const x0 = xAt(t);
    const vel = Math.abs(xAt(t + 1 / FPS) - x0);
    return (
      <>
        <Stage cy={50} light={0.08} />
        <div style={{ position: "absolute", left: x0, top: 650, height: 600, width: 2500, background: "#101012", borderRadius: 18, filter: vel > 4 ? `blur(${Math.min(6, vel / 6).toFixed(2)}px)` : undefined, boxShadow: "0 40px 80px rgba(0,0,0,0.6)" }}>
          {Array.from({ length: 41 }).map((_, i) => (
            <React.Fragment key={i}>
              <span style={{ position: "absolute", left: 16 + i * 60, top: 14, width: 26, height: 18, borderRadius: 4, background: "#2B2B2F" }} />
              <span style={{ position: "absolute", left: 16 + i * 60, bottom: 14, width: 26, height: 18, borderRadius: 4, background: "#2B2B2F" }} />
            </React.Fragment>
          ))}
          {[4, 13, 22, 31, 40, 9, 17].map((k, i) => (
            <Thumb key={i} i={k} w={290} style={{ position: "absolute", left: 24 + i * 340, top: 50, height: 500, borderRadius: 10 }} />
          ))}
        </div>
        <MaskLine t={t} t0={5.0} d={0.45} style={{ left: 84, top: 330 }}>
          <span style={{ ...display(210, C.white, 800) }}>
            Frames<span style={{ color: C.yellow }}>?</span>
          </span>
        </MaskLine>
        <PopWord t={t} t0={5.1} style={{ left: 92, top: 1310, ...label(28, C.muted, 0.32) }}>
          24 · 30 · 60 fps
        </PopWord>
      </>
    );
  }
  const k = expoOut(prog(t, 5.58, 0.5));
  const sc = lerp(1.15, 1.42, k) * push(t, 5.9, 7.27, 0.04);
  const kmh = Math.round(lerp(0, 312, easeOut(prog(t, 5.6, 0.8))));
  const lap = Math.max(0, t - 5.6);
  const p1 = reveal(t, 6.4, 0.5);
  return (
    <>
      <Footage frame={f} scale={sc} ox={MIC.x} oy={MIC.y - 120} />
      <Vignette strength={0.45} />
      <div style={{ position: "absolute", right: 64, top: 232, display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 12 }}>
        <Chip dot={C.yellow} size={24}>Aminur · Lap 01</Chip>
        <div style={{ ...display(84, C.white, 800), fontVariantNumeric: "tabular-nums", textShadow: "0 4px 20px rgba(0,0,0,0.5)" }}>
          {kmh}
          <span style={{ ...label(24, C.muted, 0.2), marginLeft: 10 }}>km/h</span>
        </div>
        <div style={{ ...label(24, C.white, 0.18), fontVariantNumeric: "tabular-nums", opacity: 0.85 }}>0:0{lap.toFixed(3)}</div>
      </div>
      {t >= 6.4 ? (
        <div style={{ position: "absolute", left: 80, top: 300, opacity: p1, transform: `translateY(${(1 - p1) * 30}px)`, filter: p1 < 0.98 ? `blur(${((1 - p1) * 12).toFixed(2)}px)` : undefined }}>
          <div style={{ ...display(230, C.yellow, 800) }}>P1</div>
          <div style={{ ...label(26, C.white, 0.32), marginTop: 10 }}>Pole position</div>
        </div>
      ) : null}
    </>
  );
};

// ============ 04 MOVIES: "I make 30-second reels feel like a movie." ============
const Movies: React.FC<BeatProps> = ({ t, f }) => {
  if (t < 8.74) {
    const sc = snapIn(t, 7.2667) * push(t, 7.27, 8.74);
    const bar = prog(t, 7.27, 1.47);
    return (
      <>
        <Footage frame={f} scale={sc} />
        {t >= 7.71 ? (
          <MaskLine t={t} t0={7.71} d={0.5} style={{ right: 36, top: 560 }}>
            <span style={{ ...display(300, C.white, 800), opacity: 0.96 }}>
              30<span style={{ fontSize: 150, color: C.yellow }}>s</span>
            </span>
          </MaskLine>
        ) : null}
        <Footage frame={f} scale={sc} person />
        <div style={{ position: "absolute", left: 64, top: 1515, width: 952, height: 4, borderRadius: 2, background: "rgba(255,255,255,0.25)" }}>
          <div style={{ width: `${bar * 100}%`, height: "100%", borderRadius: 2, background: C.white }} />
        </div>
      </>
    );
  }
  const lb = expoOut(prog(t, 8.74, 0.4));
  const bump = t >= 9.33 ? lerp(1.2, 1.14, expoOut(prog(t, 9.33, 0.5))) : lerp(1.06, 1.12, prog(t, 8.74, 0.6));
  return (
    <>
      <Footage frame={f} scale={bump} filter="contrast(1.08) saturate(0.95)" />
      <div style={{ position: "absolute", left: 0, top: 0, width: W, height: 410 * lb, background: C.black }} />
      <div style={{ position: "absolute", left: 0, bottom: 0, width: W, height: 410 * lb, background: C.black }} />
      <div style={{ position: "absolute", left: 0, width: W, top: 300, textAlign: "center", ...label(30, C.white, 0.6), opacity: prog(t, 8.95, 0.3) }}>A film by Aminur</div>
    </>
  );
};

// ============ 05 NUMBERS: "Boring numbers feel like stories." ============
const NUMS = Array.from({ length: 60 }).map((_, i) => ((i * 7919 + 13) % 9973) / 100);
const Numbers: React.FC<BeatProps> = ({ t, f }) => {
  if (t < 10.58) {
    const b = reveal(t, 10.05, 0.35);
    return (
      <>
        <Stage cy={40} light={0.07} />
        <Window x={70} y={300} w={940} h={1100} title="Q3_report_FINAL_v4.xlsx" style={{ filter: b > 0 ? `blur(${(b * 7).toFixed(2)}px)` : undefined, opacity: lerp(1, 0.55, b) }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", padding: "18px 26px" }}>
            {["", "Q1", "Q2", "Q3", "Q4"].map((h, i) => (
              <div key={`h${i}`} style={{ ...text(26, C.muted, 700), padding: "12px 8px", borderBottom: `1px solid ${C.line}` }}>{h}</div>
            ))}
            {NUMS.slice(0, 50).map((n, i) =>
              i % 5 === 0 ? (
                <div key={i} style={{ ...text(26, C.muted, 600), padding: "15px 8px", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>Row {i / 5 + 1}</div>
              ) : (
                <div key={i} style={{ ...text(28, "rgba(255,255,255,0.62)", 500), padding: "15px 8px", borderBottom: "1px solid rgba(255,255,255,0.07)", fontVariantNumeric: "tabular-nums", opacity: t >= 10.0 + (i % 17) * 0.01 ? 1 : 0 }}>
                  {n.toFixed(2)}
                </div>
              ),
            )}
          </div>
        </Window>
        <PopWord t={t} t0={10.05} style={{ left: 0, width: W, top: 760, textAlign: "center", ...display(210, C.white, 800) }}>
          Boring<span style={{ color: C.yellow }}>.</span>
        </PopWord>
      </>
    );
  }
  if (t < 11.24) return <Footage frame={f} scale={snapIn(t, 10.58) * push(t, 10.58, 11.24)} />;
  const cards = [
    { k: 7, x: 120, y: 600, r: -8, d: 0 },
    { k: 23, x: 330, y: 640, r: 7, d: 0.06 },
    { k: 36, x: 230, y: 690, r: -1, d: 0.12 },
  ];
  return (
    <>
      <Stage cy={55} light={0.12} />
      {cards.map((c, i) => {
        const p = expoOut(prog(t, 11.24 + c.d, 0.45));
        return (
          <div key={i} style={{ position: "absolute", left: c.x, top: lerp(1950, c.y, p), transform: `perspective(1400px) rotateX(${(1 - p) * 25}deg) rotate(${c.r * p}deg)`, background: "#1B1B1E", padding: "14px 14px 64px", borderRadius: 22, border: `1px solid ${C.line}`, boxShadow: "0 40px 90px rgba(0,0,0,0.6)" }}>
            <Thumb i={c.k} w={440} style={{ height: 580, borderRadius: 14 }} />
            <span style={{ position: "absolute", left: 24, bottom: 20, ...label(24, C.muted, 0.24) }}>Chapter {i + 1}</span>
          </div>
        );
      })}
      <MaskLine t={t} t0={11.24} style={{ left: 84, top: 300 }}>
        <span style={{ ...display(210, C.white, 800) }}>
          Stories<span style={{ color: C.yellow }}>.</span>
        </span>
      </MaskLine>
    </>
  );
};

// ============ 06 TEN MINUTES: "10-minute videos feel like 2 minutes." (the hidden frame lives in here) ============
const TenMin: React.FC<BeatProps> = ({ t, f }) => {
  if (t < 12.56) return <Footage frame={f} scale={snapIn(t, 12.1) * push(t, 12.1, 12.56)} />;
  if (t < 13.75) {
    const ff = easeIn(prog(t, 13.0, 0.45));
    const secs = Math.round(lerp(600, 120, ff));
    const mm = Math.floor(secs / 60);
    const ss = String(secs % 60).padStart(2, "0");
    const done = t >= 13.45;
    const ph = lerp(0.03, 0.98, ff);
    const card = reveal(t, 12.56, 0.4);
    return (
      <>
        <Stage cy={45} light={0.09} />
        <div style={{ position: "absolute", left: 70, top: 560, width: 940, height: 640, borderRadius: 36, background: C.glass, border: `1px solid ${C.line}`, boxShadow: "0 50px 100px rgba(0,0,0,0.55)", opacity: card, transform: `translateY(${(1 - card) * 40}px)` }}>
          <div style={{ position: "absolute", left: 50, top: 46, ...label(24, C.muted, 0.22) }}>VIDEO_FINAL.mp4</div>
          <div style={{ position: "absolute", right: 50, top: 34 }}>{within(t, 13.0, 13.45) ? <Chip dot={C.yellow} size={22}>▶▶ 5×</Chip> : null}</div>
          <div style={{ position: "absolute", left: 0, width: 940, top: 150, textAlign: "center", ...display(300, done ? C.yellow : C.white, 800), fontVariantNumeric: "tabular-nums", transform: done ? `scale(${lerp(1.08, 1, expoOut(prog(t, 13.45, 0.4)))})` : undefined }}>
            {done ? "2:00" : `${mm}:${ss}`}
          </div>
          <div style={{ position: "absolute", left: 50, top: 520, width: 840, height: 8, borderRadius: 4, background: "rgba(255,255,255,0.14)" }}>
            <div style={{ width: `${ph * 100}%`, height: "100%", borderRadius: 4, background: C.white }} />
            <div style={{ position: "absolute", left: `${ph * 100}%`, top: -12, width: 32, height: 32, borderRadius: 16, background: C.yellow, transform: "translateX(-16px)", boxShadow: "0 0 18px rgba(238,255,0,0.6)" }} />
          </div>
          <div style={{ position: "absolute", left: 50, top: 560, ...label(22, C.muted, 0.2) }}>{done ? "0:00 / 2:00" : "0:00 / 10:00"}</div>
        </div>
      </>
    );
  }
  return <Footage frame={f} scale={1.22 * snapIn(t, 13.75)} />;
};

// ============ 07/08 ADS: "Aur ads? … Woh ads hi nahi lagta hai. Kuch aur hi lagta hai." ============
const AdUI: React.FC<{ t: number; gone: number }> = ({ t, gone }) => {
  if (t < 14.68) return null;
  const p = reveal(t, 14.68, 0.35) * (1 - gone);
  if (p <= 0.01) return null;
  return (
    <div style={{ opacity: p, filter: gone > 0 ? `blur(${(gone * 14).toFixed(2)}px)` : undefined, transform: `translateY(${(1 - p) * 20}px)` }}>
      <div style={{ position: "absolute", left: 64, top: 1420 }}>
        <Label pad="10px 18px 12px" style={{ ...label(26, C.ink, 0.16) }}>Ad · 0:05</Label>
      </div>
      <div style={{ position: "absolute", left: 650, top: 1400, width: 366, height: 92, borderRadius: 18, background: C.glass, border: `1px solid ${C.line}`, display: "flex", alignItems: "center", justifyContent: "center", gap: 14, ...text(38, C.white, 700) }}>
        Skip Ad <span style={{ fontSize: 30 }}>▶|</span>
      </div>
    </div>
  );
};

const Ads: React.FC<BeatProps> = ({ t, f }) => {
  const frozen = t >= 14.98;
  const sc = frozen ? lerp(1.0, 1.1, expoOut(prog(t, 14.98, 0.4))) : snapIn(t, 14.5);
  return (
    <>
      <Footage frame={f} scale={sc} filter={frozen ? "grayscale(1) contrast(1.42)" : undefined} />
      <AdUI t={t} gone={0} />
    </>
  );
};

const NotAds: React.FC<BeatProps> = ({ t, f }) => {
  const sc = (t < 16.66 ? 1.16 : 1.3) * snapIn(t, t < 16.66 ? 15.3833 : 16.66);
  const cur = easeInOut(prog(t, 15.39, 0.33));
  const gone = expoOut(prog(t, 15.8, 0.3));
  const strike = expoOut(prog(t, 16.12, 0.35));
  return (
    <>
      <Footage frame={f} scale={sc} />
      <PopWord t={t} t0={15.95} style={{ left: 700, top: 300, ...display(230, C.white, 800), textShadow: "0 10px 40px rgba(0,0,0,0.5)" }}>
        AD
        <div style={{ position: "absolute", left: -20, top: 96, width: 340 * strike, height: 14, borderRadius: 7, background: C.yellow, transform: "rotate(-12deg)", transformOrigin: "left center", boxShadow: "0 0 18px rgba(238,255,0,0.5)" }} />
      </PopWord>
      <AdUI t={t} gone={gone} />
      {t < 16.1 ? <Cursor x={lerp(560, 840, cur)} y={lerp(1700, 1440, cur)} pressed={within(t, 15.72, 15.82)} /> : null}
    </>
  );
};

// ============ 09 DELIVERED: "I delivered over 2,000 videos." ============
const FILES = ["FINAL.mp4", "FINAL_v2.mp4", "FINAL_FINAL.mp4", "reel_07.mp4", "ad_cut_3.mp4", "yt_ep12.mp4", "client_v9.mp4", "reel_31.mp4", "promo_4k.mp4", "FINAL_v3.mp4", "teaser.mp4", "ad_15s.mp4", "vlog_22.mp4", "reel_88.mp4", "launch.mp4", "FINAL_ok.mp4", "short_41.mp4", "edit_v12.mp4", "reel_120.mp4", "real_FINAL.mp4"];
const Delivered: React.FC<BeatProps> = ({ t, f }) => {
  const n = Math.round(lerp(0, 2000, easeOut(prog(t, 18.28, 0.6))));
  const plus = t >= 18.86;
  return (
    <>
      <Stage cy={40} light={0.08} />
      {FILES.map((name, i) => {
        const col = i % 5;
        const row = Math.floor(i / 5);
        const p = reveal(t, 17.85 + i * 0.045, 0.4);
        if (p <= 0) return null;
        return (
          <div key={i} style={{ position: "absolute", left: 46 + col * 202, top: 640 + row * 300, width: 180, display: "flex", flexDirection: "column", alignItems: "center", gap: 8, opacity: p * 0.55, transform: `translateY(${(1 - p) * 30}px)` }}>
            <Thumb i={i * 2 + 1} w={150} style={{ borderRadius: 12 }} />
            <span style={{ ...text(19, C.muted, 600), whiteSpace: "nowrap" }}>{name}</span>
          </div>
        );
      })}
      <Footage frame={f} person scale={1.0 * snapIn(t, 17.8167)} ox={540} oy={1530} ty={BOTTOM_ANCHOR} shadow />
      {t >= 18.28 ? (
        <div style={{ position: "absolute", left: 80, top: 290, ...display(230, C.white, 800), fontVariantNumeric: "tabular-nums", textShadow: "0 10px 40px rgba(0,0,0,0.5)" }}>
          {n.toLocaleString("en-US")}
          <span style={{ color: C.yellow, opacity: plus ? 1 : 0 }}>+</span>
        </div>
      ) : null}
      <MaskLine t={t} t0={18.92} style={{ left: 88, top: 510 }}>
        <span style={{ ...label(34, C.white, 0.34) }}>Videos delivered</span>
      </MaskLine>
    </>
  );
};

// ============ 10 TEAM: "And my team is currently handling 60+ clients." ============
const MSGS = [
  { who: "Client · Dubai", msg: "Can we make it pop more?", t0: 20.33 },
  { who: "Client · Kolkata", msg: "Need it by tonight?", t0: 20.69 },
  { who: "Client · London", msg: "This is fire. Next one?", t0: 21.0 },
];
const Team: React.FC<BeatProps> = ({ t, f }) => {
  if (within(t, 21.8, 22.5)) {
    return (
      <>
        <Stage cy={45} light={0.12} />
        <MaskLine t={t} t0={21.8} d={0.5} style={{ left: 0, width: W, top: 560, textAlign: "center" }}>
          <span style={{ ...display(500, C.white, 800) }}>
            60<span style={{ color: C.yellow }}>+</span>
          </span>
        </MaskLine>
        <MaskLine t={t} t0={21.9} d={0.5} style={{ left: 0, width: W, top: 1050, textAlign: "center" }}>
          <span style={{ ...label(44, C.white, 0.5) }}>Clients</span>
        </MaskLine>
      </>
    );
  }
  const sc = (t < 21.8 ? 1.1 : 1.0) * snapIn(t, t < 21.8 ? 20.05 : 22.5);
  const visible = MSGS.filter((m) => t >= m.t0);
  return (
    <>
      <Footage frame={f} scale={sc} />
      {t < 21.8 ? (
        <PopWord t={t} t0={20.1} style={{ left: 64, top: 320 }}>
          <Chip dot={C.yellow} size={28}>My team · live</Chip>
        </PopWord>
      ) : null}
      {t < 21.8
        ? visible.map((m, i) => {
            const fromTop = visible.length - 1 - i;
            const p = expoOut(prog(t, m.t0, 0.4));
            return (
              <div key={m.msg} style={{ position: "absolute", left: 64, top: 1404 - fromTop * 126 + (1 - p) * 120, width: 952, height: 112, opacity: p, background: "rgba(28,28,31,0.82)", border: `1px solid ${C.line}`, borderRadius: 30, display: "flex", alignItems: "center", gap: 22, padding: "0 26px", boxShadow: "0 24px 50px rgba(0,0,0,0.45)" }}>
                <span style={{ width: 62, height: 62, borderRadius: 16, background: C.yellow, display: "flex", alignItems: "center", justifyContent: "center", ...display(34, C.ink, 800) }}>{m.who.split("· ")[1][0]}</span>
                <span style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{ ...label(18, C.muted, 0.16) }}>{m.who} · now</span>
                  <span style={{ ...text(34, C.white, 600) }}>{m.msg}</span>
                </span>
              </div>
            );
          })
        : null}
    </>
  );
};

// ============ 11 EVERY FRAME: "Aur har ek… frame by frame." (stepped, stop-motion film) ============
const EveryFrame: React.FC<BeatProps> = ({ t, f }) => {
  const start = 698;
  const step = Math.floor((f - start) / 4);
  const src = start + step * 4;
  const zoom = t >= 24.75 ? 1.36 : t >= 24.47 ? 1.22 : t >= 24.09 ? 1.1 : 1.0;
  const jit = ((step * 37) % 5) - 2;
  return (
    <>
      <AbsoluteFill style={{ background: C.black }} />
      <Footage frame={src} scale={zoom} ty={jit} filter="grayscale(1) contrast(1.38) brightness(0.95)" />
      <Vignette strength={0.55} />
      {[0, 984].map((x) => (
        <div key={x} style={{ position: "absolute", left: x, top: 0, width: 96, height: H, background: C.black }}>
          {Array.from({ length: 15 }).map((_, i) => (
            <span key={i} style={{ position: "absolute", left: 30, top: i * 140 + 40 + jit, width: 36, height: 54, borderRadius: 8, background: "#2A2A2D" }} />
          ))}
        </div>
      ))}
      <div style={{ position: "absolute", left: 0, width: W, top: 250, textAlign: "center", ...display(104, C.white, 800), fontVariantNumeric: "tabular-nums" }}>
        <span style={{ ...label(28, C.muted, 0.3), marginRight: 16 }}>Frame</span>
        {String(src + 1).padStart(4, "0")}
      </div>
    </>
  );
};

// ============ 12 FOUND: "Found it?" (autofocus reticle) ============
const Found: React.FC<BeatProps> = ({ t, f }) => {
  const sc = 1.42 * snapIn(t, 25.4167);
  const size = lerp(820, 560, expoOut(prog(t, 25.45, 0.35)));
  const blink = within(t, 25.81, 25.86) || within(t, 25.92, 25.97);
  return (
    <>
      <Footage frame={f} scale={sc} ox={540} oy={600} />
      <Vignette strength={0.45} />
      {!blink ? <Brackets x={540 - size / 2} y={600 - size / 2} w={size} h={size} len={80} color={C.yellow} width={5} /> : null}
    </>
  );
};

// ============ 13 DM: "DM me what it says." (electric blue is this frame's one accent) ============
const DM: React.FC<BeatProps> = ({ t, f }) => {
  const up = expoOut(prog(t, 26.38, 0.45));
  const typing = within(t, 26.93, 27.12);
  const sent = t >= 27.12;
  return (
    <>
      <Footage frame={f} scale={snapIn(t, 26.3833) * push(t, 26.38, 27.82)} />
      <div style={{ position: "absolute", left: 64, top: lerp(1920, 960, up), width: 952, height: 470, background: "rgba(22,22,24,0.92)", borderRadius: 44, border: `1px solid ${C.line}`, overflow: "hidden", boxShadow: "0 50px 100px rgba(0,0,0,0.55)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 22, padding: "26px 34px", borderBottom: `1px solid ${C.line}` }}>
          <div style={{ width: 84, height: 84, borderRadius: 42, overflow: "hidden" }}>
            <Thumb i={20} w={84} style={{ marginTop: -20 }} />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ ...text(36, C.white, 700) }}>Aminur</span>
            <span style={{ ...text(24, C.muted, 500) }}>Video Editor · Active now</span>
          </div>
        </div>
        <div style={{ padding: "28px 34px", display: "flex", flexDirection: "column", gap: 20 }}>
          <PopWord t={t} t0={26.45} style={{ position: "relative" }}>
            <div style={{ background: "#2C2C2F", borderRadius: 30, padding: "18px 28px", maxWidth: 660, ...text(36, C.white, 500) }}>Found the frame? DM me what it says.</div>
          </PopWord>
          <div style={{ alignSelf: "flex-end", position: "relative", height: 90 }}>
            {typing ? (
              <div style={{ background: C.blue, borderRadius: 30, padding: "24px 30px", display: "flex", gap: 12 }}>
                {[0, 1, 2].map((i) => (
                  <span key={i} style={{ width: 14, height: 14, borderRadius: 7, background: C.white, opacity: 0.4 + 0.6 * Math.abs(Math.sin(t * 12 + i)) }} />
                ))}
              </div>
            ) : null}
            {sent ? (
              <div style={{ background: C.blue, borderRadius: 30, padding: "18px 28px", display: "flex", gap: 14, transform: `scale(${lerp(0.9, 1, expoOut(prog(t, 27.12, 0.3)))})`, transformOrigin: "right center" }}>
                <span style={{ width: 150, height: 38, background: "rgba(255,255,255,0.92)", borderRadius: 8 }} />
                <span style={{ width: 120, height: 38, background: "rgba(255,255,255,0.92)", borderRadius: 8 }} />
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </>
  );
};

// ============ 14 NAHI MILA: "Nahi mila na?" (system alert as the caption) ============
const NahiMila: React.FC<BeatProps> = ({ t, f }) => {
  const p = expoOut(prog(t, 27.82, 0.35));
  const shake = within(t, 28.34, 28.6) ? Math.sin((t - 28.34) * 70) * 16 * (1 - prog(t, 28.34, 0.26)) : 0;
  return (
    <>
      <Footage frame={f} scale={1.16 * snapIn(t, 27.8167)} filter={`blur(${(p * 4).toFixed(2)}px) brightness(${lerp(1, 0.7, p).toFixed(3)})`} />
      <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, transform: `translateX(${shake}px)` }}>
        <div style={{ position: "absolute", left: 130, top: 860, width: 820, padding: "52px 50px 44px", borderRadius: 40, background: "rgba(30,30,33,0.9)", border: `1px solid ${C.line}`, boxShadow: "0 60px 120px rgba(0,0,0,0.6)", display: "flex", flexDirection: "column", alignItems: "center", gap: 18, opacity: p, transform: `scale(${lerp(0.9, 1, p)})` }}>
          <div style={{ width: 110, height: 110, borderRadius: 55, background: C.yellow, display: "flex", alignItems: "center", justifyContent: "center", ...display(76, C.ink, 800) }}>!</div>
          <span style={{ ...text(52, C.white, 700), marginTop: 10 }}>Frame not found</span>
          <span style={{ ...text(36, C.muted, 500) }}>Nahi mila na?</span>
          <div style={{ display: "flex", gap: 18, marginTop: 22, width: "100%" }}>
            <span style={{ flex: 1, textAlign: "center", padding: "20px 0", borderRadius: 18, background: "rgba(255,255,255,0.1)", ...text(32, C.white, 600) }}>Give up</span>
            <span style={{ flex: 1, textAlign: "center", padding: "20px 0", borderRadius: 18, background: C.yellow, ...text(32, C.ink, 700) }}>Watch again</span>
          </div>
        </div>
      </div>
    </>
  );
};

// ============ 15 EDITOR: "Tabhi toh editor main hoon." (EDITOR behind the cut-out) ============
const Editor: React.FC<BeatProps> = ({ t, f }) => {
  const hit = t >= 29.46;
  const drift = (t - 28.92) * 70;
  return (
    <>
      <Stage cy={44} light={0.1} />
      {[0, 1, 2, 3, 4, 5].map((r) => {
        const dir = r % 2 === 0 ? -1 : 1;
        if (r === 1) {
          return (
            <MaskLine key={r} t={t} t0={29.46} d={0.5} style={{ left: 0, width: W, top: 230 + r * 245, textAlign: "center" }}>
              <span style={{ ...display(290, C.yellow, 800) }}>EDITOR</span>
            </MaskLine>
          );
        }
        return (
          <div key={r} style={{ position: "absolute", left: -300 + dir * drift - (r % 2) * 180, top: 230 + r * 245, ...display(280, "transparent", 800), WebkitTextStroke: "2px rgba(255,255,255,0.2)", opacity: hit ? 1 : 0.6 }}>
            EDITOR EDITOR EDITOR
          </div>
        );
      })}
      <Footage frame={f} person scale={1.1 * snapIn(t, 28.9167)} ox={540} oy={1530} ty={BOTTOM_ANCHOR} shadow />
    </>
  );
};

// ============ 16 TWICE: "I make videos that people watch twice." ============
const Twice: React.FC<BeatProps> = ({ t, f }) => {
  if (within(t, 32.7, 33.25)) {
    const k = easeIn(prog(t, 32.7, 0.55));
    const src = Math.round(lerp(981, 0, k) / 2) * 2;
    const two = reveal(t, 32.81, 0.4);
    return (
      <>
        <Footage frame={src} filter="contrast(1.15) saturate(0.7)" />
        {[0, 1, 2].map((i) => (
          <div key={i} style={{ position: "absolute", left: 0, top: ((f * 131 + i * 577) % 1400) + 250, width: W, height: 3 + i * 3, background: "rgba(255,255,255,0.35)" }} />
        ))}
        <div style={{ position: "absolute", left: 64, top: 300 }}>
          <Chip dot={C.yellow} size={26}>◀◀ Rewind</Chip>
        </div>
        {t >= 32.81 ? (
          <div style={{ position: "absolute", left: 0, width: W, top: 640, textAlign: "center", ...display(420, C.yellow, 800), opacity: two, transform: `scale(${lerp(1.15, 1, two)})`, filter: two < 0.98 ? `blur(${((1 - two) * 16).toFixed(2)}px)` : undefined, textShadow: "0 20px 60px rgba(0,0,0,0.5)" }}>
            2×
          </div>
        ) : null}
      </>
    );
  }
  if (t >= 33.25) return <Footage frame={f} scale={snapIn(t, 33.25)} />;
  const step = t >= 32.09 ? 3 : t >= 31.53 ? 2 : t >= 31.02 ? 1 : 0;
  const base = [1.0, 1.18, 1.0, 1.3][step];
  const at = [30.65, 31.02, 31.53, 32.09][step];
  const play = within(t, 31.02, 31.53) ? reveal(t, 31.02, 0.35) : 0;
  return (
    <>
      <Footage frame={f} scale={base * snapIn(t, at)} filter={step === 3 ? "grayscale(1) contrast(1.35)" : undefined} />
      {play > 0 ? (
        <div style={{ position: "absolute", left: 90, top: 340, width: 200, height: 200, borderRadius: 100, background: "rgba(255,255,255,0.14)", border: "1px solid rgba(255,255,255,0.35)", transform: `scale(${lerp(0.85, 1, play)})`, opacity: play, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 30px 60px rgba(0,0,0,0.4)" }}>
          <svg width="76" height="88" viewBox="0 0 96 110">
            <path d="M14 6 L90 55 L14 104 Z" fill={C.white} />
          </svg>
        </div>
      ) : null}
      {step === 3 ? (
        <div style={{ position: "absolute", left: 64, top: 300, opacity: reveal(t, 32.09, 0.3) }}>
          <Chip dot={C.yellow} size={26}>Watch time ▲ 2×</Chip>
        </div>
      ) : null}
    </>
  );
};

// ============ 17/18 SERVICE + BIO ============
const SERVICES = [
  { n: "01", s: "Reels & Shorts", t0: 33.78 },
  { n: "02", s: "YouTube long-form", t0: 34.08 },
  { n: "03", s: "Ads people don't skip", t0: 34.46 },
];
const Service: React.FC<BeatProps> = ({ t, f }) => {
  const slide = expoOut(prog(t, 33.62, 0.5));
  const bio = t >= 35.8833;
  const hl = expoOut(prog(t, 36.76, 0.4));
  return (
    <>
      <Stage cx={70} cy={70} light={0.12} />
      {!bio ? (
        <>
          <MaskLine t={t} t0={33.62} style={{ left: 64, top: 290 }}>
            <span style={{ ...display(130, C.white, 800) }}>Need an</span>
          </MaskLine>
          <MaskLine t={t} t0={33.7} style={{ left: 64, top: 410 }}>
            <span style={{ ...display(130, C.yellow, 800) }}>editor?</span>
          </MaskLine>
          {SERVICES.map((s, i) => (
            <PopWord key={s.n} t={t} t0={s.t0} style={{ left: 64, top: 620 + i * 150 }}>
              <div style={{ width: 660, height: 126, borderRadius: 26, background: C.glass, border: `1px solid ${C.line}`, display: "flex", alignItems: "center", gap: 28, padding: "0 30px", boxShadow: "0 30px 60px rgba(0,0,0,0.45)" }}>
                <span style={{ ...display(64, C.yellow, 800), fontVariantNumeric: "tabular-nums" }}>{s.n}</span>
                <span style={{ ...text(42, C.white, 600) }}>{s.s}</span>
              </div>
            </PopWord>
          ))}
        </>
      ) : (
        <>
          <div style={{ position: "absolute", left: 64, top: lerp(1900, 290, expoOut(prog(t, 35.88, 0.5))), width: 952, background: C.glass, border: `1px solid ${C.line}`, borderRadius: 40, boxShadow: "0 50px 100px rgba(0,0,0,0.55)", padding: 42, display: "flex", flexDirection: "column", gap: 24 }}>
            <div style={{ display: "flex", gap: 30, alignItems: "center" }}>
              <div style={{ width: 150, height: 150, borderRadius: 75, overflow: "hidden", boxShadow: `0 0 0 4px ${C.yellow}` }}>
                <Thumb i={20} w={150} style={{ marginTop: -36 }} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <span style={{ ...text(58, C.white, 700) }}>Aminur</span>
                <span style={{ ...text(32, C.muted, 500) }}>Video Editor</span>
                <span style={{ ...label(22, C.white, 0.14) }}>2,000+ videos · 60+ clients</span>
              </div>
            </div>
            <div style={{ position: "relative", alignSelf: "flex-start", ...text(42, C.white, 600), padding: "4px 0 10px" }}>
              Contact number <span style={{ color: C.yellow }}>→</span> in bio
              <span style={{ position: "absolute", left: 0, bottom: 0, height: 5, borderRadius: 3, width: `${hl * 100}%`, background: C.yellow }} />
            </div>
            <div style={{ display: "flex", gap: 18 }}>
              <span style={{ flex: 1, textAlign: "center", padding: "20px 0", background: C.white, borderRadius: 18, ...text(34, C.ink, 700) }}>Message</span>
              <span style={{ flex: 1, textAlign: "center", padding: "20px 0", background: "rgba(255,255,255,0.1)", borderRadius: 18, ...text(34, C.white, 600) }}>Follow</span>
            </div>
          </div>
          <PopWord t={t} t0={36.15} style={{ left: 64, top: 890, display: "flex", alignItems: "center", gap: 22 }}>
            <span style={{ ...display(120, C.yellow, 800) }}>↑</span>
            <span style={{ ...label(32, C.white, 0.26), lineHeight: 1.3 }}>
              Tap my
              <br />
              profile
            </span>
          </PopWord>
        </>
      )}
      <Footage frame={f} person scale={0.7} ox={540} oy={1530} tx={lerp(760, 270, slide)} ty={BOTTOM_ANCHOR} shadow />
    </>
  );
};

// ============ END CARD: "Shuruaat… isi video se." (bookends the hook so the reel loops) ============
const EndCard: React.FC<{ t: number }> = ({ t }) => {
  const q = reveal(t, 37.36, 0.5);
  return (
    <>
      <AbsoluteFill style={{ background: C.stage }} />
      <div style={{ position: "absolute", left: 0, width: W, top: 60, textAlign: "center", ...display(900, C.yellow, 800), lineHeight: 1, opacity: q, transform: `scale(${lerp(0.9, 1 + 0.02 * Math.sin(t * 7), q)}) rotate(7deg)`, transformOrigin: "50% 60%", filter: q < 0.98 ? `blur(${((1 - q) * 20).toFixed(2)}px)` : undefined }}>?</div>
      <Vignette strength={0.85} />
      <MaskLine t={t} t0={37.4} style={{ left: 90, top: 1050 }}>
        <span style={{ ...display(140, C.white, 800) }}>Shuruaat…</span>
      </MaskLine>
      <MaskLine t={t} t0={37.78} style={{ left: 84, top: 1190 }}>
        <span style={{ ...display(170, C.yellow, 800) }}>isi video se.</span>
      </MaskLine>
      <div style={{ position: "absolute", left: 94, top: 1430, ...label(32, C.white, 0.3), opacity: prog(t, 37.95, 0.3) }}>Aminur · Video Editor</div>
      <div style={{ position: "absolute", left: 94, top: 1484, ...label(22, C.muted, 0.22), opacity: prog(t, 38.2, 0.3) }}>↺ watch again · find the frame</div>
    </>
  );
};

// ============ THE HIDDEN FRAME (exactly one frame long) ============
const Hidden: React.FC<{ f: number }> = ({ f }) => (
  <>
    <AbsoluteFill style={{ background: C.yellow }} />
    <div style={{ position: "absolute", left: 84, top: 330, ...label(40, C.ink, 0.32) }}>You found it.</div>
    <div style={{ position: "absolute", left: 76, top: 520, ...display(280, C.ink, 800), lineHeight: 0.92 }}>
      {SECRET.split(" ").map((w) => (
        <div key={w}>{w}</div>
      ))}
    </div>
    <div style={{ position: "absolute", left: 84, top: 1150, ...text(54, C.ink, 700) }}>DM me these 2 words.</div>
    <div style={{ position: "absolute", left: 84, top: 1236, ...label(24, C.ink, 0.22), opacity: 0.7 }}>
      Frame {String(f + 1).padStart(4, "0")} of {TOTAL_FRAMES}
    </div>
  </>
);

// ---------- per-beat caption placement ----------
const captionOpts = (id: string, t: number) => {
  switch (id) {
    case "hook":
    case "find":
    case "name":
    case "delivered":
    case "dm":
    case "nahimila":
      return { hide: true };
    case "frames":
      return { hide: t < 5.58 };
    case "numbers":
      return { hide: t < 10.58 || t >= 11.24 };
    case "tenmin":
      return { hide: within(t, 12.56, 13.75) };
    case "team":
      return { hide: t < 22.5 };
    case "twice":
      return { hide: within(t, 32.7, 33.25) };
    case "editor":
      return { y: 1560 };
    case "service":
    case "bio":
      return { y: 1170, left: true, width: 560 };
    default:
      return {};
  }
};

const BEATS: Record<string, React.FC<BeatProps>> = {
  hook: Hook,
  find: Find,
  name: Name,
  frames: Frames,
  movies: Movies,
  numbers: Numbers,
  tenmin: TenMin,
  ads: Ads,
  notads: NotAds,
  delivered: Delivered,
  team: Team,
  everyframe: EveryFrame,
  found: Found,
  dm: DM,
  nahimila: NahiMila,
  editor: Editor,
  twice: Twice,
  service: Service,
  bio: Service,
};

// Big hits: the frame gives a short, damped shake and a soft flash, in sync with the impact sounds.
const IMPACTS = [0.68, 3.22, 8.78, 9.33, 10.06, 18.86, 21.8, 29.46, 32.81, 37.8];
const impactAt = (t: number) => {
  const hit = IMPACTS.find((h) => t >= h && t < h + 0.2);
  if (hit === undefined) return { x: 0, y: 0, flash: 0 };
  const k = 1 - (t - hit) / 0.2;
  const n = Math.round((t - hit) * FPS);
  return { x: (rnd(hit * 100 + n) - 0.5) * 18 * k, y: (rnd(hit * 77 + n * 3) - 0.5) * 18 * k, flash: 0.2 * Math.max(0, 1 - (t - hit) / 0.1) };
};

// Picture breathes with the music: a small zoom kick on every beat, a bigger one on each bar's downbeat.
// Off during the muffled hook (music hasn't dropped yet) and the record-scratch freeze.
const beatPulse = (t: number) => {
  if (t < 2.9 || within(t, 14.98, 15.38)) return 1;
  const last = (arr: number[]) => arr.filter((b) => b <= t + 1e-4).pop();
  const b = last(MUSIC_BEATS);
  const bar = last(MUSIC_BARS);
  const kick = (at: number | undefined, amt: number) => (at === undefined || t - at > 0.18 ? 0 : amt * (1 - (t - at) / 0.18) ** 2);
  return 1 + kick(b, 0.005) + kick(bar, 0.011);
};

export const Reel: React.FC = () => {
  const [handle] = useState(() => delayRender("Loading fonts"));
  useEffect(() => {
    loadFonts().then(() => continueRender(handle));
  }, [handle]);

  const f = useCurrentFrame();
  const t = f / FPS;

  if (f === HIDDEN_FRAME) {
    return (
      <AbsoluteFill style={{ background: C.black, overflow: "hidden" }}>
        <Hidden f={f} />
      </AbsoluteFill>
    );
  }
  const hit = impactAt(t);
  if (f >= SELECTS_FRAMES) {
    return (
      <AbsoluteFill style={{ background: C.black, overflow: "hidden" }}>
        <AbsoluteFill style={{ transform: `translate(${hit.x}px, ${hit.y}px)` }}>
          <EndCard t={t} />
        </AbsoluteFill>
        <FrameCounter frame={f} scramble />
      </AbsoluteFill>
    );
  }
  const clip = clipAt(t);
  const Beat = BEATS[clip.id];
  const rewinding = clip.id === "twice" && within(t, 32.7, 33.25);
  const counterFrame = rewinding ? Math.round(lerp(981, 0, easeIn(prog(t, 32.7, 0.55)))) : f;
  return (
    <AbsoluteFill style={{ background: C.black, overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `translate(${hit.x}px, ${hit.y}px) scale(${(hit.x || hit.y ? 1.02 : 1) * beatPulse(t)})` }}>
        <Beat t={t} f={f} />
      </AbsoluteFill>
      {hit.flash > 0 ? <AbsoluteFill style={{ background: C.white, opacity: hit.flash }} /> : null}
      <Captions t={t} opts={captionOpts(clip.id, t)} />
      {clip.id !== "everyframe" ? <FrameCounter frame={counterFrame} scramble={clip.id === "hook"} /> : null}
    </AbsoluteFill>
  );
};
