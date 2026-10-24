import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, interpolate } from "remotion";
import { C, S, E, W, fr, FPS, DURATION, ICam } from "./lib";
import { Talking, PUNCHES, SHIFTS, GRAY, ENTERS } from "./Base";
import { Captions2, KEY_TIMES } from "./Captions2";
import * as X from "./Scenes";
import * as N from "./Scenes3";
import { ZoomIn, LightRing, InvertFlash, LightLeak } from "./Fx";
import META from "./sfx-meta.json";

export const MUSIC = true;

const t200 = W("hook_a", "$200");
const burnT = W("pain_4", "burnout") - 0.08;
const sirfT = W("price", "sirf") - 0.06;
const revealT = W("kicker", "humne") - 0.15;

PUNCHES.splice(0, PUNCHES.length, t200, W("hook_b", "editing"), W("pain_3", "post"), W("offer_2", "shoot"), W("style_q", "style"), W("content", "content"), W("fcfs", "first", 1), W("kicker", "humne"));
SHIFTS.splice(0, SHIFTS.length, [S("pain_3"), burnT]);
GRAY.splice(0, GRAY.length, [S("pain_1"), S("offer_1")]);
ENTERS.splice(0, ENTERS.length, 0, S("pain_3"), S("offer_2"), S("style_q"), S("content"), S("price"), S("fcfs"), S("kicker"));

const Seq: React.FC<{ a: number; b: number; children: React.ReactNode; name?: string }> = ({ a, b, children, name }) => (
  <Sequence from={fr(a)} durationInFrames={Math.max(1, fr(b) - fr(a))} name={name} layout="absolute-fill">{children}</Sequence>
);
const rel = (id: string, w: string, n = 0) => fr(W(id, w, n) - S(id));
const len = (a: number, b: number) => fr(b) - fr(a);

/* ---------------- caption visibility ---------------- */
const HIDE: [number, number][] = [
  [S("pain_1"), S("pain_2")], [burnT, S("offer_2")], [S("offer_3"), S("style_q")], [S("style_trend"), S("content")],
  [S("scroll"), S("price")], [sirfT, S("proof_b")], [S("slots"), S("fcfs")], [S("cta_1"), S("cta_2")], [S("cta_3"), S("kicker")], [revealT, 999],
];
const YS = [{ from: S("proof_b"), to: S("slots"), y: 1400 }];
const hidden = (t: number) => HIDE.some(([a, b]) => t >= a && t < b);

