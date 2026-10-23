"""The edit: reel 1's structure, re-timed to our speaker's words.

Every segment of reel 1 (its cut list, in reel-1 seconds) is mapped onto the
new timeline by anchoring it to the word it was cut on, so each graphic lands on
the same word it did in the original. B-roll inside a segment is time-warped
piecewise between those word anchors.
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

    def at_src(piece, src_t):
        """Output time of a source moment inside a piece (for words the aligner could not place)."""
        for sp in spans:
            if sp["piece"] == piece and sp["src"][0] <= src_t <= sp["src"][1]:
                return sp["out"][0] + (src_t - sp["src"][0]) / tl.speed
        raise KeyError(piece)

    def piece_end(piece):
        return max(sp["out"][1] for sp in spans if sp["piece"] == piece)

    hell = W("p02", "hell")
    s2 = hell - 0.13
    s3 = piece_end("p03") + 0.50
    s4 = s3 + 3.79                                  # the music break keeps reel 1's exact length
    s5 = W("p05", "editing") + 0.52
    s6 = W("p08", "so") - 0.03
    s7 = W("p09", "you", 1) + 0.18
    s8 = W("p10", "first") + 0.12
    s9 = W("p13", "and") + 0.25
    that14 = at_src("p14", 120.85)
    s10 = that14 + 0.35
    s11 = W("p16", "we") - 0.08
    s12 = W("p18", "that") + 0.12
    s13 = W("p18", "and") - 0.02
    end = piece_end("p20") + 0.45

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
        # the montage's last flash (15.81) is the original speaker himself: leave it out
        dict(kind="broll", t=[s6, s7], v1=[13.72, 15.77]),
        dict(kind="aroll", t=[s7, s8]),
        dict(kind="broll", t=[s8, s9], v1=[18.23, 22.90],
             anchors=[(18.23, s8), (19.20, W("p10", "freelancing")), (20.00, W("p12", "contracts")),
                      (21.10, W("p12", "soon")), (22.40, W("p12", "agency")), (22.90, s9)]),
        dict(kind="aroll", t=[s9, s10]),
        dict(kind="broll", t=[s10, s11], v1=[25.57, 27.70]),
        dict(kind="aroll", t=[s11, s12]),
        dict(kind="broll", t=[s12, s13], v1=[29.53, 31.99]),
        dict(kind="aroll", t=[s13, end]),
    ]
    for s in seg:
        if "v1" in s and "anchors" not in s:
            s["anchors"] = [(s["v1"][0], s["t"][0]), (s["v1"][1], s["t"][1])]

    def w(piece, word, nth=0, style="reg", text=None):
        return dict(text=text or word, t=W(piece, word, nth), style=style)

    cards = [
        dict(start=s4, end=s5, lines=[[dict(text="SO", t=s4 + 0.06, style="so")]]),
        dict(start=s7, end=W("p09", "go"),
             lines=[[w("p09", "you", 1), w("p09", "just")],
                    [w("p09", "have"), w("p09", "to"), w("p09", "move")],
                    [w("p09", "forward", style="key")]]),
        dict(start=W("p09", "go"), end=s8,
             lines=[[w("p09", "go", text="Go", style="big"), w("p09", "with", style="big"), w("p09", "it", style="big")]]),
        dict(start=s9, end=W("p14", "into"),
             lines=[[w("p13", "and", text="And"), w("p13", "once"), w("p13", "you")],
                    [w("p14", "turn"), w("p14", "yourself")]]),
        dict(start=W("p14", "into"), end=W("p14", "just"),
             lines=[[w("p14", "into"), w("p14", "a")], [w("p14", "business", text="BUSINESS", style="key")]]),
        dict(start=W("p14", "just"), end=s10,
             lines=[[w("p14", "just")], [w("p14", "remember"), dict(text="that", t=that14, style="reg")]]),
        dict(start=s11, end=W("p17", "but"),
             lines=[[w("p16", "we", text="We"), w("p16", "can"), w("p16", "do"), w("p16", "a")],
                    [w("p16", "bunch"), w("p16", "of"), w("p16", "things")]]),
        dict(start=W("p17", "but"), end=s12, lines=[[w("p17", "but", style="big")]]),
        dict(start=s13, end=W("p18", "who"),
             lines=[[w("p18", "and"), w("p18", "you", 2), w("p18", "need", 1), w("p18", "a", 1)],
                    [w("p18", "team", 1, text="TEAM", style="key")],
                    [w("p18", "of"), w("p18", "good"), w("p18", "players")]]),
        dict(start=W("p18", "who"), end=W("p19", "the"),
             lines=[[w("p18", "who"), w("p18", "are"), w("p18", "ready")],
                    [w("p18", "to"), w("p18", "do"), w("p18", "things")]]),
        dict(start=W("p19", "the"), end=W("p20", "and"),
             lines=[[w("p19", "the"), w("p19", "way"), w("p19", "they")],
                    [w("p19", "should"), w("p19", "be"), w("p19", "done")]]),
        dict(start=W("p20", "and"), end=end,
             lines=[[w("p20", "and"), w("p20", "they're")],
                    [w("p20", "motivated", text="MOTIVATED", style="key")],
                    [w("p20", "enough")]]),
    ]
    return seg, cards, end


def v1_time(seg, t):
    """Reel-1 time shown at new time t inside a B-roll style segment (piecewise-linear warp)."""
    a = seg["anchors"]
    for (v0, n0), (v1, n1) in zip(a, a[1:]):
        if t <= n1 or (v1, n1) == a[-1]:
            k = (t - n0) / max(n1 - n0, 1e-6)
            return v0 + (v1 - v0) * min(max(k, 0.0), 1.0)
    return a[-1][0]
