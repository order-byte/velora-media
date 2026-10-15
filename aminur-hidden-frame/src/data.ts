// Edit-timeline data. Times are seconds on the final timeline (frame = t * 30).
// Clip boundaries come from scripts/edl.json via build_selects.py (timeline.json).

export type Clip = { id: string; start: number; end: number };

export const CLIPS: Clip[] = [
  { id: "hook", start: 0, end: 1.8667 },
  { id: "find", start: 1.8667, end: 2.9 },
  { id: "name", start: 2.9, end: 5.0 },
  { id: "frames", start: 5.0, end: 7.2667 },
  { id: "movies", start: 7.2667, end: 10.0 },
  { id: "numbers", start: 10.0, end: 12.1 },
  { id: "tenmin", start: 12.1, end: 14.5 },
  { id: "ads", start: 14.5, end: 15.3833 },
  { id: "notads", start: 15.3833, end: 17.8167 },
  { id: "delivered", start: 17.8167, end: 20.05 },
  { id: "team", start: 20.05, end: 23.25 },
  { id: "everyframe", start: 23.25, end: 25.4167 },
  { id: "found", start: 25.4167, end: 26.3833 },
  { id: "dm", start: 26.3833, end: 27.8167 },
  { id: "nahimila", start: 27.8167, end: 28.9167 },
  { id: "editor", start: 28.9167, end: 30.65 },
  { id: "twice", start: 30.65, end: 33.6167 },
  { id: "service", start: 33.6167, end: 35.8833 },
  { id: "bio", start: 35.8833, end: 37.3333 },
];

export type Word = { w: string; t: number; em?: boolean };
export type Chunk = { start: number; end: number; words: Word[]; hide?: boolean };

