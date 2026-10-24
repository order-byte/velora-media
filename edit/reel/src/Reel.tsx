import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, interpolate } from "remotion";
import { C, S, E, W, fr, FPS, DURATION, ICam, IStopwatch } from "./lib";
import { Talking, Captions, PUNCHES } from "./Base";
import * as X from "./Scenes";
import META from "./sfx-meta.json";

export const MUSIC = true;

const t200 = W("hook_a", "$200");
const burnT = W("pain_4", "burnout") - 0.08;
const sirfT = W("price", "sirf") - 0.06;
const revealT = W("kicker", "humne") - 0.15;

PUNCHES.splice(0, PUNCHES.length, W("hook_b", "editing"), W("pain_3", "nahi"), W("style_q", "style"), W("fcfs", "first"), W("fcfs", "first", 1), W("kicker", "haan"));

const Seq: React.FC<{ a: number; b: number; children: React.ReactNode; name?: string }> = ({ a, b, children, name }) => (
  <Sequence from={fr(a)} durationInFrames={Math.max(1, fr(b) - fr(a))} name={name} layout="absolute-fill">{children}</Sequence>
);
const rel = (id: string, w: string, n = 0) => fr(W(id, w, n) - S(id));

/* ---------------- sound design ---------------- */
type Fx = [string, number, number?, number?]; // name, time(s), volume, max seconds
const FX: Fx[] = [
  ["glitch_text", 0.0, 0.35], ["impact_logo", 0.02, 0.55],
  ["whoosh_cine", t200 - 0.12, 0.55], ["impact_zoom", t200, 0.6, 1.2], ["coin_win", t200 + 0.25, 0.35],
  ["pop_hard", W("hook_b", "editing"), 0.4],
  ["whoosh_air", S("pain_1") - 0.1, 0.5], ["shutter", S("pain_1") + 0.15, 0.45], ["tick_counter", S("pain_1") + 0.3, 0.3],
  ["sweep_fast", S("pain_2") - 0.08, 0.5], ["tick_timer", W("pain_2", "raat") - 0.1, 0.22, 1.6],
  ["swoosh_short", S("pain_3") - 0.05, 0.45], ...[0, 1, 2, 3, 4, 5, 6].map((i) => ["pop_light", S("pain_3") + (4 + i * 3) / FPS, 0.3] as Fx),
  ["click_tech", S("pain_4") + 0.05, 0.4], ["glitch_break", burnT, 0.5], ["bass_short", burnT, 0.55, 0.9],
  ["whoosh_cine", S("offer_1") - 0.12, 0.55], ["impact_logo", S("offer_1") + 0.1, 0.5], ["reveal", W("offer_1", "aminur") - 0.05, 0.35], ["click_check", W("offer_1", "monthly") + 0.35, 0.4],
  ["shutter_digital", S("offer_2"), 0.45], ["sweep_fast2", S("offer_3") - 0.08, 0.45],
  ...[0, 1, 2, 3, 4].map((i) => ["click_select", S("offer_3") + (6 + i * 5) / FPS, 0.35] as Fx),
  ["pop_long", S("style_q") + 0.1, 0.45], ["tech_slide", S("style_trend") - 0.05, 0.3, 1.2],
  ["whoosh_fast2", S("st_talking") - 0.08, 0.45, 0.8], ["impact_logo", S("st_talking"), 0.45], ["shutter", S("st_talking") + 0.1, 0.35],
  ["sweep_fast", S("st_podcast") - 0.08, 0.5], ["bass_future", S("st_podcast"), 0.35, 0.5],
  ["whoosh_air", S("st_doc") - 0.08, 0.5], ["key_single", S("st_doc") + 0.3, 0.4], ["key_single", S("st_doc") + 0.45, 0.4], ["key_single", S("st_doc") + 0.6, 0.4],
  ["sweep_fast2", S("st_cine") - 0.08, 0.5], ["whoosh_cine", S("st_motion") - 0.1, 0.5], ["glitch_quick", S("st_motion") + 0.05, 0.3],
  ["swoosh_short", S("st_faceless") - 0.05, 0.5], ["typing_fast", S("st_faceless"), 0.25, 1.2],
  ["whoosh_air", S("content") - 0.1, 0.45], ...[0, 1, 2, 3, 4, 5].map((i) => ["pop_light", S("content") + (i * 2) / FPS, 0.28] as Fx),
  ["sweep_air", S("scroll") + 0.1, 0.45, 1.6], ["impact_big", W("scroll", "stop"), 0.6], ["shutter", W("scroll", "stop") + 0.05, 0.35],
  ...[0, 1, 2, 3].map((i) => ["pop_dry", [W("reel", "har"), W("reel", "reel"), W("reel", "alag"), W("reel", "pay")][i], 0.35] as Fx),
  ["impact_logo", W("reel", "khatam"), 0.55], ["glitch_text", W("reel", "khatam"), 0.35], ["whoosh_fast2", W("reel", "khatam") + 0.15, 0.4, 0.8],
  ["whoosh_cine", sirfT - 0.1, 0.5], ["slot_payout", sirfT + 0.2, 0.45], ["coins_clink", sirfT + 0.45, 0.4],
  ["whoosh_air", S("proof_b") - 0.08, 0.45], ["tick_counter", S("proof_b") + 0.2, 0.35], ["tick_counter", S("proof_b") + 0.9, 0.35], ["notif_correct", W("proof_b", "creators"), 0.35],
  ["sweep_fast", S("slots") - 0.08, 0.45], ["tick_timer", S("slots") + 0.2, 0.2, 2.6], ["impact_zoom", W("slots", "20"), 0.4, 0.8],
  ["swoosh_short", S("fcfs"), 0.45], ["click_tone", W("fcfs", "first", 1), 0.35],
  ["whoosh_air", S("cta_1") - 0.05, 0.45], ...[0, 1, 2, 3].map((i) => ["key_single", W("cta_1", "edit") + i * 0.085, 0.45] as Fx), ["pop_hard", W("cta_1", "edit") + 0.42, 0.4],
  ["notif_positive", S("cta_2") + 0.08, 0.5],
  ["sweep_fast2", S("cta_3") - 0.08, 0.4], ["click_tone", W("cta_3", "contact"), 0.45],
  ["whoosh_cine", revealT - 0.05, 0.5], ["reveal", revealT + 0.3, 0.35], ["impact_logo", E("kicker") - 0.35, 0.4],
];

