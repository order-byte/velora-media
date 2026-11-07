"""Build the edit decision list (EDL) for the Offscript VSL, step 1 (motion).

Every cue is anchored to the speaker's words via the word-level transcript, so
text pops, graphics and B-roll land on the exact syllable.

Usage: python3 build_edl.py <transcript.json> <face.json> <out_edl.json>
"""
import json, random, re, sys
import numpy as np

transcript, face_path, out_path = sys.argv[1:4]
T = json.load(open(transcript))
WORDS = [w for s in T["segments"] for w in s["words"]]
DUR = 356.38
HOOK_END = 41.3          # no B-roll before this point (the hook + intro stay on the speaker)


def norm(s):
    return re.sub(r"[^a-z0-9']", "", s.lower().replace("’", "'"))


TOK = [norm(w["w"]) for w in WORDS]


def find(phrase, after=0.0):
    """Return (start, end) of the first occurrence of `phrase` starting at/after `after`."""
    want = [norm(p) for p in phrase.split()]
    want = [p for p in want if p]
    for i in range(len(WORDS)):
        if WORDS[i]["s"] + 1e-3 < after:
            continue
        j, k = i, 0
        while k < len(want) and j < len(WORDS):
            if TOK[j] == "":
                j += 1
                continue
            if TOK[j] != want[k]:
                break
            j += 1
            k += 1
        if k == len(want):
            return WORDS[i]["s"], WORDS[j - 1]["e"]
    raise KeyError(f"phrase not found: {phrase!r} after {after}")


def S(phrase, after=0.0):
    return round(find(phrase, after)[0], 3)


def E(phrase, after=0.0):
    return round(find(phrase, after)[1], 3)


texts, graphics, broll = [], [], []


def stack(lead, hero, start, hero_at, end, side="L", accent=False, label=None, hero_font="serif"):
    texts.append(dict(type="stack", lead=lead, hero=hero, start=start, hero_at=hero_at, end=end,
                      side=side, accent=accent, hero_font=hero_font, label=label or f"{lead} {hero}".strip()))


def chips(lead, items, start, end, side="L", tone="ink", label=None):
    texts.append(dict(type="chips", lead=lead, items=[dict(text=t, at=a) for t, a in items], start=start, end=end,
                      side=side, tone=tone, label=label or (lead + " " + " · ".join(t for t, _ in items)).strip()))


def marker(text, start, end, side="R", lead="", label=None, y=0.30):
    texts.append(dict(type="marker", text=text, lead=lead, start=start, end=end, side=side, y=y,
                      label=label or f"{lead} {text}".strip()))


def wordlist(items, final, final_at, start, end, side="L", label=None):
    texts.append(dict(type="wordlist", items=[dict(text=t, at=a) for t, a in items], final=final, final_at=final_at,
                      start=start, end=end, side=side, label=label or " / ".join(t for t, _ in items) + " / " + final))


def counter(lead, prefix, steps, suffix, sub, start, end, side="L", tone="ink", label=None):
    """steps: list of (value, at) — number rolls to each value at its word."""
    texts.append(dict(type="counter", lead=lead, prefix=prefix, steps=[dict(value=v, at=a) for v, a in steps],
                      suffix=suffix, sub=sub, start=start, end=end, side=side, tone=tone,
                      label=label or f"{lead} {prefix}{steps[-1][0]:,}{suffix}"))


def gfx(kind, start, end, label, fullscreen=True, **params):
    graphics.append(dict(type=kind, start=start, end=end, label=label, fullscreen=fullscreen, params=params))


def roll(clip, start, end, label, clip_in=0.0, caption=None, chip_items=None):
    broll.append(dict(clip=clip, start=start, end=end, label=label, clip_in=clip_in, caption=caption,
                      chips=[dict(text=t, at=a) for t, a in (chip_items or [])]))


# ------------------------------------------------------------------ HOOK (no B-roll)
stack("What are you trying to", "prove?", S("what are you trying"), S("prove"), S("who are you trying") - 0.08, side="L")
stack("Who are you trying to", "satisfy?", S("who are you trying"), S("satisfy"), S("the society") - 0.05, side="R")
wordlist([("The society", S("the society")), ("your parents", S("your parents")), ("your cousin", S("your cousin")),
          ("your aunt", S("your aunt"))], "or yourself?", S("yourself"), S("the society"), S("who do you want") - 0.08,
         side="L")