// Word-by-word burned-in captions. `em` words sit on a highlighter label.
// `hide` chunks are shown as big type by the beat itself.
export const CAPTIONS: Chunk[] = [
  { start: 0.0, end: 0.95, words: [{ w: "I", t: 0.0 }, { w: "hid", t: 0.14 }, { w: "one", t: 0.4, em: true }, { w: "frame", t: 0.68, em: true }] },
  { start: 0.95, end: 1.86, words: [{ w: "in", t: 0.96 }, { w: "this", t: 1.12 }, { w: "video.", t: 1.24 }] },
  { start: 1.87, end: 2.89, hide: true, words: [{ w: "Dhoondh", t: 1.87 }, { w: "ke", t: 2.17 }, { w: "dikhao.", t: 2.29 }] },
  { start: 2.9, end: 3.79, words: [{ w: "I", t: 2.9 }, { w: "am", t: 3.06 }, { w: "Aminur,", t: 3.22 }] },
  { start: 3.79, end: 4.99, words: [{ w: "a", t: 3.8 }, { w: "video", t: 3.92 }, { w: "editor.", t: 4.3 }] },
  { start: 5.0, end: 5.58, hide: true, words: [{ w: "Frames?", t: 5.02 }] },
  { start: 5.58, end: 7.26, words: [{ w: "Woh", t: 5.6 }, { w: "toh", t: 5.98 }, { w: "mera", t: 6.22 }, { w: "game", t: 6.4, em: true }, { w: "hai.", t: 6.78 }] },
  { start: 7.27, end: 8.74, words: [{ w: "I", t: 7.27 }, { w: "make", t: 7.45 }, { w: "30-second", t: 7.71 }, { w: "reels", t: 8.45 }] },
  { start: 8.74, end: 9.99, words: [{ w: "feel", t: 8.77 }, { w: "like", t: 9.0 }, { w: "a", t: 9.2 }, { w: "movie.", t: 9.33, em: true }] },
  { start: 10.0, end: 10.57, words: [{ w: "Boring", t: 10.0 }, { w: "numbers", t: 10.3 }] },
  { start: 10.57, end: 12.09, words: [{ w: "feel", t: 10.59 }, { w: "like", t: 10.91 }, { w: "stories.", t: 11.24, em: true }] },
  { start: 12.1, end: 12.93, words: [{ w: "10-minute", t: 12.1 }, { w: "videos", t: 12.56 }] },
  { start: 12.93, end: 14.49, words: [{ w: "feel", t: 12.96 }, { w: "like", t: 13.25 }, { w: "2", t: 13.45, em: true }, { w: "minutes.", t: 13.77 }] },
  { start: 14.5, end: 15.38, words: [{ w: "Aur", t: 14.5 }, { w: "ads?", t: 14.68, em: true }] },
  { start: 15.39, end: 16.63, words: [{ w: "Woh", t: 15.4 }, { w: "ads", t: 15.74 }, { w: "hi", t: 15.92 }, { w: "nahi", t: 16.12 }, { w: "lagta", t: 16.3 }, { w: "hai.", t: 16.52 }] },
  { start: 16.63, end: 17.81, words: [{ w: "Kuch", t: 16.66 }, { w: "aur", t: 16.8, em: true }, { w: "hi", t: 17.04 }, { w: "lagta", t: 17.2 }, { w: "hai.", t: 17.44 }] },
  { start: 17.82, end: 20.04, words: [{ w: "I", t: 17.82 }, { w: "delivered", t: 17.94 }, { w: "over", t: 18.28 }, { w: "2,000", t: 18.62 }, { w: "videos.", t: 18.92 }] },
  { start: 20.05, end: 21.19, words: [{ w: "And", t: 20.05 }, { w: "my", t: 20.24 }, { w: "team", t: 20.33 }, { w: "is", t: 20.69 }, { w: "currently", t: 20.95 }] },
  { start: 21.19, end: 23.24, words: [{ w: "handling", t: 21.21 }, { w: "60+", t: 21.8, em: true }, { w: "clients.", t: 22.52 }] },
  { start: 23.25, end: 24.06, words: [{ w: "Aur", t: 23.25 }, { w: "har", t: 23.51 }, { w: "ek…", t: 23.83 }] },
  { start: 24.06, end: 25.41, words: [{ w: "frame", t: 24.09, em: true }, { w: "by", t: 24.47 }, { w: "frame.", t: 24.75, em: true }] },
  { start: 25.42, end: 26.37, words: [{ w: "Found", t: 25.42 }, { w: "it?", t: 25.81 }] },
  { start: 26.38, end: 27.81, words: [{ w: "DM", t: 26.38 }, { w: "me", t: 26.7 }, { w: "what", t: 26.93 }, { w: "it", t: 27.12 }, { w: "says.", t: 27.3 }] },
  { start: 27.82, end: 28.91, words: [{ w: "Nahi", t: 27.82 }, { w: "mila", t: 28.14 }, { w: "na?", t: 28.34 }] },
  { start: 28.92, end: 30.64, words: [{ w: "Tabhi", t: 28.92 }, { w: "toh", t: 29.3 }, { w: "editor", t: 29.46 }, { w: "main", t: 29.76 }, { w: "hoon.", t: 30.0 }] },
  { start: 30.65, end: 31.5, words: [{ w: "I", t: 30.65 }, { w: "make", t: 30.79 }, { w: "videos", t: 31.02 }] },
  { start: 31.5, end: 33.61, words: [{ w: "that", t: 31.53 }, { w: "people", t: 32.09 }, { w: "watch", t: 32.49 }, { w: "twice.", t: 32.81, em: true }] },
  { start: 33.62, end: 34.28, words: [{ w: "So", t: 33.62 }, { w: "if", t: 33.78 }, { w: "you", t: 33.98 }, { w: "need", t: 34.08 }] },
  { start: 34.28, end: 35.87, words: [{ w: "my", t: 34.3 }, { w: "service,", t: 34.46 }, { w: "then", t: 34.84 }] },
  { start: 35.88, end: 37.32, words: [{ w: "contact", t: 35.88 }, { w: "number", t: 36.15 }, { w: "in", t: 36.41 }, { w: "my", t: 36.65 }, { w: "bio.", t: 36.76, em: true }] },
];

export const clipAt = (t: number) => CLIPS.find((c) => t >= c.start && t < c.end) ?? CLIPS[CLIPS.length - 1];
