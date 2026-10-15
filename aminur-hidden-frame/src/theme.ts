// Brand palette from the Figma brief: neutral base + ONE accent per frame.
export const C = {
  black: "#000000",
  white: "#FFFFFF",
  gray1: "#EFEFEF",
  gray2: "#B6B6B6",
  yellow: "#EEFF00", // Atomic yellow
  blue: "#065BFF", // Electric blue
  ink: "#0B0B0B",
};

// Europa Grotesk SH Bold role (big hits, numbers). Stand-in: Inter Tight 800/900 (OFL).
// Drop the licensed Europa Grotesk SH Bold file into public/fonts and point DISPLAY_FONT_FILES at it.
export const FONT_DISPLAY = "DisplayGrotesk";
// HK Nova role (captions, UI, secondary lines). Stand-in: Hanken Grotesk (OFL), the board's own stand-in.
export const FONT_TEXT = "TextGrotesk";

export const DISPLAY_FONT_FILES = [
  { file: "fonts/InterTight-800.ttf", weight: "800" },
  { file: "fonts/InterTight-900.ttf", weight: "900" },
];
export const TEXT_FONT_FILES = [
  { file: "fonts/HankenGrotesk-400.ttf", weight: "400" },
  { file: "fonts/HankenGrotesk-500.ttf", weight: "500" },
  { file: "fonts/HankenGrotesk-700.ttf", weight: "700" },
  { file: "fonts/HankenGrotesk-800.ttf", weight: "800" },
];

export const FPS = 30;
export const W = 1080;
export const H = 1920;
// Safe zone from the brief: keep text 220 px from the top and 380 px from the bottom.
export const SAFE_TOP = 220;
export const SAFE_BOTTOM = H - 380;

export const SELECTS_FRAMES = 1120; // graded talking-head selects (37.33 s)
export const END_CARD_FRAMES = 48;
export const TOTAL_FRAMES = SELECTS_FRAMES + END_CARD_FRAMES;

// The one hidden frame. Exactly one frame on the timeline shows the secret.
export const HIDDEN_FRAME = 391;
export const SECRET = "FRAME GAME";
