import React, { useEffect, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile, useCurrentFrame } from "remotion";
import { clipAt } from "./data";
import {
  Captions,
  Cursor,
  Footage,
  FrameCounter,
  Label,
  Paper,
  PopInline,
  PopWord,
  Selection,
  Thumb,
  Window,
  clamp,
  display,
  easeIn,
  easeInOut,
  easeOut,
  lerp,
  pop,
  prog,
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

// The matte ends where the table hides his body (source y ~1530). Cut-out stickers are pushed down
// by this much so that hard edge always sits below the bottom of the frame instead of mid-shot.
const BOTTOM_ANCHOR = 405;

// quick snap-zoom at the start of every clip so jump cuts read as intentional
const snapIn = (t: number, start: number) => 1 + 0.05 * (1 - easeOut(prog(t, start, 0.13)));

// ============ 00 HOOK: "I hid one frame in this video." (low-key, redacted, a giant ? behind him) ============
// Sprocket bands for the film-gate look (hook + frame-by-frame beat).
const Sprockets: React.FC<{ offset: number; width?: number }> = ({ offset, width = 92 }) => (
  <>
    {[0, W - width].map((x) => (
      <div key={x} style={{ position: "absolute", left: x, top: 0, width, height: H, background: C.black, overflow: "hidden" }}>
        {Array.from({ length: 16 }).map((_, i) => (
          <span key={i} style={{ position: "absolute", left: width / 2 - 19, top: i * 140 - 140 + offset, width: 38, height: 56, borderRadius: 8, background: "#2A2A2A" }} />
        ))}
      </div>
    ))}
  </>
);

const Hook: React.FC<BeatProps> = ({ t, f }) => {
  const push = lerp(1.1, 1.2, easeInOut(prog(t, 0, 1.87)));
  const flicker = 0.88 + 0.14 * rnd(f + 3);
  const look = `grayscale(0.82) contrast(1.32) brightness(${(0.6 * flicker).toFixed(3)})`;
  const glitch = within(t, 0.68, 0.76) || t >= 1.74;
  const jx = glitch ? (rnd(f * 3) - 0.5) * 70 : 0;
  const qScale = 1 + 0.025 * Math.sin(t * 8);
  const redact = within(t, 0.4, 0.68);
  const typed = "IN THIS VIDEO.".slice(0, Math.max(0, Math.floor((t - 0.96) / 0.028)));
  return (
    <>
      <AbsoluteFill style={{ background: C.black }} />
      <AbsoluteFill style={{ transform: `translateX(${jx}px)` }}>
        <Footage frame={f} scale={push} filter={look} />
        <div style={{ position: "absolute", left: 600, top: 150, ...display(980, C.yellow), lineHeight: 1, transform: `scale(${qScale}) rotate(8deg)`, transformOrigin: "50% 60%" }}>?</div>
        <Footage frame={f} scale={push} person filter={look} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 72% 52% at 50% 36%, rgba(0,0,0,0) 38%, rgba(0,0,0,0.82) 100%)" }} />
      <Sprockets offset={(f * 35) % 140} />
      {glitch
        ? [0, 1, 2].map((i) => (
            <div key={i} style={{ position: "absolute", left: 0, top: 240 + rnd(f * 5 + i) * 1300, width: W, height: 4 + rnd(f + i * 9) * 16, background: i === 1 ? C.yellow : "rgba(255,255,255,0.7)" }} />
          ))
        : null}
      <div style={{ position: "absolute", left: 130, top: 1040, display: "flex", gap: 30, ...display(150, C.white) }}>
        <PopInline t={t} t0={-0.2}>I</PopInline>
        <PopInline t={t} t0={0.14}>HID</PopInline>
        <PopInline t={t} t0={0.4}>ONE</PopInline>
      </div>
      {redact ? (
        <div style={{ position: "absolute", left: 120, top: 1196, width: 760, height: 214, background: C.yellow, opacity: rnd(f) < 0.15 ? 0.55 : 1, display: "flex", alignItems: "center", justifyContent: "center", transform: "rotate(-2deg)" }}>
          <span style={{ ...text(46, C.ink, 800), letterSpacing: "0.5em" }}>REDACTED</span>
        </div>
      ) : null}
      {t >= 0.68 ? (
        <div style={{ position: "absolute", left: 112, top: 1190, ...display(250, C.ink), transform: `translateX(${glitch ? (rnd(f + 1) - 0.5) * 40 : 0}px) scale(${lerp(1.18, 1, easeOut(prog(t, 0.68, 0.12)))})` }}>
          <Label rotate={-2}>FRAME</Label>
        </div>
      ) : null}
      <div style={{ position: "absolute", left: 130, top: 1452, ...text(56, C.white, 800), letterSpacing: "0.14em" }}>
        {typed}
        {t >= 0.96 && Math.floor(t * 6) % 2 === 0 ? <span style={{ color: C.yellow }}>▍</span> : null}
      </div>
    </>
  );
};

