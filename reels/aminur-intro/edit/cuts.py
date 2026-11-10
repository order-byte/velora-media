# source-time speech segments (raw footage) -> edit timeline
# (name, src_start, src_end)
PAD_IN, PAD_OUT = 0.05, 0.09
SEGS = [
 ("AB", 0.10, 3.18),   # Hi, my name is Aminur. I go to university.
 ("C", 3.67, 7.23),    # And alongside that, I work as a freelance video editor.
 ("D", 7.67, 11.73),   # I have been working in After Effects for almost 4 years now,
 ("E", 12.28, 15.15),  # mostly making motion graphics and promo ads.
 ("FG", 16.44, 22.13), # And I really enjoy it. Now I am building my own page and posting more of my work here.
 ("H", 22.50, 25.96),  # My goal is simple. Keep getting better at editing,
 ("I", 26.83, 29.99),  # work with good clients and enjoy what I do.
 ("J", 32.53, 35.19),  # I have no idea what comes next.
 ("K", 35.69, 39.80),  # But if you want to see my work and follow my journey, stay with me.
 ("L", 40.36, 43.30),  # And if you need a video editor, just DM me.
]
SPEED = 1.08
def plan():
    out=[]; t=0.0
    for n,a,b in SEGS:
        a2=max(0,a-PAD_IN); b2=b+PAD_OUT
        out.append(dict(name=n, src0=a2, src1=b2, ed0=t, ed1=t+(b2-a2)))
        t+=b2-a2
    return out, t
def src2final(ts):
    """map a raw-footage time to final (sped-up) time"""
    segs,_=plan()
    for s in segs:
        if s["src0"]<=ts<=s["src1"]: return (s["ed0"]+ts-s["src0"])/SPEED
    # nearest
    best=min(segs,key=lambda s:min(abs(ts-s["src0"]),abs(ts-s["src1"])))
    ts=min(max(ts,best["src0"]),best["src1"]); return (best["ed0"]+ts-best["src0"])/SPEED
if __name__=="__main__":
    segs,T=plan()
    for s in segs: print(s["name"], round(s["src0"],2), round(s["src1"],2), "->", round(s["ed0"]/SPEED,2), round(s["ed1"]/SPEED,2))
    print("total edit", round(T,2), "final", round(T/SPEED,2))