export const Sound: React.FC = () => (
  <>
    {MUSIC && (
      <Audio src={staticFile("music.mp3")} volume={(f) => interpolate(f, [0, 8, DURATION - 20, DURATION], [0, 0.085, 0.085, 0], { extrapolateRight: "clamp" })} />
    )}
    {FX.map(([n, t, v = 0.5, max], i) => {
      const d = Math.min(max ?? 99, (META as Record<string, number>)[n] ?? 1);
      return (
        <Sequence key={i} from={Math.max(0, fr(t))} durationInFrames={Math.max(2, fr(d))} name={`sfx ${n}`}>
          <Audio src={staticFile(`sfx/${n}.mp3`)} volume={v} />
        </Sequence>
      );
    })}
  </>
);

/* ---------------- captions placement ---------------- */
const HIDE: [number, number][] = [
  [0, t200 + 0.95], [burnT, S("offer_1")], [S("offer_1"), S("offer_2")], [S("st_talking"), S("content")],
  [S("scroll"), S("reel")], [sirfT, S("proof_b")], [S("cta_1"), S("cta_2")], [revealT, 999],
];
const DARK: [number, number][] = [[S("pain_1"), S("pain_2")], [S("content"), S("scroll")], [S("reel"), S("price")]];
const YS = [
  { from: S("pain_1"), to: S("pain_2"), y: 1470 }, { from: S("content"), to: S("scroll"), y: 1330 }, { from: S("reel"), to: S("price"), y: 1290 },
  { from: S("proof_b"), to: S("slots"), y: 1380 }, { from: S("slots"), to: S("fcfs"), y: 1470 }, { from: S("cta_3"), to: S("kicker"), y: 1100 },
];

