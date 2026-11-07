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


# ------------------------------------------------------------------ v1.1 helpers (reference-matched motions)
FX, overrides = [], []
ACC, INKC, WHT = (214, 58, 47), (17, 20, 24), (255, 255, 255)


def T(kind, start, end, label, **kw):
    texts.append(dict(type=kind, start=round(start, 3), end=round(end, 3), label=label, **kw))


def G(kind, start, end, label, fullscreen=True, **params):
    graphics.append(dict(type=kind, start=round(start, 3), end=round(end, 3), label=label, fullscreen=fullscreen, params=params))


def leak(at):
    FX.append(dict(type="lightleak", at=round(at, 3), label="[R1·3] Light-leak flash"))


def confetti(at, **kw):
    FX.append(dict(type="confetti", at=round(at, 3), label="[R1·6] Confetti burst", **kw))


def hold(start, end, z0, z1, face_x=None, frame="med"):
    overrides.append(dict(start=round(start, 3), end=round(end, 3), z0=z0, z1=z1, face_x=face_x, frame=frame))


def spoken(start, end, n):
    """Spoken word start times in [start, end), thinned to n entries (None if too few words)."""
    ts = [w["s"] for w in WORDS if start - 0.05 <= w["s"] < end - 0.02]
    if len(ts) < n or n == 0:
        return None
    return [round(ts[int(i * len(ts) / n)], 3) for i in range(n)]


def stack(lead, hero, start, hero_at, end, side="L", accent=False, label=None, hero_font="serif"):
    texts.append(dict(type="stack", lead=lead, hero=hero, start=start, hero_at=hero_at, end=end, side=side, accent=accent,
                      lead_times=spoken(start, hero_at, len(lead.split())),
                      hero_times=spoken(hero_at, end, len(hero.split())),
                      label=label or f"[R1·1] {lead} {hero}".strip()))


def cap(text, start, end, key, key_at, label=None):
    words = text.split()
    times = spoken(start, end, len(words)) or None
    T("caption", start, end, label or f"[R5·2] {text}", text=text, key=key, key_at=key_at, times=times)


# ------------------------------------------------------------------ HOOK (no B-roll)
stack("What are you trying to", "prove?", S("what are you trying"), S("prove"), S("who are you trying") - 0.08, side="L")
stack("Who are you trying to", "satisfy?", S("who are you trying"), S("satisfy"), S("the society") - 0.05, side="R")
wordlist([("The society", S("the society")), ("your parents", S("your parents")), ("your cousin", S("your cousin")),
          ("your aunt", S("your aunt"))], "or yourself?", S("yourself"), S("the society"), S("who do you want") - 0.08,
         side="L", label="[R1·1] The society / your parents / your cousin / your aunt / or yourself?")
T("chest", S("who do you want"), S("because this is the way") - 0.1, "[R1·7] Who do you want to / live for? / yourself or other people?",
  small="Who do you want to", big="live for?", big_at=S("live for"), tail="yourself or other people?", tail_at=S("for yourself or"))
cap("Because this is the way.", S("because this is the way"), S("we're not here to follow") - 0.1, [3, 4], S("the way"))
stack("We're not here to follow", "other people's script", S("we're not here to follow"), S("other people's script"),
      S("we're not here to leave") - 0.1, side="L")
T("wavy", S("we're not here to leave"), S("we're here to write") - 0.1, "[R3·4] SOMEONE ELSE'S SCRIPT (wavy letters)",
  lead="We're not here to live", text="SOMEONE ELSE'S SCRIPT", at=S("someone else's script"), dur=0.7, tail="for us.")
T("torso", S("we're here to write"), S("we're here to be") + 0.05, "[R1·4] We're here to write our own / destiny.",
  lead="We're here to write our own", hero="destiny.", hero_at=S("destiny"))
leak(S("we're here to be") - 0.05)
T("behind_words", S("we're here to be") + 0.05, S("my name is") - 0.05, "[R5·1] OFF · SCRIPT behind the speaker",
  left="OFF", right="SCRIPT", left_at=S("be off"), right_at=S("script so welcome"), left_rgb=ACC, right_rgb=INKC, size=300,
  gap=150, y=430, front="WELCOME TO OFF-SCRIPT", front_at=S("welcome to off"), front_rgb=WHT, front_size=84)