// ============ 01 FIND: "Dhoondh ke dikhao." (scanner over B/W) ============
const Find: React.FC<BeatProps> = ({ t, f }) => {
  const st = 1.8667;
  const scanY = lerp(240, 1520, easeInOut(prog(t, st + 0.02, 0.95)));
  const sc = lerp(0.92, 1, easeOut(prog(t, st, 0.14)));
  const corner = (x: number, y: number, sx: number, sy: number, k: number) => (
    <div key={k} style={{ position: "absolute", left: x, top: y, width: 80, height: 80, borderLeft: sx > 0 ? `7px solid ${C.white}` : undefined, borderRight: sx < 0 ? `7px solid ${C.white}` : undefined, borderTop: sy > 0 ? `7px solid ${C.white}` : undefined, borderBottom: sy < 0 ? `7px solid ${C.white}` : undefined }} />
  );
  return (
    <>
      <Footage frame={f} scale={sc} filter="grayscale(1) contrast(1.18) brightness(0.92)" />
      {[360, 720].map((x) => (
        <div key={x} style={{ position: "absolute", left: x, top: 0, width: 2, height: H, background: "rgba(255,255,255,0.32)" }} />
      ))}
      {[640, 1280].map((y) => (
        <div key={y} style={{ position: "absolute", top: y, left: 0, height: 2, width: W, background: "rgba(255,255,255,0.32)" }} />
      ))}
      {[corner(56, 300, 1, 1, 0), corner(944, 300, -1, 1, 1), corner(56, 1460, 1, -1, 2), corner(944, 1460, -1, -1, 3)]}
      <div style={{ position: "absolute", left: 0, top: scanY, width: W, height: 8, background: C.yellow }} />
      <div style={{ position: "absolute", left: 64, top: 1030, display: "flex", gap: 34, ...display(150, C.white) }}>
        <PopInline t={t} t0={1.87}>DHOONDH</PopInline>
        <PopInline t={t} t0={2.17}>KE</PopInline>
      </div>
      <PopWord t={t} t0={2.29} from={0.4} style={{ left: 50, top: 1190, ...display(205, C.ink) }}>
        <Label rotate={-3}>DIKHAO.</Label>
      </PopWord>
    </>
  );
};

// ============ 02 NAME: "I am Aminur, a video editor." (name behind a B/W cut-out on yellow) ============
const Name: React.FC<BeatProps> = ({ t, f }) => {
  const st = 2.9;
  const ps = 1.04 * snapIn(t, st);
  const nameP = pop(t, 3.22, 0.18);
  const cur = easeInOut(prog(t, 3.95, 0.3));
  const clicked = t >= 4.3;
  return (
    <>
      <Paper tint={C.yellow} />
      <PopWord t={t} t0={2.9} style={{ left: 70, top: 330, ...text(60, C.ink, 800) }}>
        I AM
      </PopWord>
      {t >= 3.22 ? (
        <div style={{ position: "absolute", left: 0, width: W, top: 410, textAlign: "center", ...display(262, C.ink), transform: `scale(${lerp(1.35, 1, clamp(nameP))})`, opacity: clamp(prog(t, 3.22, 0.04)) }}>
          AMINUR
        </div>
      ) : null}
      <Footage frame={f} person scale={ps} ox={540} oy={1530} ty={BOTTOM_ANCHOR} sticker={9} filter="grayscale(1) contrast(1.12)" />
      <PopWord t={t} t0={3.92} style={{ left: 96, top: 1300 }}>
        <div style={{ position: "relative" }}>
          <Label bg={C.black} color={C.white} rotate={-4} pad="16px 30px 20px" style={{ ...text(70, C.white, 800) }}>
            VIDEO EDITOR
          </Label>
          {clicked ? <Selection x={-14} y={-26} w={580} h={140} color={C.white} p={prog(t, 4.3, 0.1)} /> : null}
        </div>
      </PopWord>
      {t >= 3.92 ? <Cursor x={lerp(900, 560, cur)} y={lerp(1560, 1360, cur)} pressed={within(t, 4.28, 4.38)} /> : null}
    </>
  );
};

// ============ 03 FRAMES: "Frames? Woh toh mera game hai." ============
const Frames: React.FC<BeatProps> = ({ t, f }) => {
  if (t < 5.58) {
    const slide = easeOut(prog(t, 5.0, 0.58));
    const x0 = lerp(120, -420, slide);
    return (
      <>
        <AbsoluteFill style={{ background: C.black }} />
        <div style={{ position: "absolute", left: x0, top: 640, height: 640, width: 2400, background: "#111" }}>
          {Array.from({ length: 40 }).map((_, i) => (
            <React.Fragment key={i}>
              <span style={{ position: "absolute", left: 14 + i * 60, top: 14, width: 30, height: 22, borderRadius: 5, background: C.gray1 }} />
              <span style={{ position: "absolute", left: 14 + i * 60, bottom: 14, width: 30, height: 22, borderRadius: 5, background: C.gray1 }} />
            </React.Fragment>
          ))}
          {[4, 13, 22, 31, 40, 9].map((k, i) => (
            <Thumb key={i} i={k} w={300} style={{ position: "absolute", left: 20 + i * 330, top: 52, height: 536 }} />
          ))}
        </div>
        <PopWord t={t} t0={5.02} style={{ left: 64, top: 330, ...display(230, C.white) }}>
          FRAMES<span style={{ color: C.yellow }}>?</span>
        </PopWord>
        <div style={{ position: "absolute", left: 64, top: 1340, ...text(34, C.gray2, 700), letterSpacing: "0.12em" }}>
          24 FPS · 30 FPS · 60 FPS
        </div>
      </>
    );
  }
  const sc = 1.32 * snapIn(t, 5.58);
  const xp = easeOut(prog(t, 5.6, 0.8));
  return (
    <>
      <Footage frame={f} scale={sc} />
      <div style={{ position: "absolute", right: 64, top: 236, display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 10 }}>
        <span style={{ ...text(30, C.white, 800), letterSpacing: "0.1em", textShadow: "0 3px 0 rgba(0,0,0,.4)" }}>P1 · AMINUR</span>
        <div style={{ width: 300, height: 26, border: `4px solid ${C.white}`, padding: 3, background: "rgba(0,0,0,.35)" }}>
          <div style={{ width: `${xp * 100}%`, height: "100%", background: C.yellow }} />
        </div>
        <span style={{ ...text(24, C.white, 700), letterSpacing: "0.1em", opacity: 0.85 }}>SKILL {Math.round(xp * 100)}%</span>
      </div>
      {t >= 6.4 ? (
        <div style={{ position: "absolute", right: 90, top: lerp(700, 560, easeOut(prog(t, 6.4, 0.5))), opacity: 1 - prog(t, 6.75, 0.3), ...display(140, C.yellow) }}>+1</div>
      ) : null}
    </>
  );
};