export const Reel: React.FC = () => {
  const hookWords = [
    { w: "SIRF", f: fr(W("hook_a", "sirf")) }, { w: "20", f: fr(W("hook_a", "20")), c: C.green }, { w: "CREATORS", f: fr(W("hook_a", "creators")), c: C.purple },
  ];
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Talking />

      {/* 1 · HOOK */}
      <Seq a={0} b={t200 + 0.4} name="Hook split"><X.HookSplit cut={fr(t200)} words={hookWords} /></Seq>
      <Seq a={t200} b={t200 + 1.1} name="$200 hit"><X.Price200Hit /></Seq>
      <Seq a={t200} b={t200 + 0.2}><X.Flash dur={5} /></Seq>

      {/* 2 · PAIN */}
      <Seq a={S("pain_1")} b={S("pain_2")} name="Pain: shoot"><X.PainShoot /></Seq>
      <Seq a={S("pain_2")} b={S("pain_3")} name="Pain: edit all night"><X.PainEdit raatF={rel("pain_2", "raat")} /></Seq>
      <Seq a={S("pain_3")} b={S("pain_4")} name="Pain: posting"><X.PainPost /></Seq>
      <Seq a={S("pain_4")} b={burnT} name="Pain: growth"><X.PainGrowth burnF={fr(burnT - S("pain_4"))} /></Seq>
      <Seq a={burnT} b={S("offer_1")} name="Burnout"><X.Burnout /></Seq>

      {/* 3 · OFFER */}
      <Seq a={S("offer_1")} b={S("offer_2")} name="Offer brand"><X.OfferBrand nameF={rel("offer_1", "aminur")} pkgF={rel("offer_1", "monthly")} offset={fr(S("offer_1"))} /></Seq>
      <Seq a={S("offer_1")} b={S("offer_1") + 0.2}><X.Flash dur={5} /></Seq>
      <Seq a={S("offer_2")} b={S("offer_3")} name="You shoot"><X.BigLine text="YOU SHOOT." icon={<ICam size={110} color={C.purple} stroke={2.6} />} y={150} size={120} /></Seq>
      <Seq a={S("offer_3")} b={S("style_q")} name="We do the rest"><X.WeDo /></Seq>

      {/* 4 · STYLES */}
      <Seq a={S("style_q")} b={S("style_trend")} name="Style?"><X.QBubble /></Seq>
      <Seq a={S("style_trend")} b={S("st_talking")} name="Trending"><X.Trending /></Seq>
      <Seq a={S("st_talking")} b={S("st_podcast")} name="01 talking head"><X.DemoTalking offset={fr(S("st_talking"))} /></Seq>
      <Seq a={S("st_podcast")} b={S("st_doc")} name="02 podcast"><X.DemoPodcast /></Seq>
      <Seq a={S("st_doc")} b={S("st_cine")} name="03 documentary"><X.DemoDoc /></Seq>
      <Seq a={S("st_cine")} b={S("st_motion")} name="04 cinematic"><X.DemoCine /></Seq>
      <Seq a={S("st_motion")} b={S("st_faceless")} name="05 motion"><X.DemoMotion /></Seq>
      <Seq a={S("st_faceless")} b={S("content")} name="06 faceless"><X.DemoFaceless /></Seq>
      {["st_talking", "st_podcast", "st_doc", "st_cine", "st_motion", "st_faceless"].map((id) => (
        <Seq key={id} a={S(id)} b={S(id) + 0.15}><X.Flash dur={4} /></Seq>
      ))}
      <Seq a={S("content")} b={S("scroll")} name="Your style grid"><X.ContentGrid shuffleF={rel("content", "tumhara", 1)} /></Seq>
      <Seq a={S("scroll")} b={S("reel")} name="Scroll stop"><X.ScrollStop stopF={rel("scroll", "stop")} /></Seq>

      {/* 5 · PRICE */}
      <Seq a={S("reel")} b={S("price")} name="Invoices"><X.Invoices drops={["har", "reel", "alag", "pay"].map((w) => rel("reel", w))} killF={rel("reel", "khatam")} /></Seq>
      <Seq a={sirfT} b={S("proof_b")} name="$200 reveal"><X.PriceReveal /></Seq>

      {/* 6 · PROOF */}
      <Seq a={S("proof_b")} b={S("slots")} name="10 creators"><X.CreatorsOrbit offset={fr(S("proof_b"))} countEnd={rel("proof_b", "creators") + 6} /></Seq>
      <Seq a={S("slots")} b={S("fcfs")} name="20 slots"><X.Slots /></Seq>
      <Seq a={S("fcfs")} b={S("cta_1")} name="First come"><X.BigLine text="FIRST COME, FIRST SERVE" icon={<IStopwatch size={84} color={C.amber} stroke={2.6} />} y={170} size={72} /></Seq>

      {/* 7 · CTA */}
      <Seq a={S("cta_1")} b={S("cta_2")} name="Comment EDIT"><X.CommentSheet typeF={rel("cta_1", "edit")} /></Seq>
      <Seq a={S("cta_2")} b={S("cta_3")} name="DM banner"><X.DMBanner /></Seq>
      <Seq a={S("cta_3")} b={S("kicker")} name="Bio / contact"><X.BioCard tapF={rel("cta_3", "contact")} offset={fr(S("cta_3"))} /></Seq>

      <Captions hide={HIDE} darkIn={DARK} yIn={YS} />

      {/* 8 · KICKER */}
      <Seq a={revealT} b={E("kicker") + 1} name="Editor reveal"><X.EditorReveal offset={fr(revealT)} captionsHide={[]} /></Seq>

      <Sound />
    </AbsoluteFill>
  );
};
