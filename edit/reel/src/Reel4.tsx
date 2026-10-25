import React from "react";
import { AbsoluteFill, Audio, Sequence, OffthreadVideo, staticFile, interpolate, useCurrentFrame, Easing } from "remotion";
import { S, E, W, fr, FPS, DURATION, SCN, inter, serif } from "./lib";
import { Talking, PUNCHES, SHIFTS, GRAY, ENTERS, CFG } from "./Base";
import { Captions4 } from "./Captions4";
import * as X from "./Scenes";
import META from "./sfx-meta.json";

/* ---- look: researched low-key pro style ---- */
CFG.src = "base_lowkey.mp4";
CFG.zooms = [1.3, 1.48];
SCN.minimal = true;

const t200 = W("hook_a", "$200");
const burnT = W("pain_4", "burnout") - 0.05;
const sirfT = W("price", "sirf") - 0.05;
const revealT = W("kicker", "humne") - 0.15;
const at = (id: string, w: string, n = 0) => W(id, w, n) - 0.04; // cut a hair before the word

PUNCHES.splice(0, PUNCHES.length);
SHIFTS.splice(0, SHIFTS.length);
ENTERS.splice(0, ENTERS.length);
GRAY.splice(0, GRAY.length, [S("pain_1"), S("offer_1")]);

const Seq: React.FC<{ a: number; b: number; children: React.ReactNode; name?: string }> = ({ a, b, children, name }) => (
  <Sequence from={fr(a)} durationInFrames={Math.max(1, fr(b) - fr(a))} name={name} layout="absolute-fill">{children}</Sequence>
);
const rel = (id: string, w: string, n = 0) => fr(W(id, w, n) - S(id));