hold(S("we're here to be") + 0.05, S("my name is") - 0.05, 1.10, 1.16, face_x=960)
T("karaoke", S("this year i personally"), S("i'm not telling you this") - 0.05, "[R2·5] This year I personally closed over / in personal production",
  line1="This year I personally closed over", line2_at=S("in personal production"), line2="in personal production", hl=[1])
T("counter_behind", S("this year i personally"), S("i'm not telling you this") - 0.05, "[R2·1] $60,000,000 counter behind the speaker",
  value=60_000_000, prefix="$", at=S("60 million"), roll=1.5, tag="closed this year", y=440)
hold(S("this year i personally"), S("i'm not telling you this") - 0.05, 1.12, 1.18, face_x=960)
cap("I'm not telling you this to impress you.", S("i'm not telling you this"), S("i'm telling you to let") - 0.05, [6], S("impress"))
stack("I know", "both sides.", S("know that i know both") + 0.3, S("both sides"), S("i was homeless") - 0.02, side="R")

# ------------------------------------------------------------------ BODY (B-roll allowed from here)
roll("5978", S("i was homeless"), S("i made millions") - 0.02, "Homeless before", clip_in=3.0, caption="BEFORE")
roll("18304", S("i made millions"), E("pick to make millions") + 0.15, "Made millions", clip_in=1.0, caption="AFTER")
G("nodes", S("the difference between"), S("it's not complicated") - 0.05, "[R4·5] Homeless ---- largest investor deal (nodes + dashed line)",
  title="The difference between", title_at=S("the difference between"),
  left=dict(text="Homeless", icon="night_shelter", at=S("homeless", 49)),
  right=dict(text="Largest investor deal", icon="handshake", at=S("largest")), caption="in entire South Florida",
  caption_at=S("south florida"))
T("chest", S("it's not complicated"), S("i got to the point that i realized") - 0.1, "[R1·7] It's not complicated at all, / very difficult.",
  small="It's not complicated at all, but", big="very difficult.", big_at=S("but it's very very"))
stack("Everything is", "programmed.", S("everything is programmed"), S("programmed"), S("everything is basically") - 0.05, side="R")
stack("Everything is basically", "preset.", S("everything is basically"), S("preset"), S("we've been told") - 0.1, side="R")
leak(S("we've been told") - 0.05)
G("tiles", S("we've been told"), S("i just didn't like that") + 0.8, "[R4·1] The script: school → degree → graduate → job → retire (glossy tiles)",
  title="We've been told what to do", title_at=S("we've been told"),
  items=[dict(text="School", icon="school", at=S("go to the school")),
         dict(text="Degree", icon="workspace_premium", at=S("get your degrees")),
         dict(text="Graduate", icon="history_edu", at=S("get graduated")),
         dict(text="Job", icon="work", at=S("go get a job")),
         dict(text="Retire at 60–65", icon="elderly", at=S("retire at"))],
  strike_at=S("i just didn't like that"))
stack("Someone else wrote", "a script for me.", S("someone else is wrote"), S("a script for me"), S("i got to the point that i was") - 0.1, side="L")
stack("What if I don't want", "that type of life?", S("what if i don't"), S("that type of life"), S("no one asked me what type") - 0.05, side="R")
cap("No one asked me what type of life I want.", S("no one asked me what type"), S("no one asked me what is") - 0.05, [0, 1],
    S("no one asked me what type"))
roll("8861", S("what is the cost of going"), S("five years") - 0.05, "Cost of college", clip_in=1.0)
G("bignum", S("five years") - 0.05, S("go to college at") - 0.05, "[R3·1] Giant “10” fly-in → 10 YEARS card",
  fly="10", cut_at=S("10 years") + 0.3, text="10 YEARS", sub="by school I mean college", sub_at=S("by school i mean"))
roll("15923", S("go to college at"), S("with a lot of student") - 0.02, "10–15 years of college", clip_in=1.0,
     chip_items=[("10 years", S("10 years", 96)), ("15 years", S("15 years"))])
G("bars", S("with a lot of student"), S("and you're gonna go to the market") - 0.05, "[R3·5] Debt bars: 10 years $100K · 15 years $200K",
  bars=[dict(label="10 YEARS", value="$100K", at=S("100", 100), h=330),
        dict(label="15 YEARS", value="$200K", at=S("200", 101), h=620)],
  caption="in student loans and debt", caption_at=S("student loans", 102))
