import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { CLIPS, FPS } from "./lib";
import { GROUPS } from "./Captions2";

/**
 * Minimal "pro" captions (researched from Iman Gadzhi-style reels):
 * small two-line text, centre frame; the spoken word turns bold white, the rest stay light.
 * Colour only on numbers / the CTA keyword. No bars, no glow, no bounce.
 */
type W = { w: string; s: number; e: number };
const clip = (id: string) => CLIPS.find((c) => c.id === id)!;
const clean = (w: string) => w.replace(/[—…]+$/g, "").replace(/^'|'$/g, "");
const ACCENT = /^(\$?\d+[,.]?|'EDIT'.*)$/;

type Phrase = { lines: W[][]; s: number; e: number };
const PHRASES: Phrase[] = GROUPS.map((g) => {
  const ws = [...g.lead, ...g.key, ...g.tail].map(([c, i]) => clip(c).words[i]).filter((w) => clean(w.w).length > 0);
  const n = ws.length;
  const cut = n <= 3 ? n : Math.ceil(n / 2);
  const lines = [ws.slice(0, cut), ws.slice(cut)].filter((l) => l.length);
  return { lines, s: ws[0].s, e: ws[n - 1].e };
}).map((p, i, arr) => ({ ...p, e: arr[i + 1] ? Math.min(arr[i + 1].s - 0.02, p.e + 0.5) : p.e + 0.5 }));

export const Captions4: React.FC<{ hide: [number, number][]; offset?: number; y?: number }> = ({ hide, offset = 0, y = 1150 }) => {
  const frame = useCurrentFrame();
  const t = (frame + offset) / FPS;
  if (hide.some(([a, b]) => t >= a && t < b)) return null;
  const p = PHRASES.find((x) => t >= x.s - 0.05 && t < x.e);
  if (!p) return null;
  const a = interpolate(t, [p.s - 0.05, p.s + 0.02], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 60, right: 60, top: y, textAlign: "center", opacity: a }}>
      <div style={{ position: "absolute", left: 40, right: 40, top: -30, bottom: -30, borderRadius: 120, background: "rgba(0,0,0,0.42)", filter: "blur(36px)" }} />
      {p.lines.map((ln, li) => (
        <div key={li} style={{ lineHeight: 1.18, position: "relative" }}>
          {ln.map((w, wi) => {
            const said = t >= w.s - 0.03;
            const accent = ACCENT.test(w.w.trim());
            return (
              <span key={wi} style={{
                fontFamily: "Montserrat", fontWeight: said ? 800 : 500, fontSize: 60, letterSpacing: "-0.01em", margin: "0 9px",
                color: said ? (accent ? "#F6C344" : "#FFFFFF") : "rgba(255,255,255,0.62)",
                textShadow: "0 2px 14px rgba(0,0,0,0.65), 0 0 2px rgba(0,0,0,0.4)",
              }}>{clean(w.w)}</span>
            );
          })}
        </div>
      ))}
    </div>
  );
};