// ============ 04 MOVIES: "I make 30-second reels feel like a movie." ============
const Movies: React.FC<BeatProps> = ({ t, f }) => {
  if (t < 8.74) {
    const sc = snapIn(t, 7.2667);
    const bar = prog(t, 7.27, 1.47);
    return (
      <>
        <Footage frame={f} scale={sc} />
        {t >= 7.71 ? (
          <div style={{ position: "absolute", left: 30, top: 300, ...display(400, C.white), transform: `scale(${lerp(1.4, 1, clamp(pop(t, 7.71, 0.18)))})`, transformOrigin: "left top" }}>
            30<span style={{ fontSize: 200 }}>s</span>
          </div>
        ) : null}
        <Footage frame={f} scale={sc} person />
        <div style={{ position: "absolute", left: 64, top: 1500, width: 952, height: 10, background: "rgba(255,255,255,.35)" }}>
          <div style={{ width: `${bar * 100}%`, height: "100%", background: C.white }} />
        </div>
      </>
    );
  }
  const lb = easeOut(prog(t, 8.74, 0.2));
  const bump = t >= 9.33 ? lerp(1.2, 1.14, easeOut(prog(t, 9.33, 0.25))) : 1.12;
  return (
    <>
      <Footage frame={f} scale={bump} filter="contrast(1.12) saturate(0.85)" />
      <div style={{ position: "absolute", left: 0, top: 0, width: W, height: 400 * lb, background: C.black }} />
      <div style={{ position: "absolute", left: 0, bottom: 0, width: W, height: 400 * lb, background: C.black }} />
      <div style={{ position: "absolute", left: 0, width: W, top: 292, textAlign: "center", ...text(32, C.white, 700), letterSpacing: "0.42em", opacity: prog(t, 8.95, 0.2) }}>
        A FILM BY AMINUR
      </div>
    </>
  );
};

// ============ 05 NUMBERS: "Boring numbers feel like stories." ============
const NUMS = Array.from({ length: 60 }).map((_, i) => ((i * 7919 + 13) % 9973) / 100);
const Numbers: React.FC<BeatProps> = ({ t, f }) => {
  if (t < 10.58) {
    return (
      <>
        <Paper />
        <Window x={64} y={300} w={952} h={1080} title="Q3_report_FINAL_v4.xlsx">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", padding: "20px 24px" }}>
            {["", "Q1", "Q2", "Q3", "Q4"].map((h, i) => (
              <div key={`h${i}`} style={{ ...text(30, C.black, 800), padding: "12px 8px", borderBottom: `3px solid ${C.black}` }}>{h}</div>
            ))}
            {NUMS.slice(0, 50).map((n, i) =>
              i % 5 === 0 ? (
                <div key={i} style={{ ...text(28, C.black, 700), padding: "14px 8px", borderBottom: `2px solid ${C.gray2}` }}>Row {i / 5 + 1}</div>
              ) : (
                <div key={i} style={{ ...text(30, "#8A8A8A", 500), padding: "14px 8px", borderBottom: `2px solid ${C.gray2}`, fontVariantNumeric: "tabular-nums", opacity: t >= 10.0 + (i % 17) * 0.012 ? 1 : 0 }}>
                  {n.toFixed(2)}
                </div>
              ),
            )}
          </div>
        </Window>
        {t >= 10.05 ? (
          <div style={{ position: "absolute", left: 120, top: 640, transform: `rotate(-9deg) scale(${lerp(1.7, 1, easeOut(prog(t, 10.05, 0.1)))})`, border: `14px solid ${C.black}`, padding: "6px 30px 16px", background: C.yellow, ...display(230, C.ink) }}>
            BORING.
          </div>
        ) : null}
      </>
    );
  }
  if (t < 11.24) return <Footage frame={f} scale={snapIn(t, 10.58)} />;
  const cards = [
    { k: 7, x: 170, y: 560, r: -9, d: 0 },
    { k: 23, x: 330, y: 600, r: 6, d: 0.05 },
    { k: 36, x: 250, y: 640, r: -2, d: 0.1 },
  ];
  return (
    <>
      <Paper />
      {cards.map((c, i) => {
        const p = easeOut(prog(t, 11.24 + c.d, 0.2));
        return (
          <div key={i} style={{ position: "absolute", left: c.x, top: lerp(1900, c.y, p), transform: `rotate(${c.r}deg)`, background: C.white, padding: "16px 16px 70px", boxShadow: `10px 10px 0 ${C.black}`, border: `3px solid ${C.black}` }}>
            <Thumb i={c.k} w={420} style={{ height: 560 }} />
            <span style={{ position: "absolute", left: 160, top: -22, width: 140, height: 44, background: "rgba(255,255,255,.75)", border: `2px solid ${C.gray2}`, transform: "rotate(-4deg)" }} />
            <span style={{ position: "absolute", left: 22, bottom: 16, ...text(32, C.black, 800) }}>CH. {i + 1}</span>
          </div>
        );
      })}
      <PopWord t={t} t0={11.24} style={{ left: 64, top: 300, ...display(220, C.ink) }}>
        STORIES.
      </PopWord>
    </>
  );
};