/** B-roll shot: hard cut in, slow push for life */
const Shot: React.FC<{ src: string; from?: number; push?: number; rec?: boolean }> = ({ src, from = 0, push = 0.06, rec }) => {
  const f = useCurrentFrame();
  const z = 1.02 + push * Math.min(1, f / 75);
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <OffthreadVideo src={staticFile(`broll4/${src}.mp4`)} muted startFrom={from} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z})` }} />
      {rec && <RecDot />}
    </AbsoluteFill>
  );
};
const RecDot: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <div style={{ position: "absolute", left: 70, top: 180, display: "flex", alignItems: "center", gap: 14, fontFamily: "Montserrat", fontWeight: 700, fontSize: 32, color: "#fff", letterSpacing: "0.08em" }}>
      <div style={{ width: 20, height: 20, borderRadius: 10, background: "#ff3b30", opacity: Math.floor(f / 10) % 2 ? 1 : 0.3 }} /> REC
    </div>
  );
};

/** offer_1: refined title over the speaker */
const BrandTitle: React.FC<{ nameF: number; pkgF: number }> = ({ nameF, pkgF }) => {
  const f = useCurrentFrame();
  const a = interpolate(f, [nameF - 2, nameF + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const b = interpolate(f, [pkgF - 2, pkgF + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const line = interpolate(f, [pkgF, pkgF + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.65, 0, 0.35, 1) });
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 1110, textAlign: "center" }}>
      <div style={{ fontFamily: "Montserrat", fontWeight: 700, fontSize: 34, letterSpacing: "0.42em", color: "rgba(255,255,255,0.9)", opacity: a, filter: `blur(${(1 - a) * 8}px)`, paddingLeft: "0.42em" }}>AMINUR REX TEAM</div>
      <div style={{ width: 360 * line, height: 2, background: "rgba(246,195,68,0.85)", margin: "22px auto 18px" }} />
      <div style={{ fontFamily: serif, fontStyle: "italic", fontSize: 104, lineHeight: 1, color: "#fff", opacity: b, filter: `blur(${(1 - b) * 10}px)`, transform: `translateY(${(1 - b) * 16}px)`, textShadow: "0 6px 30px rgba(0,0,0,0.6)" }}>Monthly Editing Package</div>
    </div>
  );
};

/** price: $200 over falling cash */
const PriceCard: React.FC = () => {
  const f = useCurrentFrame();
  const a = interpolate(f, [0, 10], [0, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const b = interpolate(f, [8, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  return (
    <AbsoluteFill>
      <Shot src="cash" push={0.05} />
      <AbsoluteFill style={{ background: "radial-gradient(70% 45% at 50% 50%, rgba(0,0,0,0.15), rgba(0,0,0,0.55))" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: 760, textAlign: "center" }}>
        <div style={{ fontFamily: "Montserrat", fontWeight: 800, fontSize: 250, letterSpacing: "-0.04em", color: "#fff", opacity: a, transform: `scale(${1.06 - 0.06 * a})`, filter: `blur(${(1 - a) * 10}px)`, textShadow: "0 0 60px rgba(246,195,68,0.35), 0 10px 40px rgba(0,0,0,0.6)" }}>$200</div>
        <div style={{ marginTop: 10, fontFamily: "Montserrat", fontWeight: 700, fontSize: 36, letterSpacing: "0.4em", paddingLeft: "0.4em", color: "#F6C344", opacity: b }}>PER MONTH</div>
      </div>
    </AbsoluteFill>
  );
};

/** two-frame white flash for the colour return */
const Flash: React.FC = () => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{ background: "#fff", opacity: interpolate(f, [0, 2, 5], [0.85, 0.5, 0], { extrapolateRight: "clamp" }) }} />;
};

const Finish: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill style={{ background: "radial-gradient(115% 80% at 50% 42%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.5) 100%)" }} />
    <X.Grain opacity={0.09} />
  </AbsoluteFill>
);

/* ---- B-roll edit decision list: [shot, from(s), to(s), options] ---- */
const BROLL: [string, number, number, { rec?: boolean; push?: number }?][] = [
  ["cashtop", t200 - 0.04, W("hook_b", "aur") - 0.04],
  ["tripod", S("pain_1") - 0.02, S("pain_2") - 0.02],
  ["editclose", S("pain_2") - 0.02, at("pain_2", "poori")],
  ["clock", at("pain_2", "poori"), S("pain_3") - 0.02],
  ["analytics", S("pain_4") - 0.02, burnT],
  ["rubface", burnT, S("offer_1") - 0.02],
  ["yttripod", S("offer_2") - 0.02, S("offer_3") - 0.02, { rec: true }],
  ["editoroff", S("offer_3") - 0.02, at("offer_3", "humara")],
  ["lumetri", at("offer_3", "humara"), S("style_q") - 0.02],
  ["scroll", S("scroll") - 0.02, at("scroll", "scroll")],
  ["pay", S("reel") - 0.02, at("reel", "jhanjhat")],
  ["ytstudio", S("proof_b") - 0.02, at("proof_b", "humare")],
  ["camgirl", at("proof_b", "humare"), at("proof_b", "package")],
  ["vlogout", at("proof_b", "package"), S("slots") - 0.02],
  ["hourglass", S("slots") - 0.02, S("fcfs") - 0.02],
];

/* ---- captions off where a graphic carries the words ---- */
const HIDE: [number, number][] = [
  [S("offer_1"), S("offer_2")], [at("scroll", "scroll"), S("reel")], [sirfT, S("proof_b")], [S("cta_1"), S("cta_2")], [S("cta_3"), S("kicker")], [revealT, 999],
];

/* ---- sound: cinematic bed + subtle, purposeful SFX ---- */
type Fx = [string, number, number?, number?, number?];
const FX: Fx[] = [
  ["impact_deep", 0.0, 0.28, 1.6],
  ["whoosh_air", t200 - 0.12, 0.18, 0.6], ["coins_clink", t200 + 0.05, 0.16],
  ["bass_short", S("pain_1") - 0.02, 0.26, 0.6], ["shutter", S("pain_1") + 0.6, 0.2],
  ["key_single", S("pain_2") + 0.15, 0.22], ["key_single", S("pain_2") + 0.35, 0.18], ["key_single", S("pain_2") + 0.5, 0.2],
  ["tick_timer", at("pain_2", "poori"), 0.2, 1.4],
  ["swoosh_short", S("pain_3") - 0.06, 0.12],
  ["click_tech", S("pain_4") + 0.1, 0.15], ["bass_short", burnT, 0.3, 0.6],
  ["swoosh_short", S("offer_1") - 0.08, 0.16], ["impact_logo", S("offer_1"), 0.3], ["reveal", W("offer_1", "monthly") - 0.05, 0.18],
  ["shutter", S("offer_2") + 0.2, 0.22], ["whoosh_air", S("offer_3") - 0.08, 0.14, 0.6], ["typing_fast", S("offer_3") + 0.1, 0.12, 1.2],
  ["whoosh_air", S("st_talking") - 0.08, 0.16, 0.6], ["shutter", S("st_talking") + 0.08, 0.2],
  ["swoosh_short", S("st_podcast") - 0.06, 0.16], ["swoosh_short", S("st_doc") - 0.06, 0.16], ["key_single", S("st_doc") + 0.35, 0.2], ["key_single", S("st_doc") + 0.5, 0.2],
  ["swoosh_short", S("st_cine") - 0.06, 0.16], ["whoosh_air", S("st_motion") - 0.08, 0.16, 0.6], ["swoosh_short", S("st_faceless") - 0.06, 0.16], ["typing_fast", S("st_faceless"), 0.12, 1.0],
  ["swoosh_short", S("content") - 0.06, 0.12],
  ["sweep_air", at("scroll", "scroll") + 0.05, 0.22, 1.4], ["impact_big", W("scroll", "stop"), 0.3],
  ["click_select", at("reel", "pay"), 0.2],
  ["riser", sirfT - 1.2, 0.18, 1.2, 5.38 - 1.2], ["impact_deep", sirfT, 0.3, 1.4], ["coins_clink", sirfT + 0.35, 0.16],
  ["whoosh_air", S("proof_b") - 0.08, 0.14, 0.6], ["swoosh_short", at("proof_b", "humare") - 0.05, 0.12], ["swoosh_short", at("proof_b", "package") - 0.05, 0.12],
  ["tick_timer", S("slots"), 0.14, 2.8], ["bass_short", W("slots", "20"), 0.22, 0.5],
  ["swoosh_short", S("cta_1") - 0.05, 0.16], ...[0, 1, 2, 3].map((i) => ["key_single", W("cta_1", "edit") + i * 0.085, 0.3] as Fx), ["pop_hard", W("cta_1", "edit") + 0.42, 0.18],
  ["notif_positive", S("cta_2") + 0.08, 0.28], ["swoosh_short", S("cta_3") - 0.06, 0.14], ["click_tone", W("cta_3", "contact"), 0.25],
  ["whoosh_cine", revealT - 0.05, 0.28], ["impact_deep", E("kicker") - 0.4, 0.22, 1.2],
];

const MUSIC_START = 3.0; // skip the intro swell
const Sound: React.FC = () => (
  <>
    <Audio src={staticFile("music_cine.mp3")} startFrom={fr(MUSIC_START)}
      volume={(f) => interpolate(f, [0, 6, fr(S("st_talking")), fr(S("st_talking")) + 6, fr(S("content")), fr(S("content")) + 6, DURATION - 24, DURATION], [0, 0.13, 0.13, 0.2, 0.2, 0.13, 0.13, 0], { extrapolateRight: "clamp" })} />
    {FX.map(([n, t, v = 0.3, max, off = 0], i) => {
      const d = Math.min(max ?? 99, ((META as Record<string, number>)[n] ?? 1) - off);
      return (
        <Sequence key={i} from={Math.max(0, fr(t))} durationInFrames={Math.max(2, fr(d))} name={`sfx ${n}`}>
          <Audio src={staticFile(`sfx/${n}.mp3`)} volume={v} startFrom={fr(off)} />
        </Sequence>
      );
    })}
  </>
);

export const Reel4: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Talking />

    {BROLL.map(([src, a, b, o], i) => (
      <Seq key={i} a={a} b={b} name={`broll ${src}`}><Shot src={src} rec={o?.rec} push={o?.push} /></Seq>
    ))}

    <Seq a={S("offer_1") - 0.02} b={S("offer_1") + 0.2} name="flash"><Flash /></Seq>
    <Seq a={S("offer_1")} b={S("offer_2")} name="brand title"><BrandTitle nameF={rel("offer_1", "aminur")} pkgF={rel("offer_1", "monthly")} /></Seq>

    {/* style montage: hard cuts, no labels (his voice + captions name each style) */}
    <Seq a={S("st_talking")} b={S("st_podcast")} name="01 talking head"><X.DemoTalking offset={fr(S("st_talking"))} /></Seq>
    <Seq a={S("st_podcast")} b={S("st_doc")} name="02 podcast"><X.DemoPodcast /></Seq>
    <Seq a={S("st_doc")} b={S("st_cine")} name="03 documentary"><X.DemoDoc /></Seq>
    <Seq a={S("st_cine")} b={S("st_motion")} name="04 cinematic"><X.DemoCine /></Seq>
    <Seq a={S("st_motion")} b={S("st_faceless")} name="05 motion"><X.DemoMotion /></Seq>
    <Seq a={S("st_faceless")} b={S("content")} name="06 faceless"><X.DemoFaceless /></Seq>

    <Seq a={at("scroll", "scroll")} b={S("reel")} name="scroll stop"><X.ScrollStop stopF={fr(W("scroll", "stop") - at("scroll", "scroll"))} /></Seq>
    <Seq a={sirfT} b={S("proof_b") - 0.02} name="$200"><PriceCard /></Seq>

    <Seq a={S("cta_1")} b={S("cta_2")} name="comment"><X.CommentSheet typeF={rel("cta_1", "edit")} /></Seq>
    <Seq a={S("cta_2")} b={S("cta_3")} name="dm"><X.DMBanner /></Seq>
    <Seq a={S("cta_3")} b={S("kicker")} name="bio"><X.BioCard tapF={rel("cta_3", "contact")} offset={fr(S("cta_3"))} /></Seq>

    <Finish />
    <Captions4 hide={HIDE} />
    <Seq a={revealT} b={E("kicker") + 1} name="editor reveal"><X.EditorReveal offset={fr(revealT)} captionsHide={[[0, 0]]} /></Seq>
    <Sound />
  </AbsoluteFill>
);