roll("6052", S("and you're gonna go to the market"), S("for 60", 108) - 0.3, "Competing for jobs", clip_in=2.0)
marker("Now what?", S("and now what"), S("you're gonna compete") - 0.05, side="R", y=0.24)
G("cards", S("for 60", 108) - 0.3, S("why", 115) - 0.1, "[R3·2] Job cards $60K · $100K · $200K + MIGHT NOT slam",
  cards=[dict(title="Analyst", company="Corporate job", pay="$60,000/yr", at=S("60", 108)),
         dict(title="Associate", company="Corporate job", pay="$100,000/yr", at=S("100", 109.5)),
         dict(title="Manager", company="Corporate job", pay="$200,000/yr", at=S("200", 110))],
  slam="MIGHT NOT", slam_at=S("you might not"))
cap("Why?", S("why", 115), S("i can teach you how to make money") - 0.05, [0], S("why", 115))
T("countup", S("i can teach you how to make money"), S("if you want to go to the college") - 0.1, "[R5·5] Count-up: 6 MONTHS",
  lead="I can teach you how to make money in", value=6, unit=" MONTHS", at=S("six months"), side="R")
T("wavy", S("if you want to go to the college"), S("this is not for me") - 0.05, "[R3·4] College for money? / DO NOT DO THAT.",
  lead="College for the sake of money?", text="DO NOT DO THAT.", at=S("do not do that"), dur=0.55)
broll.append(dict(clip="16108", start=S("don't become a lawyer"), end=S("don't become a doctor") - 0.02, label="[R1·5] Split-screen: lawyer",
                  clip_in=1.0, mode="split", lead="don't become a", word="lawyer,", word_at=S("lawyer", 127.5), chips=[], caption=None))
broll.append(dict(clip="29933", start=S("don't become a doctor"), end=S("if you want to become a lawyer") - 0.02, label="[R1·5] Split-screen: doctor",
                  clip_in=2.0, mode="split", lead="don't become a", word="doctor.", word_at=S("doctor", 128.7), chips=[], caption=None))
hold(S("don't become a lawyer"), S("if you want to become a lawyer") - 0.02, 1.38, 1.42, face_x=470, frame="close")
stack("We need good doctors,", "but not for money.", S("we need good lawyers"), S("but not for money"), S("if it's your passion") - 0.05, side="L")
T("torso", S("if it's your passion"), S("but if it's just for the money") - 0.05, "[R1·4] If it's your / passion, / do it.",
  lead="If it's your", hero="passion,", hero_at=S("passion"), tail="do it.", tail_at=S("do it", 136.5))
T("numchips", S("there are other ways"), S("imagine as a doctor") - 0.05, "[R5·4] 01 Easier · 02 Faster · 03 Flexible",
  lead="Other ways to make money", side="L",
  items=[dict(text="Easier", at=S("much easier")), dict(text="Faster", at=S("much faster")), dict(text="Flexible", at=S("more flexible"))])
T("countup", S("imagine as a doctor"), S("as long as you practice as long") - 0.05, "[R5·5] Count-up: 10 YEARS",
  lead="Even if you practice for", value=10, unit=" YEARS", at=S("10 years", 147), side="R")
broll.append(dict(clip="7632", start=S("as long as you practice as long"), end=S("if you want to take a vacation") - 0.02,
                  label="[R1·5] Split-screen: doctor and patients", clip_in=4.0, mode="split", lead="as long as you see your",
                  word="patients", word_at=S("patients"), chips=[], caption=None))
hold(S("as long as you practice as long"), S("if you want to take a vacation") - 0.02, 1.38, 1.42, face_x=470, frame="close")
roll("22246", S("if you want to take a vacation"), S("see your nurse") + 0.4, "Vacation", clip_in=3.0)
cap("They want to work with you.", S("they want to work"), S("so as long as you work") - 0.05, [4, 5], S("with you", 160))
stack("As long as you work,", "you make money.", S("so as long as you work"), S("you make money", 161), S("but mortgage industry") - 0.05, side="R")
T("chest", S("but mortgage industry"), S("so you don't have to work") - 0.05, "[R1·7] Mortgage & loan origination / is not like that.",
  small="Mortgage & loan origination", big="is not like that.", big_at=S("is not like that"))