// ============ 06 TEN MINUTES: "10-minute videos feel like 2 minutes." (+ the hidden frame lives here) ============
const TenMin: React.FC<BeatProps> = ({ t, f }) => {
  if (t < 12.56) return <Footage frame={f} scale={snapIn(t, 12.1)} />;
  if (t < 13.75) {
    const ff = easeIn(prog(t, 13.0, 0.45));
    const secs = Math.round(lerp(600, 120, ff));
    const mm = Math.floor(secs / 60);
    const ss = String(secs % 60).padStart(2, "0");
    const done = t >= 13.45;
    const ph = lerp(0.04, 0.98, ff);
    return (
      <>
        <AbsoluteFill style={{ background: C.black }} />
        <div style={{ position: "absolute", left: 64, top: 320, ...text(34, C.gray2, 700), letterSpacing: "0.12em" }}>VIDEO_FINAL.mp4 · {done ? "2:00" : "10:00"}</div>
        <div style={{ position: "absolute", left: 0, width: W, top: 640, textAlign: "center", fontVariantNumeric: "tabular-nums" }}>
          {done ? (
            <span style={{ ...display(330, C.ink), display: "inline-block", transform: `scale(${lerp(1.3, 1, clamp(pop(t, 13.45, 0.16)))})` }}>
              <Label rotate={-3}>2:00</Label>
            </span>
          ) : (
            <span style={{ ...display(330, C.white) }}>
              {mm}:{ss}
            </span>
          )}
        </div>
        <div style={{ position: "absolute", left: 64, top: 1180, width: 952, height: 14, background: "#333" }}>
          <div style={{ width: `${ph * 100}%`, height: "100%", background: C.white }} />
          <div style={{ position: "absolute", left: `${ph * 100}%`, top: -22, width: 8, height: 58, background: C.yellow, transform: "translateX(-4px)" }} />
        </div>
        {within(t, 13.0, 13.45) ? (
          <div style={{ position: "absolute", left: 64, top: 1250, ...display(90, C.white) }}>▶▶ 5×</div>
        ) : null}
      </>
    );
  }
  return <Footage frame={f} scale={1.25 * snapIn(t, 13.75)} />;
};

// ============ 07/08 ADS: "Aur ads? … Woh ads hi nahi lagta hai. Kuch aur hi lagta hai." ============
const AdUI: React.FC<{ t: number; gone: boolean }> = ({ t, gone }) => {
  if (gone || t < 14.68) return null;
  const p = clamp(pop(t, 14.68, 0.14));
  return (
    <>
      <div style={{ position: "absolute", left: 64, top: 1408, transform: `scale(${p})`, transformOrigin: "left center" }}>
        <Label rotate={0} pad="10px 18px 12px" style={{ ...text(38, C.ink, 800) }}>Ad · 0:05</Label>
      </div>
      <div style={{ position: "absolute", left: 640, top: 1392, width: 376, height: 92, background: C.black, border: `3px solid ${C.white}`, display: "flex", alignItems: "center", justifyContent: "center", gap: 16, transform: `scale(${p})`, ...text(42, C.white, 700) }}>
        Skip Ad <span style={{ fontSize: 36 }}>▶|</span>
      </div>
    </>
  );
};

const Ads: React.FC<BeatProps> = ({ t, f }) => {
  const frozen = t >= 14.98;
  const sc = frozen ? lerp(1.0, 1.1, easeOut(prog(t, 14.98, 0.4))) : snapIn(t, 14.5);
  return (
    <>
      <Footage frame={f} scale={sc} filter={frozen ? "grayscale(1) contrast(1.25)" : undefined} />
      <AdUI t={t} gone={false} />
    </>
  );
};

const NotAds: React.FC<BeatProps> = ({ t, f }) => {
  const sc = (t < 16.66 ? 1.18 : 1.32) * snapIn(t, t < 16.66 ? 15.3833 : 16.66);
  const cur = easeInOut(prog(t, 15.39, 0.33));
  const skipped = t >= 15.8;
  const strike = easeOut(prog(t, 16.12, 0.16));
  return (
    <>
      <Footage frame={f} scale={sc} />
      {t >= 15.95 ? (
        <div style={{ position: "absolute", left: 720, top: 300, ...display(230, C.white), textShadow: "0 8px 0 rgba(0,0,0,.35)", transform: `rotate(6deg) scale(${lerp(1.3, 1, clamp(pop(t, 15.95, 0.16)))})` }}>
          AD
          <div style={{ position: "absolute", left: -24, top: 92, width: 360 * strike, height: 30, background: C.yellow, transform: "rotate(-14deg)", transformOrigin: "left center" }} />
        </div>
      ) : null}
      {within(t, 15.8, 15.87) ? (
        <div style={{ position: "absolute", left: 40, top: 1392, width: 1000, height: 92, background: C.white, opacity: 0.5, transform: "translateX(30px)" }} />
      ) : null}
      <AdUI t={t} gone={skipped} />
      {t < 16.1 ? <Cursor x={lerp(560, 840, cur)} y={lerp(1700, 1430, cur)} pressed={within(t, 15.72, 15.82)} /> : null}
    </>
  );
};