/* ---------------- sound design ---------------- */
type Fx = [string, number, number?, number?, number?]; // name, time, volume, max seconds, start offset (s)
const SWISH = ["swoosh_short", "sweep_fast", "whoosh_air"];
const keyFx: Fx[] = KEY_TIMES.filter((k) => !hidden(k.t + 0.01)).flatMap((k, i) => {
  const list: Fx[] = [[SWISH[i % 3], k.t - 0.06, 0.2, 0.55]];
  if (k.style === "green") list.push(["pop_light", k.t, 0.28]);
  if (k.style === "red") list.push(["bass_short", k.t, 0.32, 0.45]);
  if (k.style === "bar") list.push(["click_tech", k.t + 0.06, 0.22]);
  return list;
});
const sceneIn = [S("pain_1"), S("pain_2"), S("offer_3"), S("style_trend"), S("scroll"), S("reel"), S("proof_b"), S("slots"), S("cta_3")];
const FX: Fx[] = [
  ...keyFx,
  ...sceneIn.map((t, i) => [i % 2 ? "whoosh_cine" : "sweep_fast2", t - 0.1, 0.42] as Fx),
  ...ENTERS.filter((t) => t > 0).map((t) => ["whoosh_air", t - 0.06, 0.26, 0.6] as Fx),
  ["impact_logo", 0.0, 0.4], ["riser", t200 - 0.9, 0.22, 0.9, 5.38 - 0.9],
  ["coin_win", t200 + 0.1, 0.3],
  // pain (B&W)
  ...[0, 1, 2, 3, 4].map((i) => ["key_single", S("pain_1") + (6 + i * 2) / FPS, 0.35] as Fx), ["tick_counter", S("pain_1") + 0.7, 0.3],
  ["tick_timer", W("pain_2", "raat") - 0.1, 0.22, 1.5],
  ...[0, 1, 2, 3, 4, 5, 6].map((i) => ["pop_light", S("pain_3") + (5 + i * 3) / FPS, 0.16] as Fx),
  ["tech_slide", S("pain_4") + 0.1, 0.18, 1.0],
  ["glitch_quick", burnT, 0.45], ["bass_short", burnT, 0.5, 0.8], ["glitch_text", burnT + 0.1, 0.25],
  // colour returns
  ["impact_logo", S("offer_1"), 0.5], ["reveal", S("offer_1") + 0.05, 0.32], ["whoosh_cine", S("offer_1") - 0.12, 0.45], ["click_check", W("offer_1", "monthly") + 0.35, 0.3],
  ["typing_fast", S("offer_3") + 0.15, 0.16, 1.4], ...[0, 1, 2, 3, 4].map((i) => ["click_check", S("offer_3") + (4 + i * 6) / FPS, 0.22] as Fx), ["whoosh_cine", S("style_q") - 0.18, 0.4],
  // styles
  ...[0, 1, 2, 3, 4, 5].map((i) => ["click_tone", S("style_trend") + (2 + i * 4) / FPS, 0.16, 0.5] as Fx), ["sweep_air", S("st_talking") - 0.32, 0.36, 0.9],
  ["impact_logo", S("st_talking"), 0.35], ["shutter", S("st_talking") + 0.1, 0.3],
  ["sweep_fast", S("st_podcast") - 0.08, 0.42], ["bass_future", S("st_podcast"), 0.3, 0.5],
  ["whoosh_air", S("st_doc") - 0.08, 0.42], ...[0, 1, 2].map((i) => ["key_single", S("st_doc") + 0.3 + i * 0.15, 0.35] as Fx),
  ["sweep_fast2", S("st_cine") - 0.08, 0.42], ["whoosh_cine", S("st_motion") - 0.1, 0.42], ["glitch_quick", S("st_motion") + 0.05, 0.22],
  ["swoosh_short", S("st_faceless") - 0.05, 0.42], ["typing_fast", S("st_faceless"), 0.2, 1.2],
  ["sweep_air", S("scroll") + 0.1, 0.4, 1.6], ["impact_big", W("scroll", "stop"), 0.55], ["shutter", W("scroll", "stop") + 0.05, 0.3],
  // price
  ...["har", "reel", "alag", "pay"].map((w) => ["pop_dry", W("reel", w), 0.3] as Fx),
  ["impact_logo", W("reel", "khatam"), 0.5], ["glitch_text", W("reel", "khatam"), 0.3], ["whoosh_fast2", W("reel", "khatam") + 0.15, 0.35, 0.8],
  ["riser", sirfT - 1.3, 0.28, 1.3, 5.38 - 1.3], ["impact_big", sirfT, 0.5], ["slot_payout", sirfT + 0.25, 0.4], ["coins_clink", sirfT + 0.5, 0.35],
  // proof
  ["tick_counter", S("proof_b") + 0.2, 0.3], ["tick_counter", S("proof_b") + 0.9, 0.3], ["notif_correct", W("proof_b", "creators"), 0.3],
  ["tick_timer", S("slots") + 0.2, 0.18, 2.6], ["impact_zoom", W("slots", "20"), 0.35, 0.8],
  // cta
  ["whoosh_air", S("cta_1") - 0.05, 0.4], ...[0, 1, 2, 3].map((i) => ["key_single", W("cta_1", "edit") + i * 0.085, 0.42] as Fx), ["pop_hard", W("cta_1", "edit") + 0.42, 0.35],
  ["notif_positive", S("cta_2") + 0.08, 0.45], ["click_tone", W("cta_3", "contact"), 0.4],
  ["whoosh_cine", revealT - 0.05, 0.45], ["reveal", revealT + 0.3, 0.32], ["impact_logo", E("kicker") - 0.35, 0.35],
];

export const Sound: React.FC = () => (
  <>
    {MUSIC && <Audio src={staticFile("music.mp3")} volume={(f) => interpolate(f, [0, 8, DURATION - 20, DURATION], [0, 0.095, 0.095, 0], { extrapolateRight: "clamp" })} />}
    {FX.map(([n, t, v = 0.5, max, off = 0], i) => {
      const d = Math.min(max ?? 99, ((META as Record<string, number>)[n] ?? 1) - off);
      return (
        <Sequence key={i} from={Math.max(0, fr(t))} durationInFrames={Math.max(2, fr(d))} name={`sfx ${n}`}>
          <Audio src={staticFile(`sfx/${n}.mp3`)} volume={v} startFrom={fr(off)} />
        </Sequence>
      );
    })}
  </>
);

/** soft vignette + bottom shade for caption legibility + fine grain */
const Finish: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill style={{ background: "radial-gradient(120% 85% at 50% 40%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.42) 100%)" }} />
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 48%, rgba(0,0,0,0.38) 100%)" }} />
    <X.Grain opacity={0.06} />
  </AbsoluteFill>
);