stack("Who do you want to", "live for?", S("who do you want"), S("live for"), S("because this is the way") - 0.1, side="R")
stack("We're not here to follow", "other people's script", S("we're not here to follow"), S("other people's script"),
      S("we're not here to leave") - 0.1, side="L")
stack("We're here to write our own", "destiny.", S("we're here to write"), S("destiny"), S("we're here to be") + 0.45,
      side="R", accent=True)
gfx("offscript_title", S("off script so welcome") - 0.15, S("my name is") - 0.05, "OFF-SCRIPT title reveal",
    fullscreen=False, strike_at=S("script so welcome"), welcome_at=S("welcome to off"), side="L")
counter("This year I personally closed", "$", [(60_000_000, S("60 million"))], "+", "in personal production",
        S("this year i personally"), S("i'm not telling you this") - 0.05, side="L", label="$60M closed counter")
marker("not to impress you.", S("i'm not telling you this"), S("i'm telling you to let") - 0.05, side="R",
       lead="I'm telling you this")
stack("I know", "both sides.", S("know that i know both") + 0.3, S("both sides"), S("i was homeless") - 0.02, side="R")

# ------------------------------------------------------------------ BODY (B-roll allowed from here)
roll("5978", S("i was homeless"), S("i made millions") - 0.02, "Homeless before", clip_in=3.0, caption="BEFORE")
roll("18304", S("i made millions"), E("pick to make millions") + 0.15, "Made millions", clip_in=1.0, caption="AFTER")
stack("the difference between", "homeless", S("the difference between") , S("homeless", 49), S("and close the largest") - 0.02,
      side="L", label="the difference between homeless…")
roll("11814", S("and close the largest"), S("it's not complicated") - 0.05, "Largest investor deal, South Florida",
     clip_in=0.5, caption="SOUTH FLORIDA")
stack("It's not complicated…", "but very, very difficult.", S("it's not complicated"), S("but it's very very"),
      S("i got to the point that i realized") - 0.1, side="L", accent=True)
stack("Everything is", "programmed.", S("everything is programmed"), S("programmed"), S("everything is basically") - 0.05,
      side="R")
stack("Everything is basically", "preset.", S("everything is basically"), S("preset"), S("we've been told") - 0.1, side="R")
gfx("script_page", S("we've been told"), S("i just didn't like that") + 0.85, "The script you were handed (full-screen)",
    header="THE SCRIPT YOU WERE HANDED",
    scenes=[dict(text="GO TO SCHOOL", at=S("go to the school")), dict(text="GET YOUR DEGREE", at=S("get your degrees")),
            dict(text="GET GRADUATED", at=S("get graduated")), dict(text="GET A JOB", at=S("go get a job")),
            dict(text="RETIRE AT 60–65", at=S("retire at"))],
    strike_at=S("i just didn't like that"))
stack("Someone else wrote", "a script for me.", S("someone else is wrote"), S("a script for me"), S("i got to the point that i was") - 0.1,
      side="L")
stack("What if I don't want", "that type of life?", S("what if i don't"), S("that type of life"), S("no one asked me what type") - 0.05,
      side="R")
marker("No one asked me.", S("no one asked me what type"), S("no one asked me what is") - 0.05, side="L")
roll("8861", S("what is the cost of going"), S("by school i mean"), "Cost of college", clip_in=1.0,
     chip_items=[("5 years", S("five years")), ("10 years", S("10 years"))])
roll("15923", S("go to college at"), S("with a lot of student") - 0.02, "10–15 years of college", clip_in=1.0,
     chip_items=[("10 years", S("10 years", 96)), ("15 years", S("15 years"))])
counter("with student loans", "$", [(100_000, S("100", 100)), (200_000, S("200", 101))], "", "in debt",
        S("with a lot of student"), S("and you're gonna go to the market") - 0.05, side="R", tone="red",
        label="$200K student debt counter")
