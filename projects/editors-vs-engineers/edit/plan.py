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
    s4 = s3 + 3.79                                  # the music break keeps reel 1's exact length
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

    def w(piece, word, nth=0, style="reg", text=None):
        return dict(text=text or word, t=W(piece, word, nth), style=style)

    cards = [
        dict(start=s4, end=s5, lines=[[dict(text="SO", t=s4 + 0.06, style="so")]]),
        dict(start=s7, end=W("p11", "go"),
             lines=[[w("p10", "you"), w("p10", "just")],
                    [w("p10", "have"), w("p10", "to"), w("p10", "move")],
                    [w("p10", "forward", style="key")]]),
        dict(start=W("p11", "go"), end=s8,
             lines=[[w("p11", "go", text="Go", style="big"), w("p11", "with", style="big"), w("p11", "it", style="big")]]),
        dict(start=s9, end=W("p17", "into"),
             lines=[[w("p16", "and", text="And"), w("p16", "once"), w("p16", "you")],
                    [w("p17", "turn"), w("p17", "yourself")]]),
        dict(start=W("p17", "into"), end=W("p18", "just"),
             lines=[[w("p17", "into"), w("p17", "a")], [w("p17", "business", text="BUSINESS", style="key")]]),
        dict(start=W("p18", "just"), end=s10,
             lines=[[w("p18", "just")], [w("p18", "remember"), w("p18", "that")]]),
        dict(start=s11, end=W("p21", "but"),
             lines=[[w("p20", "we", text="We"), w("p20", "can"), w("p20", "do"), w("p20", "a")],
                    [w("p20", "bunch"), w("p20", "of"), w("p20", "things")]]),
        dict(start=W("p21", "but"), end=s12,
             lines=[[w("p21", "but", style="big"), w("p21", "this", style="big")]]),
        dict(start=s13, end=W("p26", "who"),
             lines=[[w("p24", "and"), w("p24", "you"), w("p24", "need"), w("p24", "a")],
                    [w("p24", "team", text="TEAM", style="key")],
                    [w("p25", "of"), w("p25", "good"), w("p25", "players")]]),
        dict(start=W("p26", "who"), end=W("p27", "the"),
             lines=[[w("p26", "who"), w("p26", "are"), w("p26", "ready")],
                    [w("p26", "to"), w("p26", "do"), w("p26", "things")]]),
        dict(start=W("p27", "the"), end=W("p28", "and"),
             lines=[[w("p27", "the"), w("p27", "way"), w("p27", "they")],
                    [w("p27", "should"), w("p27", "be"), w("p27", "done")]]),
        dict(start=W("p28", "and"), end=end,
             lines=[[w("p28", "and"), w("p28", "they"), w("p28", "are")],
                    [w("p28", "motivated", text="MOTIVATED", style="key")],
                    [w("p28", "enough")]]),
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