// ============ 09 DELIVERED: "I delivered over 2,000 videos." (cut-out on a desktop of exports) ============
const FILES = ["FINAL.mp4", "FINAL_v2.mp4", "FINAL_FINAL.mp4", "reel_07.mp4", "ad_cut_3.mp4", "yt_ep12.mp4", "client_v9.mp4", "reel_31.mp4", "promo_4k.mp4", "FINAL_v3.mp4", "teaser.mp4", "ad_15s.mp4", "vlog_22.mp4", "reel_88.mp4", "launch.mp4", "FINAL_ok.mp4", "short_41.mp4", "edit_v12.mp4", "reel_120.mp4", "real_FINAL.mp4"];
const Delivered: React.FC<BeatProps> = ({ t, f }) => {
  const n = Math.round(lerp(0, 2000, easeOut(prog(t, 18.28, 0.6))));
  const plus = t >= 18.86;
  return (
    <>
      <Paper />
      {FILES.map((name, i) => {
        const col = i % 5;
        const row = Math.floor(i / 5);
        const t0 = 17.85 + i * 0.05;
        if (t < t0) return null;
        const p = clamp(pop(t, t0, 0.12));
        return (
          <div key={i} style={{ position: "absolute", left: 40 + col * 205, top: 250 + row * 330, width: 180, display: "flex", flexDirection: "column", alignItems: "center", gap: 8, transform: `scale(${p})` }}>
            <Thumb i={i * 2 + 1} w={150} style={{ border: `3px solid ${C.black}` }} />
            <span style={{ ...text(21, C.black, 700), whiteSpace: "nowrap" }}>{name}</span>
          </div>
        );
      })}
      <Footage frame={f} person scale={1.0 * snapIn(t, 17.8167)} ox={540} oy={1530} ty={BOTTOM_ANCHOR} sticker={9} />
      {t >= 18.28 ? (
        <div style={{ position: "absolute", left: 50, top: 290, transform: `scale(${lerp(1.25, 1, clamp(pop(t, 18.28, 0.16)))})`, transformOrigin: "left center" }}>
          <Label rotate={-3} style={{ ...display(250, C.ink), fontVariantNumeric: "tabular-nums" }}>
            {n.toLocaleString("en-US")}
            {plus ? "+" : ""}
          </Label>
        </div>
      ) : null}
      <PopWord t={t} t0={18.92} style={{ left: 80, top: 560 }}>
        <Label bg={C.black} color={C.white} rotate={-3} pad="10px 22px 14px" style={{ ...text(66, C.white, 800) }}>VIDEOS DELIVERED</Label>
      </PopWord>
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
        <Paper tint={C.yellow} />
        <div style={{ position: "absolute", left: 0, width: W, top: 540, textAlign: "center", ...display(560, C.ink), transform: `scale(${lerp(1.4, 1, clamp(pop(t, 21.8, 0.18)))})` }}>60+</div>
        <PopWord t={t} t0={21.86} style={{ left: 0, width: W, top: 1090, textAlign: "center", ...display(150, C.ink) }}>CLIENTS</PopWord>
      </>
    );
  }
  const sc = (t < 21.8 ? 1.12 : 1.0) * snapIn(t, t < 21.8 ? 20.05 : 22.5);
  const visible = MSGS.filter((m) => t >= m.t0);
  return (
    <>
      <Footage frame={f} scale={sc} />
      {t < 21.8
        ? visible.map((m, i) => {
            const fromTop = visible.length - 1 - i;
            const p = easeOut(prog(t, m.t0, 0.16));
            return (
              <div key={m.msg} style={{ position: "absolute", left: 80, top: 1416 - fromTop * 124 + (1 - p) * 140, width: 920, height: 108, opacity: p, background: C.white, border: `3px solid ${C.black}`, borderRadius: 26, display: "flex", alignItems: "center", gap: 22, padding: "0 26px" }}>
                <span style={{ width: 64, height: 64, borderRadius: 32, background: C.black, color: C.white, display: "flex", alignItems: "center", justifyContent: "center", ...text(30, C.white, 800) }}>{m.who.split("· ")[1][0]}</span>
                <span style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ ...text(24, "#6B6B6B", 700) }}>{m.who} · now</span>
                  <span style={{ ...text(36, C.black, 700) }}>{m.msg}</span>
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
  const zoom = t >= 24.75 ? 1.38 : t >= 24.47 ? 1.24 : t >= 24.09 ? 1.12 : 1.0;
  const jit = ((step * 37) % 7) - 3;
  return (
    <>
      <AbsoluteFill style={{ background: C.black }} />
      <Footage frame={src} scale={zoom} ty={jit} filter="grayscale(1) contrast(1.2)" />
      {[0, 970].map((x) => (
        <div key={x} style={{ position: "absolute", left: x, top: 0, width: 110, height: H, background: C.black }}>
          {Array.from({ length: 15 }).map((_, i) => (
            <span key={i} style={{ position: "absolute", left: 34, top: i * 140 + 40 + jit, width: 42, height: 60, borderRadius: 9, background: C.gray1 }} />
          ))}
        </div>
      ))}
      <div style={{ position: "absolute", left: 0, width: W, top: 250, textAlign: "center", ...display(120, C.white, 800), fontVariantNumeric: "tabular-nums" }}>
        FR. {String(src + 1).padStart(4, "0")}
      </div>
    </>
  );
};

// ============ 12 FOUND: "Found it?" (autofocus reticle) ============
const Found: React.FC<BeatProps> = ({ t, f }) => {
  const sc = 1.45 * snapIn(t, 25.4167);
  const size = lerp(820, 560, easeOut(prog(t, 25.45, 0.18)));
  const blink = within(t, 25.81, 25.86) || within(t, 25.92, 25.97);
  const L = 90;
  const b = `9px solid ${C.yellow}`;
  const x = 540 - size / 2;
  const y = 600 - size / 2;
  return (
    <>
      <Footage frame={f} scale={sc} ox={540} oy={600} />
      {!blink ? (
        <>
          <div style={{ position: "absolute", left: x, top: y, width: L, height: L, borderLeft: b, borderTop: b }} />
          <div style={{ position: "absolute", left: x + size - L, top: y, width: L, height: L, borderRight: b, borderTop: b }} />
          <div style={{ position: "absolute", left: x, top: y + size - L, width: L, height: L, borderLeft: b, borderBottom: b }} />
          <div style={{ position: "absolute", left: x + size - L, top: y + size - L, width: L, height: L, borderRight: b, borderBottom: b }} />
        </>
      ) : null}
    </>
  );
};

// ============ 13 DM: "DM me what it says." (electric blue is this frame's one accent) ============
const DM: React.FC<BeatProps> = ({ t, f }) => {
  const up = easeOut(prog(t, 26.38, 0.22));
  const typing = within(t, 26.93, 27.12);
  const sent = t >= 27.12;
  return (
    <>
      <Footage frame={f} scale={snapIn(t, 26.3833)} />
      <div style={{ position: "absolute", left: 70, top: lerp(1920, 930, up), width: 940, height: 470, background: C.white, borderRadius: 40, border: `3px solid ${C.black}`, overflow: "hidden" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 22, padding: "26px 34px", borderBottom: `3px solid ${C.gray1}` }}>
          <div style={{ width: 84, height: 84, borderRadius: 42, overflow: "hidden", border: `3px solid ${C.black}` }}>
            <Thumb i={20} w={84} style={{ marginTop: -20 }} />
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ ...text(38, C.black, 800) }}>Aminur</span>
            <span style={{ ...text(26, "#6B6B6B", 500) }}>Video Editor · Active now</span>
          </div>
        </div>
        <div style={{ padding: "28px 34px", display: "flex", flexDirection: "column", gap: 20 }}>
          <PopWord t={t} t0={26.45} style={{ position: "relative" }}>
            <div style={{ background: C.gray1, borderRadius: 30, padding: "18px 28px", maxWidth: 640, ...text(38, C.black, 600) }}>Found the frame? DM me what it says.</div>
          </PopWord>
          <div style={{ alignSelf: "flex-end", position: "relative", height: 90 }}>
            {typing ? (
              <div style={{ background: C.blue, borderRadius: 30, padding: "22px 30px", display: "flex", gap: 12 }}>
                {[0, 1, 2].map((i) => (
                  <span key={i} style={{ width: 16, height: 16, borderRadius: 8, background: C.white, opacity: 0.4 + 0.6 * Math.abs(Math.sin((t * 12) + i)) }} />
                ))}
              </div>
            ) : null}
            {sent ? (
              <div style={{ background: C.blue, borderRadius: 30, padding: "18px 28px", display: "flex", gap: 14, transform: `scale(${clamp(pop(t, 27.12, 0.14))})`, transformOrigin: "right center" }}>
                <span style={{ width: 150, height: 40, background: C.white, borderRadius: 6 }} />
                <span style={{ width: 120, height: 40, background: C.white, borderRadius: 6 }} />
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </>
  );
};

// ============ 14 NAHI MILA: "Nahi mila na?" (error pop-up as the caption) ============
const NahiMila: React.FC<BeatProps> = ({ t, f }) => {
  const p = clamp(pop(t, 27.82, 0.16));
  const shake = within(t, 28.34, 28.6) ? Math.sin((t - 28.34) * 70) * 18 * (1 - prog(t, 28.34, 0.26)) : 0;
  return (
    <>
      <Footage frame={f} scale={1.18 * snapIn(t, 27.8167)} />
      <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, transform: `translateX(${shake}px)` }}>
        <Window x={110} y={960} w={860} h={500} title="Frame Finder" style={{ transform: `scale(${lerp(0.6, 1, p)})`, opacity: p }}>
          <div style={{ display: "flex", gap: 34, padding: "40px 44px 0" }}>
            <div style={{ width: 110, height: 110, borderRadius: 55, background: C.black, color: C.white, display: "flex", alignItems: "center", justifyContent: "center", ...display(84, C.white) }}>!</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <span style={{ ...text(56, C.black, 800) }}>Frame not found.</span>
              <span style={{ ...text(40, "#555", 600) }}>Nahi mila na?</span>
            </div>
          </div>
          <div style={{ display: "flex", gap: 20, padding: "44px 44px 0", justifyContent: "flex-end" }}>
            <span style={{ padding: "16px 34px", border: `3px solid ${C.black}`, borderRadius: 14, ...text(34, C.black, 800) }}>Give up</span>
            <span style={{ padding: "16px 34px", background: C.black, borderRadius: 14, ...text(34, C.white, 800) }}>Watch again</span>
          </div>
        </Window>
      </div>
    </>
  );
};