roll("6052", S("and you're gonna go to the market"), S("all these people") + 0.3, "Competing for jobs", clip_in=2.0,
     caption=None)
marker("Now what?", S("and now what"), S("you're gonna compete") - 0.05, side="R", y=0.24)
chips("Competing for", [("$60K", S("60", 108)), ("$100K", S("100", 109.5)), ("$200K", S("200", 110))],
      S("for 60", 108) - 0.25, S("you might get it") + 0.6, side="L", label="Salary chips $60K / $100K / $200K")
marker("Why?", S("why", 115), S("i can teach you how to make money") - 0.05, side="R", y=0.28)
stack("I can teach you to make money in", "six months.", S("i can teach you how to make money"), S("six months"),
      S("if you want to go to the college") - 0.1, side="L", accent=True)
stack("College for the sake of money?", "Do not do that.", S("for the sake of money"), S("do not do that"),
      S("this is not for me") - 0.05, side="R")
roll("16108", S("don't become a lawyer"), S("don't become a doctor") - 0.02, "Lawyer", clip_in=1.0)
roll("29933", S("don't become a doctor"), S("if you want to become a lawyer") - 0.02, "Doctor", clip_in=2.0)
stack("We need good doctors", "but not for money.", S("we need good lawyers"), S("but not for money"), S("if it's your passion") - 0.05,
      side="L")
stack("If it's your", "passion, do it.", S("if it's your passion"), S("passion"), S("but if it's just for the money") - 0.05,
      side="R", accent=True)
chips("Other ways to make money", [("much easier", S("much easier")), ("much faster", S("much faster")),
                                    ("more flexible", S("more flexible"))],
      S("there are other ways"), S("imagine as a doctor") - 0.05, side="L", label="Easier / faster / more flexible chips")
roll("7632", S("as long as you practice as long"), S("if you want to take a vacation") - 0.02, "Doctor seeing patients",
     clip_in=4.0)
roll("22246", S("if you want to take a vacation"), S("see your nurse") + 0.4, "Vacation", clip_in=3.0)
stack("As long as you work,", "you make money.", S("so as long as you work"), S("you make money", 161), S("but mortgage industry") - 0.05,
      side="R")
stack("Mortgage & loan origination", "is not like that.", S("but mortgage industry"), S("is not like that"),
      S("so you don't have to work") - 0.05, side="L", accent=True)
stack("You don't have to physically", "be anywhere.", S("you don't have to physically"), S("be anywhere"), S("i literally travel") - 0.05,
      side="R")
roll("4204", S("i literally travel"), S("and i close loans in texas"), "Travel: Canada, Bahamas", clip_in=6.0,
     chip_items=[("Canada", S("canada")), ("Bahamas", S("bahamas"))])
roll("17049", S("and i close loans in texas") + 0.02, S("so there is no limitation"), "Closing loans in TX / MI / CA",
     clip_in=2.0, chip_items=[("Texas", S("texas")), ("Michigan", S("michigan")), ("California", S("california"))])
stack("There is", "no limitation.", S("so there is no limitation"), S("no limitation"), S("as long as you know how to promote") - 0.05,
      side="L", accent=True)
chips("As long as you know how to", [("promote yourself", S("promote yourself")), ("prospect", S("prospect", 187))],
      S("as long as you know how to promote"), S("you can be anywhere in the world") - 0.1, side="R")
roll("6724", S("you can be anywhere in the world"), E("you still make money") + 0.1, "Work from anywhere", clip_in=2.0,
     caption="ANYWHERE IN THE WORLD")
stack("Consistent.", "Not one-time money.", S("you can be consistent"), S("it's not just one time"), S("the formula that") - 0.05,
      side="R")
stack("The formula that helps you", "do it consistently.", S("the formula that"), S("this consistently"), S("here's what i mean") - 0.05,
      side="L")
stack("Here's what I mean by", "complicated vs. difficult", S("here's what i mean"), S("complicated and difficult"),
      S("complicated is hard") - 0.08, side="R")
