"""The edit: reel 1's structure, re-timed to our speaker's words.

Every segment of reel 1 (its cut list, in reel-1 seconds) is mapped onto the
new timeline by anchoring it to the word it was cut on, so each graphic lands on
the same word it did in the original. B-roll inside a segment is time-warped
piecewise between those word anchors. Reel 1's photo montage is replaced by our
own "right path" animation.
"""
import re

FPS = 24000 / 1001


def build(tl):
    """tl: tools/timeline.Timeline. Returns (segments, caption_cards, duration)."""
    spans = tl.spans

    def norm(s):
        return re.sub(r"[^a-z']", "", s.lower())

    def W(piece, word, nth=0, end=False):
        hits = [w for sp in spans if sp["piece"] == piece for w in sp["words"] if norm(w["w"]) == word]
        w = hits[nth]
        return w["end"] if end else w["t"]

    def piece_end(piece):
        return max(sp["out"][1] for sp in spans if sp["piece"] == piece)

    hell = W("p02", "hell")
    s2 = hell - 0.13
    s3 = piece_end("p03") + 0.50
    s4 = W("p04", "so") - 0.10                      # back on camera as "So" starts (break ~reel 1's length)
    s5 = W("p05", "editing") + 0.52
    s6 = W("p08", "so") - 0.03
    s7 = W("p10", "you") + 0.18
    s8 = W("p12", "first") + 0.12
    s9 = W("p16", "and") + 0.25
    s10 = W("p18", "that") + 0.35
    s11 = W("p20", "we") - 0.08
    s12 = W("p21", "is") - 0.04
    s13 = W("p24", "and") - 0.02
    end = piece_end("p28") + 0.45

    seg = [
        dict(kind="bars", t=[0.0, s2], entrance=True),
        dict(kind="paper", t=[s2, s3], v1=[2.17, 6.05],
             anchors=[(2.17, s2), (2.33, hell), (3.00, W("p03", "a")), (3.50, W("p03", "editors")),
                      (4.13, W("p03", "making") - 0.17), (4.67, W("p03", "doctor") - 0.36),
                      (5.10, W("p03", "doctor")), (6.05, s3)]),
        # reel 1 starts blurring into its next talking-head shot at 9.72: stop just before
        dict(kind="broll", t=[s3, s4], v1=[6.05, 9.70]),
        dict(kind="aroll", t=[s4, s5], entrance=True),
        dict(kind="monitor", t=[s5, s6], v1=[11.22, 13.72],
             anchors=[(11.22, s5), (12.20, W("p06", "going")), (12.70, W("p07", "get")),
                      (13.50, W("p07", "bigger", 1)), (13.72, s6)]),
        dict(kind="path", t=[s6, s7], t_trust=W("p08", "trust") - s6, t_choose=W("p09", "choose") - s6,
             t_right=W("p09", "right") - s6),
        dict(kind="aroll", t=[s7, s8]),
        dict(kind="broll", t=[s8, s9], v1=[18.23, 22.90],
             anchors=[(18.23, s8), (19.20, W("p12", "freelancing")), (20.00, W("p13", "contracts")),
                      (21.10, W("p14", "soon")), (22.40, W("p15", "agency")), (22.90, s9)]),
        dict(kind="aroll", t=[s9, s10]),
        dict(kind="broll", t=[s10, s11], v1=[25.57, 27.70]),
        dict(kind="aroll", t=[s11, s12]),
        dict(kind="broll", t=[s12, s13], v1=[29.53, 31.99]),
        dict(kind="aroll", t=[s13, end]),
    ]
    for s in seg:
        if "v1" in s and "anchors" not in s:
            s["anchors"] = [(s["v1"][0], s["t"][0]), (s["v1"][1], s["t"][1])]
        if s["kind"] == "broll":
            # reel 1's own entry transition (flashes, whips) plays at its original speed
            (v0, n0), (v1, n1) = s["anchors"][0], s["anchors"][1]
            if v1 - v0 > 0.3 and n1 - n0 > 0.3:
                s["anchors"].insert(1, (v0 + 0.17, n0 + 0.17))

    cards = caption_cards(spans, seg)
    return seg, cards, end