// ============ 15 EDITOR: "Tabhi toh editor main hoon." (repeated type behind a B/W cut-out) ============
const Editor: React.FC<BeatProps> = ({ t, f }) => {
  const hit = t >= 29.46;
  const drift = (t - 28.92) * 90;
  return (
    <>
      <AbsoluteFill style={{ background: C.black }} />
      {[0, 1, 2, 3, 4, 5].map((r) => {
        const solid = hit && r % 2 === 1;
        const dir = r % 2 === 0 ? -1 : 1;
        if (solid) {
          return (
            <div key={r} style={{ position: "absolute", left: dir * 40 * prog(t, 29.46, 1.2), width: W, top: 230 + r * 245, textAlign: "center", ...display(280, C.yellow), transform: r === 3 ? `scale(${lerp(1.15, 1, easeOut(prog(t, 29.46, 0.2)))})` : undefined }}>
              EDITOR
            </div>
          );
        }
        return (
          <div key={r} style={{ position: "absolute", left: -300 + dir * drift - (r % 2) * 180, top: 230 + r * 245, ...display(280, "transparent"), WebkitTextStroke: `4px ${C.yellow}` }}>
            EDITOR EDITOR EDITOR
          </div>
        );
      })}
      <Footage frame={f} person scale={1.1 * snapIn(t, 28.9167)} ox={540} oy={1530} ty={BOTTOM_ANCHOR} sticker={9} filter="grayscale(1) contrast(1.15)" />
    </>
  );
};