gfx("split", S("complicated is hard") - 0.05, S("i can teach you how to make over") - 0.05,
    "Complicated vs Difficult (full-screen)",
    left=dict(title="COMPLICATED", sub="hard to understand", at=S("complicated is hard"), sub_at=S("hard to understand")),
    right=dict(title="DIFFICULT", sub="hard to do", at=S("difficult is hard"), sub_at=S("hard to do")))
stack("Six figures in", "less than a month.", S("i can teach you how to make over"), S("less than a month"),
      S("but for you to actual") - 0.05, side="R", accent=True)
chips("It takes a lot of", [("effort", S("effort")), ("resistance", S("resistance"))], S("it takes a lot of"),
      S("for you to overcome") - 0.05, side="L")
stack("The voice in your head that pushes you to", "quit.", S("for you to overcome"), S("quit"), S("but you're gonna get up") - 0.05,
      side="R", accent=True)
roll("40265", S("but you're gonna get up"), S("you tell yourself") - 0.02, "Get up again and again", clip_in=0.5,
     caption="AGAIN & AGAIN")
stack("I'm gonna", "make it happen.", S("you tell yourself"), S("make it happen"), S("that's very difficult") + 0.6, side="L")
stack("The vehicle I use:", "the mortgage industry", S("the vehicle that i use"), S("mortgage industry", 235),
      S("you help families") - 0.05, side="R")
roll("6518", S("you help families"), S("you impact lives") - 0.02, "Help families buy homes", clip_in=4.0)
roll("36840", S("you impact lives"), S("and you get paid well") - 0.02, "Impact lives", clip_in=3.0)
stack("…and you get", "paid well.", S("and you get paid well"), S("paid well"), S("you're flexible") - 0.05, side="L", accent=True)
roll("4280", S("you're flexible"), S("this is not just a course") - 0.02, "Flexible, work from anywhere", clip_in=2.0)
stack("Not just a course about mortgages.", "This is the mindset.", S("this is not just a course"), S("this is the mindset"),
      S("i'm gonna teach you how to think") - 0.05, side="R")
chips("I'm gonna teach you how to", [("think", S("think")), ("generate business", S("generate business")),
                                     ("prospect", S("prospect", 257)), ("fill your pipeline", S("fill out your pipeline")),
                                     ("communicate", S("communicate"))],
      S("i'm gonna teach you how to think"), S("how to see the opportunity") - 0.05, side="L")
stack("See the opportunity", "everyone walks past.", S("how to see the opportunity"), S("everyone just walks"),
      S("but you know the opportunity") - 0.05, side="R")
stack("This is a", "lifetime career.", S("this is a lifetime"), S("lifetime career"), S("that's why i built") - 0.05, side="L",
      accent=True)
stack("That's why I built", "Offscript.", S("that's why i built"), S("offscript", 272), S("i teach you everything") + 0.6,
      side="R")
roll("18249", S("how the money moves"), S("what is the secret about") - 0.02, "How the money moves", clip_in=1.0,
     chip_items=[("how the money moves", S("how the money moves")), ("how the banks work", S("how the banks works"))])
stack("Why no one talks about", "the mortgage industry", S("why no one talk about mortgage"), S("mortgage industry", 282),
      S("why no one talk about this flexible") - 0.05, side="L")
chips("A career with", [("flexibility", S("flexible", 288)), ("anywhere in the world", S("anywhere in the world", 293)),
                        ("no limitation", S("no limitation", 295))],
      S("why no one talk about this flexible"), S("i hold your hand") - 0.05, side="R")
gfx("guarantee", S("i hold your hand"), S("i teach you the difference") - 0.05, "Hold your hand / investment back badge",
    fullscreen=False, lead="I hold your hand until you make money", line_at=S("until you make money"),
    badge="OR YOUR INVESTMENT BACK", badge_at=S("otherwise i'm gonna give"), side="L")
chips("The difference between", [("shops", S("shops")), ("retail", S("retails")), ("brokers", S("brokers")),
                                 ("banks", S("different banks")), ("lenders", S("different lenders"))],
      S("i teach you the difference"), S("what is behind the scene") - 0.05, side="R")
stack("What's behind", "the scenes.", S("what is behind the scene"), S("behind the scene"), S("this course is not") - 0.05,
      side="L")