export const Reel: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Talking />
    <Finish />
    <Seq a={0} b={0.7}><LightLeak dur={20} /></Seq>

    {/* 2 · PAIN (black & white) */}
    <Seq a={S("pain_1")} b={S("pain_2")} name="Shoot (cream)"><ZoomIn dur={len(S("pain_1"), S("pain_2"))} out={false}><N.ShootCream /></ZoomIn></Seq>
    <Seq a={S("pain_2")} b={S("pain_3")} name="Edit all night"><ZoomIn dur={len(S("pain_2"), S("pain_3"))}><X.PainEdit raatF={rel("pain_2", "raat")} /></ZoomIn></Seq>
    <Seq a={S("pain_3")} b={S("pain_4")} name="Posting glass"><N.PostGlass /></Seq>
    <Seq a={S("pain_4")} b={burnT} name="Growth glass"><N.GrowthGlass /></Seq>
    <Seq a={burnT} b={S("offer_1")} name="Burnout"><InvertFlash><X.Burnout /></InvertFlash></Seq>

    {/* 3 · OFFER: colour comes back */}
    <Seq a={S("offer_1")} b={S("offer_2")} name="Offer brand"><X.OfferBrand nameF={rel("offer_1", "aminur")} pkgF={rel("offer_1", "monthly")} offset={fr(S("offer_1"))} /></Seq>
    <Seq a={S("offer_1") - 0.08} b={S("offer_1") + 0.6} name="Light ring"><LightRing /></Seq>
    <Seq a={S("offer_3")} b={S("style_q")} name="We edit checklist"><ZoomIn dur={len(S("offer_3"), S("style_q"))} out={false}><N.WeEdit offset={fr(S("offer_3"))} dur={len(S("offer_3"), S("style_q"))} /></ZoomIn></Seq>

    {/* 4 · STYLES */}
    <Seq a={S("style_trend")} b={S("st_talking")} name="Navy styles"><ZoomIn dur={len(S("style_trend"), S("st_talking"))} out={false}><N.NavyStyles panAt={len(S("style_trend"), S("st_talking")) - 9} trendF={rel("style_trend", "trend")} /></ZoomIn></Seq>
    <Seq a={S("st_talking")} b={S("st_podcast")} name="01 talking head"><ZoomIn dur={99} out={false}><X.DemoTalking offset={fr(S("st_talking"))} /></ZoomIn></Seq>
    <Seq a={S("st_podcast")} b={S("st_doc")} name="02 podcast"><ZoomIn dur={99} out={false}><X.DemoPodcast /></ZoomIn></Seq>
    <Seq a={S("st_doc")} b={S("st_cine")} name="03 documentary"><ZoomIn dur={99} out={false}><X.DemoDoc /></ZoomIn></Seq>
    <Seq a={S("st_cine")} b={S("st_motion")} name="04 cinematic"><ZoomIn dur={99} out={false}><X.DemoCine /></ZoomIn></Seq>
    <Seq a={S("st_motion")} b={S("st_faceless")} name="05 motion"><ZoomIn dur={99} out={false}><X.DemoMotion /></ZoomIn></Seq>
    <Seq a={S("st_faceless")} b={S("content")} name="06 faceless"><ZoomIn dur={len(S("st_faceless"), S("content"))}><X.DemoFaceless /></ZoomIn></Seq>
    <Seq a={S("scroll")} b={S("reel")} name="Scroll stop"><ZoomIn dur={len(S("scroll"), S("reel"))} out={false}><X.ScrollStop stopF={rel("scroll", "stop")} /></ZoomIn></Seq>

    {/* 5 · PRICE */}
    <Seq a={S("reel")} b={S("price")} name="Invoices"><ZoomIn dur={len(S("reel"), S("price"))}>
      <X.Invoices drops={["har", "reel", "alag", "pay"].map((w) => rel("reel", w))} killF={rel("reel", "khatam")} />
      <N.InvoiceHead killF={rel("reel", "khatam")} />
    </ZoomIn></Seq>
    <Seq a={sirfT} b={S("proof_b")} name="$200 reveal"><X.PriceReveal /></Seq>
    <Seq a={sirfT - 0.06} b={sirfT + 0.6} name="Light ring"><LightRing color="#9dffc7" /></Seq>

    {/* 6 · PROOF */}
    <Seq a={S("proof_b")} b={S("slots")} name="10 creators"><ZoomIn dur={len(S("proof_b"), S("slots"))} out={false}><X.CreatorsOrbit offset={fr(S("proof_b"))} countEnd={rel("proof_b", "creators") + 6} /></ZoomIn></Seq>
    <Seq a={S("slots")} b={S("fcfs")} name="20 slots"><ZoomIn dur={len(S("slots"), S("fcfs"))}><X.Slots /></ZoomIn></Seq>

    {/* 7 · CTA */}
    <Seq a={S("cta_1")} b={S("cta_2")} name="Comment EDIT"><X.CommentSheet typeF={rel("cta_1", "edit")} /></Seq>
    <Seq a={S("cta_2")} b={S("cta_3")} name="DM banner"><X.DMBanner /></Seq>
    <Seq a={S("cta_3")} b={S("kicker")} name="Bio / contact"><ZoomIn dur={len(S("cta_3"), S("kicker"))}><X.BioCard tapF={rel("cta_3", "contact")} offset={fr(S("cta_3"))} /></ZoomIn></Seq>

    <Captions2 hide={HIDE} y={YS} />

    {/* 8 · KICKER */}
    <Seq a={revealT} b={E("kicker") + 1} name="Editor reveal"><X.EditorReveal offset={fr(revealT)} captionsHide={[]} /></Seq>

    <Sound />
  </AbsoluteFill>
);