// ============ 16 TWICE: "I make videos that people watch twice." (rewind back to frame one) ============
const Twice: React.FC<BeatProps> = ({ t, f }) => {
  if (within(t, 32.7, 33.25)) {
    const k = easeIn(prog(t, 32.7, 0.55));
    const src = Math.round(lerp(981, 0, k) / 2) * 2;
    const lines = [0, 1, 2].map((i) => ((f * 131 + i * 577) % 1500) + 230);
    return (
      <>
        <Footage frame={src} filter="contrast(1.2) saturate(0.6)" />
        {lines.map((y, i) => (
          <div key={i} style={{ position: "absolute", left: 0, top: y, width: W, height: 6 + i * 5, background: "rgba(255,255,255,0.55)" }} />
        ))}
        <div style={{ position: "absolute", left: 64, top: 320, ...text(52, C.white, 800), letterSpacing: "0.06em", textShadow: "0 4px 0 rgba(0,0,0,.4)" }}>◀◀ REWIND</div>
        {t >= 32.81 ? (
          <div style={{ position: "absolute", left: 0, width: W, top: 600, textAlign: "center", ...display(420, C.ink), transform: `scale(${lerp(1.4, 1, clamp(pop(t, 32.81, 0.16)))})` }}>
            <Label rotate={-4}>2×</Label>
          </div>
        ) : null}
      </>
    );
  }
  if (t >= 32.7) return <Footage frame={f} scale={snapIn(t, 33.25)} />;
  // a new beat on "videos", "that" and "people"
  const step = t >= 32.09 ? 3 : t >= 31.53 ? 2 : t >= 31.02 ? 1 : 0;
  const base = [1.0, 1.2, 1.0, 1.32][step];
  const at = [30.65, 31.02, 31.53, 32.09][step];
  const play = within(t, 31.02, 31.53) ? clamp(pop(t, 31.02, 0.16)) : 0;
  return (
    <>
      <Footage frame={f} scale={base * snapIn(t, at)} filter={step === 3 ? "grayscale(1) contrast(1.15)" : undefined} />
      {play > 0 ? (
        <div style={{ position: "absolute", left: 90, top: 330, width: 230, height: 230, borderRadius: 115, background: C.white, transform: `scale(${play}) rotate(-6deg)`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `8px 8px 0 ${C.black}` }}>
          <svg width="96" height="110" viewBox="0 0 96 110"><path d="M10 6 L90 55 L10 104 Z" fill={C.black} /></svg>
        </div>
      ) : null}
      {step === 3 ? (
        <div style={{ position: "absolute", left: 64, top: 300, ...text(44, C.white, 800), letterSpacing: "0.08em", textShadow: "0 4px 0 rgba(0,0,0,.4)", opacity: prog(t, 32.09, 0.06) }}>
          WATCH TIME ▲ 2×
        </div>
      ) : null}
    </>
  );
};