gfx("checklist", S("this course is not"), S("this is for people who") - 0.05, "Not for you if… (full-screen)",
    header="THIS COURSE IS NOT FOR EVERYONE", header_at=S("this course is not"),
    rows=[dict(text="You want passive income", at=S("if you want passive"), x_at=S("this is not for you", 314.5)),
          dict(text="You want a shortcut", at=S("if you want a shortcut"), x_at=S("this is not for you", 317)),
          dict(text="You don't want to do the job", at=S("if you want to be lazy"), x_at=S("this is definitely not"))])
stack("For people done living", "someone else's script.", S("this is for people who"), S("someone else's script", 325),
      S("and they're ready to do") - 0.05, side="L", accent=True)
stack("…and ready to do", "the difficult work.", S("and they're ready to do"), S("the difficult work"), S("i take too many") - 0.05,
      side="R")
stack("I personally teach and handhold you.", "I don't scale my time.", S("i take too many"), S("i don't scale my time"),
      S("if you're serious about") - 0.05, side="L")
chips("If you're serious about", [("the mindset", S("the mindset", 340)), ("the work", S("the work", 341)),
                                  ("making money", S("make money", 342))],
      S("if you're serious about"), S("click below and apply") - 0.05, side="R")
gfx("apply_button", S("click below and apply") - 0.1, S("i read every application") - 0.05, "Click below & apply button",
    fullscreen=False, click_at=S("apply", 344), side="L")
stack("I read every", "application myself.", S("i read every application"), S("application myself"), S("i'm gonna handpick") - 0.05,
      side="R")
stack("I'm gonna", "handpick", S("i'm gonna handpick"), S("handpick"), S("if you're ready") - 0.05, side="L",
      label="I'm gonna handpick the ones…")
stack("If you're ready,", "see you on the other side.", S("if you're ready", 352), S("see you on the other side"),
      S("welcome to offscript") - 0.1, side="R", accent=True)
gfx("endcard", S("welcome to offscript") - 0.1, DUR, "Welcome to Offscript end card", welcome_at=S("welcome to offscript"))

# ------------------------------------------------------------------ SHOTS (zoom motion on the talking head)
face = json.load(open(face_path))
fs = np.array(face["samples"])
med_cx, med_cy, med_fw = np.median(fs[:, 1]), np.median(fs[:, 2]), np.median(fs[:, 3])
ok = (np.abs(fs[:, 2] - med_cy) < 90) & (np.abs(fs[:, 1] - med_cx) < 160)  # drop false detections (hands, etc.)
fs = fs[ok]


def face_at(a, b):
    m = (fs[:, 0] >= a - 0.5) & (fs[:, 0] <= b + 0.5)
    if m.sum() < 2:
        return float(med_cx), float(med_cy)
    return float(np.median(fs[m, 1])), float(np.median(fs[m, 2]))


# cut points: sentence ends + every cue start (so motion changes land with the graphics) + B-roll ends
cuts = {0.0, DUR}
for i, w in enumerate(WORDS[:-1]):
    if w["w"].rstrip().endswith((".", "?", "!")):
        cuts.add(round((w["e"] + WORDS[i + 1]["s"]) / 2, 3))
for t in texts:
    cuts.add(round(t["start"], 3))
for g in graphics:
    cuts.add(round(g["start"], 3)); cuts.add(round(g["end"], 3))
for b in broll:
    cuts.add(round(b["start"], 3)); cuts.add(round(b["end"], 3))
cuts = sorted(cuts)
# merge tiny shots (<1.3 s) into their neighbour; cue cuts win over sentence cuts so moves land on the graphics
prio = {round(x["start"], 3) for x in texts + graphics + broll} | {round(x["end"], 3) for x in graphics + broll}
merged = [cuts[0]]
for c in cuts[1:]:
    if c - merged[-1] < 1.3 and c != DUR:
        if c in prio and merged[-1] not in prio and len(merged) > 1 and c - merged[-2] >= 1.0:
            merged[-1] = c
        continue
    merged.append(c)
if merged[-1] != DUR:
    merged[-1] = DUR