stack("You don't have to physically", "be anywhere.", S("you don't have to physically"), S("be anywhere"), S("i literally travel") - 0.05, side="R")
roll("4204", S("i literally travel"), S("and i close loans in texas"), "Travel: Canada, Bahamas", clip_in=6.0,
     chip_items=[("Canada", S("canada")), ("Bahamas", S("bahamas"))])
roll("17049", S("and i close loans in texas") + 0.02, S("so there is no limitation"), "Closing loans in TX / MI / CA",
     clip_in=2.0, chip_items=[("Texas", S("texas")), ("Michigan", S("michigan")), ("California", S("california"))])
T("torso", S("so there is no limitation"), S("as long as you know how to promote") - 0.05, "[R1·4] there is / no limitation.",
  lead="there is", hero="no limitation.", hero_at=S("no limitation"))
T("pills", S("as long as you know how to promote"), S("you can be anywhere in the world") - 0.05, "[R2·3] Pills: promote yourself ✓ prospect ✓",
  ok=True, items=[dict(text="Promote yourself", at=S("promote yourself")), dict(text="Prospect", at=S("prospect", 187)),
                  dict(text="I'll teach you how", at=S("teach you how to do"))])
roll("6724", S("you can be anywhere in the world"), E("you still make money") + 0.1, "Work from anywhere", clip_in=2.0,
     caption="ANYWHERE IN THE WORLD")
stack("Consistent.", "Not one-time money.", S("you can be consistent"), S("it's not just one time"), S("the formula that") - 0.05, side="R")
cap("The formula helps you do this consistently.", S("the formula that"), S("here's what i mean") - 0.05, [1], S("formula"))
stack("Here's what I mean by", "complicated vs. difficult", S("here's what i mean"), S("complicated and difficult"),
      S("complicated is hard") - 0.08, side="R")
gfx("split", S("complicated is hard") - 0.05, S("i can teach you how to make over") - 0.05,
    "Complicated vs Difficult (full-screen)",
    left=dict(title="COMPLICATED", sub="hard to understand", at=S("complicated is hard"), sub_at=S("hard to understand")),
    right=dict(title="DIFFICULT", sub="hard to do", at=S("difficult is hard"), sub_at=S("hard to do")))
G("money_chart", S("i can teach you how to make over"), S("but for you to actual") - 0.05, "[R2·2] Six-figure counter + chart line",
  prefix="$", value=100_000, suffix="+", at=S("six figures"), note="in less than a month", note_at=S("less than a month"))
T("pills", S("it takes a lot of"), S("for you to overcome") - 0.05, "[R2·3] Pills: effort · resistance", ok=True,
  items=[dict(text="A lot of effort", at=S("effort")), dict(text="A lot of resistance", at=S("resistance"))])
stack("The sound in your brain that pushes you to", "quit.", S("for you to overcome"), S("quit"), S("but you're gonna get up") - 0.05,
      side="R", accent=True)
roll("40265", S("but you're gonna get up"), S("you tell yourself") - 0.02, "Get up again and again", clip_in=0.5,
     caption="AGAIN & AGAIN")
T("torso", S("you tell yourself"), S("that's very difficult") + 0.6, "[R1·4] I'm gonna / make it happen.",
  lead="I'm gonna", hero="make it happen.", hero_at=S("make it happen"))
stack("The vehicle I use:", "the mortgage industry", S("the vehicle that i use"), S("mortgage industry", 235),
      S("because the numbers") - 0.05, side="R")
cap("The numbers make sense.", S("because the numbers"), S("you help families") - 0.15, [1], S("numbers"))
leak(S("you help families") - 0.15)
G("tree", S("you help families") - 0.1, S("what is better than") - 0.05, "[R4·3] Tree: mortgage → families · lives · paid well",
  root=dict(text="Mortgage industry", icon="real_estate_agent", at=S("you help families") - 0.05),
  children=[dict(text="Help families buy homes", icon="home", at=S("buy homes")),
            dict(text="Impact lives", icon="favorite", at=S("impact lives")),
            dict(text="Get paid well", icon="payments", at=S("paid well"))])