// ============ 17/18 SERVICE + BIO: editorial cards + cut-out sticker ============
const SERVICES = [
  { n: "01", s: "Reels & Shorts", t0: 33.78 },
  { n: "02", s: "YouTube long-form", t0: 34.08 },
  { n: "03", s: "Ads people don't skip", t0: 34.46 },
];
const Service: React.FC<BeatProps> = ({ t, f }) => {
  const slide = easeOut(prog(t, 33.62, 0.22));
  const bio = t >= 35.8833;
  const hl = easeOut(prog(t, 36.76, 0.18));
  return (
    <>
      <Paper />
      {!bio ? (
        <>
          <PopWord t={t} t0={33.62} style={{ left: 64, top: 296, ...display(150, C.ink) }}>
            NEED AN
            <br />
            <Label rotate={-2}>EDITOR?</Label>
          </PopWord>
          {SERVICES.map((s, i) => (
            <PopWord key={s.n} t={t} t0={s.t0} style={{ left: 64, top: 640 + i * 160 }}>
              <div style={{ width: 660, height: 136, background: C.white, border: `3px solid ${C.black}`, boxShadow: `10px 10px 0 ${C.black}`, display: "flex", alignItems: "center", gap: 30, padding: "0 30px" }}>
                <span style={{ ...display(96, C.ink) }}>{s.n}</span>
                <span style={{ ...text(44, C.black, 800) }}>{s.s}</span>
              </div>
            </PopWord>
          ))}
        </>
      ) : (
        <>
          <div style={{ position: "absolute", left: 64, top: lerp(1900, 290, easeOut(prog(t, 35.88, 0.22))), width: 952, height: 560, background: C.white, border: `3px solid ${C.black}`, borderRadius: 30, boxShadow: `12px 12px 0 ${C.black}`, padding: 40, display: "flex", flexDirection: "column", gap: 22 }}>
            <div style={{ display: "flex", gap: 30, alignItems: "center" }}>
              <div style={{ width: 150, height: 150, borderRadius: 75, overflow: "hidden", border: `4px solid ${C.black}` }}>
                <Thumb i={20} w={150} style={{ marginTop: -36 }} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span style={{ ...text(60, C.black, 800) }}>Aminur</span>
                <span style={{ ...text(34, "#555", 600) }}>Video Editor</span>
                <span style={{ ...text(30, C.black, 700) }}>2,000+ videos · 60+ clients</span>
              </div>
            </div>
            <div style={{ position: "relative", alignSelf: "flex-start", ...text(44, C.black, 800), padding: "6px 14px" }}>
              <span style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${hl * 100}%`, background: C.yellow, zIndex: 0 }} />
              <span style={{ position: "relative" }}>Contact number → in bio</span>
            </div>
            <div style={{ display: "flex", gap: 18 }}>
              <span style={{ flex: 1, textAlign: "center", padding: "18px 0", background: C.black, borderRadius: 16, ...text(36, C.white, 800) }}>Message</span>
              <span style={{ flex: 1, textAlign: "center", padding: "18px 0", border: `3px solid ${C.black}`, borderRadius: 16, ...text(36, C.black, 800) }}>Follow</span>
            </div>
          </div>
          <PopWord t={t} t0={36.15} style={{ left: 64, top: 900, display: "flex", alignItems: "center", gap: 24 }}>
            <span style={{ ...display(170, C.ink) }}>↑</span>
            <span style={{ ...text(46, C.black, 800), lineHeight: 1.05 }}>
              TAP MY
              <br />
              PROFILE
            </span>
          </PopWord>
        </>
      )}
      <Footage frame={f} person scale={0.7} ox={540} oy={1530} tx={lerp(760, 270, slide)} ty={BOTTOM_ANCHOR} sticker={9} />
    </>
  );
};

// ============ END CARD: "Shuruaat… isi video se." ============
const EndCard: React.FC<BeatProps> = ({ t }) => (
  <>
    <AbsoluteFill style={{ background: C.black }} />
    <PopWord t={t} t0={37.38} style={{ left: 64, top: 620, ...display(170, C.white) }}>
      Shuruaat…
    </PopWord>
    <PopWord t={t} t0={37.78} from={0.4} style={{ left: 50, top: 820, ...display(170, C.ink) }}>
      <Label rotate={-3}>isi video se.</Label>
    </PopWord>
    <div style={{ position: "absolute", left: 64, top: 1360, ...text(32, C.gray2, 700), letterSpacing: "0.32em", opacity: prog(t, 37.6, 0.25) }}>
      AMINUR · VIDEO EDITOR
    </div>
    <div style={{ position: "absolute", left: 64, top: 1420, ...text(28, C.gray2, 600), letterSpacing: "0.12em", opacity: prog(t, 38.1, 0.25) }}>
      ↺ watch again · find the frame
    </div>
  </>
);

// ============ THE HIDDEN FRAME (exactly one frame long) ============
const Hidden: React.FC<{ f: number }> = ({ f }) => (
  <>
    <Paper tint={C.yellow} />
    <div style={{ position: "absolute", left: 64, top: 300, ...text(64, C.ink, 800) }}>YOU FOUND IT.</div>
    <div style={{ position: "absolute", left: 50, top: 520, ...display(285, C.ink) }}>
      {SECRET.split(" ").map((w) => (
        <div key={w}>{w}</div>
      ))}
    </div>
    <div style={{ position: "absolute", left: 64, top: 1180, ...text(58, C.ink, 800) }}>DM me these 2 words.</div>
    <div style={{ position: "absolute", left: 64, top: 1270, ...text(36, C.ink, 600) }}>Frame {String(f + 1).padStart(4, "0")} of {TOTAL_FRAMES}</div>
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
      return within(t, 21.8, 22.5) ? { hide: true } : { y: t < 21.8 ? 1000 : 1190 };
    case "twice":
      return { hide: within(t, 32.7, 33.25) };
    case "service":
    case "bio":
      return { y: 1170, boxed: true, left: true, width: 560 };
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

// Big hits: the whole frame shakes and flashes for a beat, in sync with the impact sounds.
const IMPACTS = [0.68, 3.22, 8.78, 9.33, 10.06, 18.86, 21.8, 29.46, 32.81, 37.8];
const impactAt = (t: number) => {
  const hit = IMPACTS.find((h) => t >= h && t < h + 0.2);
  if (hit === undefined) return { x: 0, y: 0, flash: 0 };
  const k = 1 - (t - hit) / 0.2;
  const n = Math.round((t - hit) * FPS);
  return { x: (rnd(hit * 100 + n) - 0.5) * 30 * k, y: (rnd(hit * 77 + n * 3) - 0.5) * 30 * k, flash: 0.32 * Math.max(0, 1 - (t - hit) / 0.1) };
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
  if (f >= SELECTS_FRAMES) {
    return (
      <AbsoluteFill style={{ background: C.black, overflow: "hidden" }}>
        <AbsoluteFill style={{ transform: `translate(${impactAt(t).x}px, ${impactAt(t).y}px)` }}>
          <EndCard t={t} f={f} />
        </AbsoluteFill>
        <FrameCounter frame={f} />
      </AbsoluteFill>
    );
  }
  const clip = clipAt(t);
  const Beat = BEATS[clip.id];
  const rewinding = clip.id === "twice" && within(t, 32.7, 33.25);
  const counterFrame = rewinding ? Math.round(lerp(981, 0, easeIn(prog(t, 32.7, 0.55)))) : f;
  const hit = impactAt(t);
  return (
    <AbsoluteFill style={{ background: C.black, overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `translate(${hit.x}px, ${hit.y}px) scale(${hit.x || hit.y ? 1.03 : 1})` }}>
        <Beat t={t} f={f} />
      </AbsoluteFill>
      {hit.flash > 0 ? <AbsoluteFill style={{ background: C.white, opacity: hit.flash }} /> : null}
      <Captions t={t} opts={captionOpts(clip.id, t)} />
      {clip.id !== "everyframe" ? <FrameCounter frame={counterFrame} scramble={clip.id === "hook"} /> : null}
    </AbsoluteFill>
  );
};