final = [merged[0]]
for c in merged[1:]:
    a, gap = final[-1], c - final[-1]
    if gap > 6.5:
        n = int(np.ceil(gap / 5.0))
        for k in range(1, n):
            final.append(round(a + gap * k / n, 3))
    final.append(c)
final = sorted(set(round(x, 3) for x in final))


def covered(a, b):
    """True when [a,b] is fully hidden behind B-roll or a full-screen graphic."""
    for x in broll + [g for g in graphics if g["fullscreen"]]:
        if x["start"] <= a + 0.05 and x["end"] >= b - 0.05:
            return True
    return False


def text_side(a, b):
    """Side of the cue that overlaps this shot the most (None when no side text)."""
    best, side = 0.0, None
    for t in texts + [g | {"side": g["params"].get("side")} for g in graphics if not g["fullscreen"]]:
        ov = min(b, t["end"]) - max(a, t["start"])
        if ov > best and t.get("side"):
            best, side = ov, t["side"]
    return side if best > 0.25 else None


LEVELS = {"wide": (1.00, 1.07), "med": (1.20, 1.27), "close": (1.34, 1.44)}
rng = random.Random(7)
shots, prev = [], "close"
emph = {round(t["hero_at"], 3) for t in texts if t["type"] == "stack" and t.get("accent")}
for a, b in zip(final[:-1], final[1:]):
    if covered(a, b):
        shots.append(dict(start=a, end=b, frame="hidden", z0=1.0, z1=1.0, cx=med_cx, cy=med_cy, ease_in=False, label=None))
        continue
    side = text_side(a, b)
    # pick framing: never the same twice in a row; text on screen prefers medium (room to shift the speaker)
    if a < 0.5:
        frame = "med"
    elif side:
        frame = rng.choice(["med", "med", "close"]) if prev != "med" else "close"   # never wide under text
    else:
        frame = rng.choice([f for f in ("wide", "med", "close") if f != prev])
    if any(a - 0.05 <= e <= b for e in emph):
        frame = "close" if prev != "close" else "med"
    lo, hi = LEVELS[frame]
    zin = rng.random() < 0.62               # mostly slow push-ins, some pull-outs
    z0, z1 = (lo, hi) if zin else (hi, lo)
    if frame == "wide":
        z0, z1 = (1.0, 1.07) if zin else (1.07, 1.01)
    fx, fy = face_at(a, b)
    shift = 0.0
    if side == "L":
        shift = -1.0                          # speaker moves right of centre (crop moves left)
    elif side == "R":
        shift = 1.0
    shots.append(dict(start=a, end=b, frame=frame, z0=round(z0, 3), z1=round(z1, 3), cx=round(fx, 1), cy=round(fy, 1),
                      shift=shift, ease_in=rng.random() < 0.33 and frame != "wide", label=None))
    prev = frame

# label a few shots for the edit log
for s in shots:
    if s["frame"] == "hidden":
        continue
    kind = "push-in" if s["z1"] > s["z0"] else "pull-out"
    s["label"] = f"{s['frame']} {kind} {s['z0']:.2f}→{s['z1']:.2f}" + (" (eased)" if s["ease_in"] else " (cut)")

# small scale "bumps" on hero words (adds a pulse without changing the shot)
bumps = sorted({round(t["hero_at"], 3) for t in texts if t["type"] in ("stack", "marker") and "hero_at" in t})

edl = dict(meta=dict(duration=DUR, fps=30, width=1920, height=1080, hookEnd=HOOK_END, face=dict(cx=med_cx, cy=med_cy, fw=med_fw),
                     step="v1-motion"),
           shots=shots, bumps=bumps, texts=sorted(texts, key=lambda x: x["start"]),
           graphics=sorted(graphics, key=lambda x: x["start"]), broll=sorted(broll, key=lambda x: x["start"]), sfx=[], music=[])
json.dump(edl, open(out_path, "w"), indent=1)
vis = [s for s in shots if s["frame"] != "hidden"]
print(f"shots {len(shots)} (visible {len(vis)}, avg {np.mean([s['end']-s['start'] for s in vis]):.2f}s) | "
      f"texts {len(texts)} | graphics {len(graphics)} | broll {len(broll)} | first broll {min(b['start'] for b in broll):.2f}s")