T("torso", S("what is better than"), S("you're flexible") - 0.02, "[R1·6] What is / better than that? + confetti",
  lead="What is", hero="better than that?", hero_at=S("better than"))
confetti(S("better than") + 0.1, y=880)
roll("4280", S("you're flexible"), S("this is not just a course") - 0.02, "Flexible, work from anywhere", clip_in=2.0)
stack("Not just a course about mortgages.", "This is the mindset.", S("this is not just a course"), S("this is the mindset"),
      S("i'm gonna teach you how to think") - 0.05, side="R")
G("title_icons", S("i'm gonna teach you how to think"), S("how to see the opportunity") - 0.05,
  "[R4·4] Title + icon row: think · business · prospect · pipeline · communicate",
  title="I'm gonna teach you how to", title_at=S("i'm gonna teach you how to think"),
  items=[dict(text="Think", icon="psychology", at=S("think")),
         dict(text="Generate business", icon="trending_up", at=S("generate business")),
         dict(text="Prospect", icon="person_search", at=S("prospect", 257)),
         dict(text="Fill your pipeline", icon="filter_alt", at=S("fill out your pipeline")),
         dict(text="Communicate", icon="forum", at=S("communicate"))])
G("spotlight", S("how to see the opportunity"), S("you're gonna jump on it") - 0.05, "[R4·2] Spotlight: the opportunity everyone walks past",
  icon="diamond", tile="The opportunity", land_at=S("everyone just walks"), title="See the opportunity everyone walks past",
  title_at=S("how to see the opportunity"))
stack("Jump on it and", "maximize it.", S("you're gonna jump on it"), S("maximize"), S("this is a lifetime") - 0.05, side="L", accent=True)
T("behind_words", S("this is a lifetime"), S("that's why i built") - 0.05, "[R5·1] LIFETIME CAREER behind the speaker",
  left="LIFETIME", right="CAREER", left_at=S("lifetime"), right_at=S("career", 270), left_rgb=INKC, right_rgb=ACC, size=230,
  gap=150, y=430)
hold(S("this is a lifetime"), S("that's why i built") - 0.05, 1.10, 1.15, face_x=960)
cap("That's why I built Offscript.", S("that's why i built"), S("i teach you everything"), [4], S("offscript", 272))
G("doc_cam", S("i teach you everything"), S("why no one talk about mortgage") - 0.05,
  "[R2·6 + R2·7] Shrink to circle cam + document highlighter",
  title="Inside Offscript", kicker="I teach you everything:",
  lines=[dict(text="How the money moves", at=S("how the money moves")),
         dict(text="How the banks work", at=S("how the banks works")),
         dict(text="The secrets of the mortgage industry", at=S("what is the secret about"))])
T("prompt", S("why no one talk about mortgage"), S("why no one talk about this flexible") - 0.05, "[R1·2] AI prompt bar: why does no one talk about it?",
  hero="Why?", bar_at=S("why no one talk about mortgage") + 0.3, text="why does no one talk about the mortgage industry?",
  type_dur=1.8)
G("blur_list", S("why no one talk about this flexible"), S("i hold your hand") - 0.05, "[R5·6] A career with: flexibility · anywhere · no limitation",
  title="A career with", items=[dict(text="Flexibility", icon="bolt", at=S("flexible", 288)),
                                dict(text="Anywhere in the world", icon="public", at=S("anywhere in the world", 293)),
                                dict(text="No limitation", icon="all_inclusive", at=S("no limitation", 295))])
T("karaoke", S("i hold your hand"), S("i teach you the difference") - 0.05, "[R2·5] I hold your hand until you make money / or your investment back",
  line1="I hold your hand until you make money,", line2_at=S("otherwise i'm gonna give"), line2="or your investment back.", hl=[2, 3])
G("icon_cards", S("i teach you the difference"), S("what is behind the scene") - 0.05, "[R2·4] Icon cards: shops · retail · brokers · banks · lenders",
  title="The difference between",
  items=[dict(text="Shops", icon="storefront", at=S("shops")), dict(text="Retail", icon="shopping_bag", at=S("retails")),
         dict(text="Brokers", icon="handshake", at=S("brokers")), dict(text="Banks", icon="account_balance", at=S("different banks")),
         dict(text="Lenders", icon="payments", at=S("different lenders"))])