KEYWORDS = {"forward": "forward", "business": "BUSINESS", "team": "TEAM", "motivated": "MOTIVATED"}


def _lines(words, max_words=4, max_chars=20):
    """Break a run of ordinary words into balanced short lines."""
    n = len(words)
    if not n:
        return []
    k = 1
    while True:
        size = -(-n // k)
        chunks = [words[i:i + size] for i in range(0, n, size)]
        if all(len(c) <= max_words and sum(len(w["text"]) for w in c) + len(c) - 1 <= max_chars for c in chunks):
            return chunks
        k += 1


def caption_cards(spans, seg):
    """Every spoken word, the way pro reels caption: phrases split at real pauses, each phrase
    cut evenly into cards of a few words on balanced lines, keywords big and yellow on their own
    line inside the card. The torn-paper segment is left alone (its HELL / EDITORS / DOCTORS
    graphics are the captions there); over the opening bar chart captions sit at the top."""
    paper = next(s["t"] for s in seg if s["kind"] == "paper")
    bars = next(s["t"] for s in seg if s["kind"] == "bars")
    words = [dict(w) for sp in spans for w in sp["words"] if not (paper[0] - 0.05 <= w["t"] < paper[1])]
    phrases, cur = [], []
    for i, w in enumerate(words):
        if cur and w["t"] - cur[-1]["end"] > 0.25:
            phrases.append(cur)
            cur = []
        cur.append(w)
    phrases.append(cur)

    cards = []
    for ph in phrases:
        toks = []
        for w in ph:
            word = w["w"].lower()
            if word in KEYWORDS:
                toks.append(dict(text=KEYWORDS[word], t=w["t"], end=w["end"], style="key"))
            elif word == "so" and len(ph) == 1:
                toks.append(dict(text="SO", t=w["t"], end=w["end"], style="so"))
            else:
                toks.append(dict(text=word, t=w["t"], end=w["end"], style="reg"))
        normal = [t for t in toks if t["style"] == "reg"]
        has_key = any(t["style"] == "key" for t in toks)
        n_cards = max(1, -(-len(normal) // (7 if has_key else 6)))
        per = -(-len(normal) // n_cards)
        # walk the phrase, starting a new card every `per` ordinary words (keywords ride along)
        groups, g, count = [], [], 0
        for t in toks:
            if t["style"] == "reg" and count == per:
                groups.append(g)
                g, count = [], 0
            g.append(t)
            count += t["style"] == "reg"
        groups.append(g)
        for g in groups:
            lines, run = [], []
            for t in g:
                if t["style"] == "key":
                    lines += _lines(run)
                    run = []
                    lines.append([t])
                else:
                    run.append(t)
            lines += _lines(run)
            cards.append(dict(start=g[0]["t"] - 0.1, end=None, last=max(t["end"] for t in g), lines=lines,
                              y=0.17 if g[0]["t"] < bars[1] else 0.68))
    # cream-coloured scenes (smileys, skills, the right-path animation) get dark captions
    light_bg = [s["t"] for s in seg if s["kind"] == "path" or (s["kind"] == "broll" and s["v1"][0] > 15)]
    for c in cards:
        mid = (c["start"] + c["last"]) / 2
        c["theme"] = "dark" if any(a <= mid < b for a, b in light_bg) else "light"
    for c, nxt in zip(cards, cards[1:] + [None]):
        hold = c["last"] + 0.5
        c["end"] = min(nxt["start"] - 0.02, hold if nxt["start"] - c["last"] > 0.8 else nxt["start"]) if nxt else hold
        c["end"] = max(c["end"], c["last"] + 0.1)
    return cards


def v1_time(seg, t):
    """Reel-1 time shown at new time t inside a B-roll style segment (piecewise-linear warp)."""
    a = seg["anchors"]
    for (v0, n0), (v1, n1) in zip(a, a[1:]):
        if t <= n1 or (v1, n1) == a[-1]:
            k = (t - n0) / max(n1 - n0, 1e-6)
            return v0 + (v1 - v0) * min(max(k, 0.0), 1.0)
    return a[-1][0]