stack("What's behind", "the scenes.", S("what is behind the scene"), S("behind the scene"), S("this course is not") - 0.05, side="L")
cap("This course is not for everyone.", S("this course is not"), S("if you want passive") - 0.05, [3], S("not for everyone"))
T("pills", S("if you want passive"), S("this is for people who") - 0.05, "[R2·3] Pills: passive income ✕ · shortcut ✕ · lazy ✕ · not doing the job ✕",
  ok=False, items=[dict(text="Passive income", at=S("passive income")), dict(text="A shortcut", at=S("a shortcut")),
                   dict(text="Being lazy", at=S("lazy")), dict(text="Not doing the job", at=S("do the job"))])
T("karaoke", S("this is for people who"), S("and they're ready to do") - 0.05, "[R2·5] This is for people done living / someone else's script",
  line1="This is for people who are done living", line2_at=S("someone else's script", 325), line2="someone else's script", hl=[2])
stack("…and ready to do", "the difficult work.", S("and they're ready to do"), S("the difficult work"), S("i take too many") - 0.05, side="R")
stack("I personally teach and handhold you.", "I don't scale my time.", S("i take too many"), S("i don't scale my time"),
      S("if you're serious about") - 0.05, side="L")
G("ring", S("if you're serious about"), S("click below and apply") - 0.05, "[R5·3] Ring: serious about the mindset · the work · making money",
  title="IF YOU'RE SERIOUS ABOUT", items=[dict(text="The mindset", at=S("the mindset", 340)), dict(text="The work", at=S("the work", 341)),
                                          dict(text="Making money", at=S("make money", 342))])
G("ui_card", S("click below and apply") - 0.1, S("i'm gonna handpick") - 0.05, "[R3·3] Speaker inside an apply card + click",
  brand="OFFSCRIPT", headline="Click below and apply", sub="I read every application myself.", button="Apply now",
  click_at=S("apply", 344))
cap("I'm gonna handpick the ones I can work with.", S("i'm gonna handpick"), S("if you're ready", 352) - 0.05, [2], S("handpick"))
T("torso", S("if you're ready", 352), S("welcome to offscript") - 0.15, "[R1·4] If you're ready, I'll see you on / the other side.",
  lead="If you're ready, I'll see you on", hero="the other side.", hero_at=S("the other side"))
leak(S("welcome to offscript") - 0.15)
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
for o in overrides:
    cuts.add(o["start"]); cuts.add(o["end"])
cuts = sorted(cuts)
# merge tiny shots (<1.3 s) into their neighbour; cue cuts win over sentence cuts so moves land on the graphics
prio = ({round(x["start"], 3) for x in texts + graphics + broll} | {round(x["end"], 3) for x in graphics + broll}
        | {o["start"] for o in overrides} | {o["end"] for o in overrides})
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
    for x in [b for b in broll if b.get("mode") != "split"] + [g for g in graphics if g["fullscreen"]]:
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
    ov = next((o for o in overrides if o["start"] <= a + 0.05 and o["end"] >= b - 0.05), None)
    if ov:
        fx_, fy_ = face_at(a, b)
        shots.append(dict(start=a, end=b, frame=ov["frame"], z0=ov["z0"], z1=ov["z1"], cx=round(fx_, 1), cy=round(fy_, 1),
                          shift=0.0, face_x=ov["face_x"], ease_in=False, label=None))
        prev = ov["frame"]
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
                     step="v1.1-motion"),
           shots=shots, bumps=bumps, texts=sorted(texts, key=lambda x: x["start"]),
           graphics=sorted(graphics, key=lambda x: x["start"]), broll=sorted(broll, key=lambda x: x["start"]),
           fx=sorted(FX, key=lambda x: x["at"]), sfx=[], music=[])
json.dump(edl, open(out_path, "w"), indent=1)
vis = [s for s in shots if s["frame"] != "hidden"]
print(f"shots {len(shots)} (visible {len(vis)}, avg {np.mean([s['end']-s['start'] for s in vis]):.2f}s) | "
      f"texts {len(texts)} | graphics {len(graphics)} | broll {len(broll)} | first broll {min(b['start'] for b in broll):.2f}s")
